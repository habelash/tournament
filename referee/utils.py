def is_referee_for_tournament(user, tournament):
    return (
        hasattr(user, "referee_profile")
        and user.referee_profile.tournaments.filter(id=tournament.id).exists()
    )

def is_referee(user):
    return hasattr(user, 'referee_profile')  # only referees have this
