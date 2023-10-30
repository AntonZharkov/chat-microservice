import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from typing import TypedDict, NamedTuple
from dataclasses import dataclass
from api.v1.chat.services import ChatQueryService
from enum import Enum
from .models import Message
from django.conf import settings

class ReceivedData(TypedDict):
    command: str
    data: dict


class ActionType(Enum):
    ADD = 1
    DISCARD = -1

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def new_message_handler(self, data: dict):
        chat_id = data['chat_id']
        data['user'] = self.user
        message: Message = await Message.objects.acreate(author=self.user['id'], chat_id=chat_id, body=data['body'])
        data['created'] = str(message.created)

        await self.channel_layer.group_send(
            chat_id,
            {
                'type': 'new_message_event',
                'data': data,
            }
        )


    async def write_message_handler(self, data: dict):
        chat_id = data['chat_id']
        await self.channel_layer.group_send(
            chat_id,
            {
                'type': 'write_message_event',
                'data': data,
            }
        )

    async def new_chat_event(self, event: dict):
        await self.send_json(event)

    async def new_message_event(self, event: dict):
        await self.send_json(event)

    async def write_message_event(self, event: dict):
        await self.send_json(event)

    async def user_online_event(self, event: dict):
        await self.send_json(event)


    commands = {
        'new_message': new_message_handler,
        'write_message': write_message_handler,
    }

    async def update_chat_groups(self, action: ActionType):

        service = ChatQueryService()
        chats = service.get_chats(self.user['id'])

        if action == ActionType.ADD:
            event_channel_name = settings.WEBSOCKET_EVENT_CHANNEL_NAME.format(user_id=self.user['id'])
            await self.channel_layer.group_add(event_channel_name, self.channel_name)

            async for chat in chats:
                await self.channel_layer.group_add(chat.id, self.channel_name)
                await self.channel_layer.group_send(
                            chat.id,
                            {
                                'type': 'user_online_event',
                                'data': {
                                    'user_name': self.user['full_name'],
                                    'online': True,
                                    'chat_id': chat.id,
                                }
                            }
                )
        elif action == ActionType.DISCARD:
            async for chat in chats:
                await self.channel_layer.group_discard(chat.id, self.channel_name)
                await self.channel_layer.group_send(
                            chat.id,
                            {
                                'type': 'user_online_event',
                                'data': {
                                    'online': False,
                                    'chat_id': chat.id,
                                }
                            }
                        )

    async def connect(self):
        self.user: dict = self.scope['user']
        await self.update_chat_groups(ActionType.ADD)
        await self.accept()

    async def disconnect(self, close_code):
        await self.update_chat_groups(ActionType.DISCARD)

    # Receive message from WebSocket
    async def receive_json(self, data: ReceivedData):
        command = data['command']
        handler = self.commands[command]
        await handler(self, data['data'])

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))
