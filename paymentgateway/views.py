from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from registration.models import TournamentRegistration, Payment
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import uuid
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest
from django.urls import reverse
from django.utils.http import urlencode
from players.utils import reshuffle_leagues


def send_transaction_email(player_email, partner_email, partner_2_email, player_name, partner_name, partner_2_name, category, paytm_params):
    subject = "Shuttle Up - Tournament Registration Confirmation"

    # Create greeting based on category, no trailing commas
    if category.lower() == "singles":
        greeting = f"{player_name}"
        recipients = [player_email]
    elif category.lower() == "triplets":
        greeting = f"{player_name}, {partner_name}, and {partner_2_name}"
        recipients = [email.strip() for email in [player_email, partner_email, partner_2_email] if email]
    else:  # Doubles or Mixed Doubles
        greeting = f"{player_name} and {partner_name}"
        recipients = [email.strip() for email in [player_email, partner_email] if email]

    # Build the message
    from_email = "StringsAttched@gmail.com"
    to_email = recipients

    html_content = render_to_string('confirmation_email.html', {
        'greeting': greeting,
        'category': category,
        'paytm_params': paytm_params,
    })

    msg = EmailMultiAlternatives(subject, "", from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def get_amount_by_category(category):
    return 49900 if category == 'singles' else 99900 if category == 'triplets' else 79900

def initiate_phonepe_payment(request, registration_id):
    try:
        registration = TournamentRegistration.objects.get(id=registration_id)
    except TournamentRegistration.DoesNotExist:
        return render(request, 'payment_failure.html', {'error': 'Registration not found'})

    amount = get_amount_by_category(registration.category)
    merchant_order_id = f"TXN{registration.id}{uuid.uuid4().hex[:6]}"
    registration.phonepay_order_id = merchant_order_id
    registration.save()

    client = StandardCheckoutClient.get_instance(
        client_id=settings.PHONEPE_CLIENT_ID,
        client_secret=settings.PHONEPE_CLIENT_SECRET,
        client_version=1,
        env=Env.SANDBOX if settings.PHONEPE_ENV == 'SANDBOX' else Env.PRODUCTION
    )
    # Build the callback URL with merchantTransactionId as query param
    callback_path = reverse("paymentgateway:phonepe_callback")
    callback_url = request.build_absolute_uri(callback_path)
    redirect_url = f"{callback_url}?{urlencode({'merchantTransactionId': merchant_order_id})}"

    pay_request = StandardCheckoutPayRequest.build_request(
        merchant_order_id=merchant_order_id,
        amount=amount,
        redirect_url=redirect_url
    )

    try:
        response = client.pay(pay_request)
    except Exception as e:
        return render(request, 'payment_failure.html', {'error': str(e)})

    # 🟢 Check for pending and valid redirect
    if getattr(response, 'state', '').upper() == 'PENDING' and hasattr(response, 'redirect_url') and response.redirect_url:
        return redirect(response.redirect_url)

    # ❌ Otherwise, payment initiation failed
    error_msg = getattr(response, 'state', 'UNKNOWN')
    return render(request, 'payment_failure.html', {'error': error_msg})

@csrf_exempt
def phonepe_callback(request):
    
    merchant_transaction_id = request.POST.get("merchantTransactionId") or request.GET.get("merchantTransactionId")

    if not merchant_transaction_id:
        return render(request, 'payment_failure.html', {'error': 'Missing merchantTransactionId'})

    # PhonePe client
    client = StandardCheckoutClient.get_instance(
        client_id=settings.PHONEPE_CLIENT_ID,
        client_secret=settings.PHONEPE_CLIENT_SECRET,
        client_version=1,
        env=Env.SANDBOX if settings.PHONEPE_ENV == 'SANDBOX' else Env.PRODUCTION
    )

    try:
        status_resp = client.get_order_status(merchant_order_id=merchant_transaction_id)
        print(status_resp)
        if status_resp and status_resp.state in ['SUCCESS', 'COMPLETED']:
            registration = TournamentRegistration.objects.get(phonepay_order_id=merchant_transaction_id)
            amount_paid = get_amount_by_category(registration.category)
            
            # First try top-level amount
            if status_resp.amount:
                amount_paid = status_resp.amount
            # Then try first payment detail's amount
            elif status_resp.payment_details and status_resp.payment_details[0].amount:
                amount_paid = status_resp.payment_details[0].amount
            # Lastly, try first split instrument's amount
            elif (
                status_resp.payment_details and
                status_resp.payment_details[0].split_instruments and
                status_resp.payment_details[0].split_instruments[0].amount
            ):
                amount_paid = status_resp.payment_details[0].split_instruments[0].amount

            # Convert to rupees if needed (amount is in paisa)
            amount_paid_inr = amount_paid / 100

            txn_id = (
                        status_resp.payment_details[0].transaction_id
                        if status_resp.payment_details and status_resp.payment_details[0].transaction_id
                        else None
                    )
            # Create payment entry
            Payment.objects.create(
                registration=registration,
                order_id=merchant_transaction_id,
                txn_id=txn_id,
                txn_amount=amount_paid_inr,
                status="TXN_SUCCESS",
                response_data=status_resp.__dict__,
            )

            registration.payment_status = "Paid"
            registration.save()

            # Get player info from your model or request
            player_name = registration.player_name 
            partner_name = registration.partner_name 
            player_email = registration.player_email
            partner_email = registration.partner_email
            partner_2_email = registration.partner_2_email
            player_name = registration.player_name
            partner_2_name = registration.partner_2_name
            category = registration.get_category_display()

            # Simulate Paytm POST data (normally comes from Paytm)
            payment_params = {
                "ORDERID": merchant_transaction_id,
                "TXNID": txn_id,
                "TXNAMOUNT": amount_paid_inr,
                "STATUS": "SUCCESS"
            }
            send_transaction_email(player_email, partner_email, partner_2_email, player_name, partner_name, partner_2_name, category, payment_params)
            reshuffle_leagues()
            return render(request, 'payment_success.html')

        return render(request, 'payment_failure.html')

    except Exception as e:
        return render(request, 'payment_failure.html', {'error': str(e)})