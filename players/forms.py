from django import forms
from .models import TournmentMatch
from registration.models import TournamentRegistration

class TournmentMatchAdminForm(forms.ModelForm):
    class Meta:
        model = TournmentMatch
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get('instance')
        if instance:
            # Limit the winner choices to team1 and team2
            self.fields['winner'].queryset = TournamentRegistration.objects.filter(
                id__in=[instance.team1_id, instance.team2_id]
            )
