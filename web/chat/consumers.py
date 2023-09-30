import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from typing import TypedDict, NamedTuple
from dataclasses import dataclass
from .models import Chat
from channels.db import database_sync_to_async

class ReceivedData(TypedDict):
    command: str
    data: dict

class ChatConsumer(AsyncJsonWebsocketConsumer):
    def new_message_handler(self, data: dict):
        print('new message handler', data)

    def write_message_handler(self, data: dict):
        print('write_message_handler', data)

    @database_sync_to_async
    def get_chats(self, user_id: int):
        return list(Chat.objects.filter(name__has_key=f'id_{user_id}'))

    commands = {
        'new_message': new_message_handler,
        'write_message': write_message_handler,
    }


    async def connect(self):
        user_id = self.scope['user_id']
        chats = await self.get_chats(user_id)

        for chat in chats:
            await self.channel_layer.group_add(chat.id, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive_json(self, data: ReceivedData):
        print('receive json', data)
        # self.send_json(data, close=True)

        command = data['command']
        handler = self.commands[command]
        handler(self, data['data'])
        # Send message to room group
        # await self.channel_layer.group_send(
        #     self.room_group_name, {"type": "chat.message", "message": message}
        # )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))
