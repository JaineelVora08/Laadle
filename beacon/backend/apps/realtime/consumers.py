from channels.generic.websocket import AsyncJsonWebsocketConsumer


class BeaconLiveConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'user_{self.user_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get('type') == 'heartbeat':
            await self.send_json({'type': 'heartbeat_ack'})

    async def query_update(self, event):
        await self.send_json(event['data'])
