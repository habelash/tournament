from django.db import models
from registration.models import TournamentRegistration
from organiser.models import Tournament,TournamentCategory,Category, Court
# Create your models here.

class LeagueAssignment(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="League")
    team = models.OneToOneField(TournamentRegistration, on_delete=models.CASCADE)
    league = models.CharField(max_length=1)  # A, B, C...
    category = models.ForeignKey(TournamentCategory, on_delete=models.CASCADE, related_name="league_assignments")


    def __str__(self):
        return f"{self.team.player_name} - League {self.league} ({self.category})"


class TournmentMatch(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="matches")
    game_number = models.PositiveIntegerField()
    category = models.ForeignKey(TournamentCategory, on_delete=models.CASCADE, related_name="categories")  
    league = models.CharField(max_length=2, blank=True, null=True)  # Optional for knockout

    round = models.CharField(max_length=50, default='League')  # No fixed choices

    team1 = models.ForeignKey(TournamentRegistration, on_delete=models.CASCADE, related_name='team1_matches', null=True, blank=True)
    team2 = models.ForeignKey(TournamentRegistration, on_delete=models.CASCADE, related_name='team2_matches', null=True, blank=True)
    court = models.ForeignKey(
        Court,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches"
    )
    team1_score = models.PositiveIntegerField(null=True, blank=True)
    team2_score = models.PositiveIntegerField(null=True, blank=True)

    note = models.CharField(max_length=255, blank=True, null=True)  # <- Add this

    winner = models.ForeignKey(
        TournamentRegistration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_matches'
    )
    is_started = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.round}] {self.category} – {self.team1} vs {self.team2}"

    def get_status(self):
        if self.is_completed and self.winner:
            return f"✅ Winner: {self.winner}"
        elif self.is_started:
            return "🔴 In Progress"
        else:
            return "🕒 Pending"
