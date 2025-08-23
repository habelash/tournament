import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ScoreUpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("score_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("score_updates", self.channel_name)

    async def receive(self, text_data):
        pass  # You typically don’t need this unless frontend sends data.

    async def send_score_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))

