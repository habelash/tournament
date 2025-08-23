from django.urls import re_path
from . import consumers  # Make sure consumers.py is in the same app

websocket_urlpatterns = [
    re_path(r"^ws/score_updates/$", consumers.ScoreUpdateConsumer.as_asgi()),
]
