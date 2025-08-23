from django import forms
from .models import TournamentRegistration, CATEGORY_CHOICES

class TournamentRegistrationForm(forms.ModelForm):
    class Meta:
        model = TournamentRegistration
        fields = ['player_name', 'partner_name', 'phone_number', 'category']

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        partner_name = cleaned_data.get('partner_name')

        doubles_categories = ['mens_doubles', 'womens_doubles', 'mixed_doubles']

        if category in doubles_categories and not partner_name:
            raise forms.ValidationError("Partner name is required for doubles categories.")

        if category not in doubles_categories:
            cleaned_data['partner_name'] = ''

        return cleaned_data
