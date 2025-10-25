def is_referee_for_tournament(user, tournament):
    return (
        hasattr(user, "refereeprofile")
        and user.refereeprofile.tournaments.filter(id=tournament.id).exists()
    )

def is_referee(user):
    return hasattr(user, 'refereeprofile')  # only referees have this
