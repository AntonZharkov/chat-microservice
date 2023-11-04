import json
from base64 import b64decode
from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple, TypedDict

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings

from api.v1.chat.services import ChatQueryService

from .models import Message
from main.services import RedisUserStatus


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
        if file := data.get('file'):
            decoded_file = b64decode(file['content'])
        message: Message = await Message.objects.acreate(author=self.user['id'], chat_id=chat_id, body=data['body'])
        data['created'] = str(message.created)

        await self.channel_layer.group_send(
            chat_id,
            {
                'type': 'new_message_event',
                'data': data,
            },
        )

    async def write_message_handler(self, data: dict):
        chat_id = data['chat_id']
        await self.channel_layer.group_send(
            chat_id,
            {
                'type': 'write_message_event',
                'data': data,
            },
        )

    async def new_chat_event(self, event: dict):
        # TODO: когда создается новый чат добавляем юзера к в группу этого чата чтобы ему приходили ивенты
        redis_service = RedisUserStatus()
        status_online = redis_service.get_status(self.user['id'])['online']
        if status_online:
            chat_id = event['data']['chat_id']
            await self.channel_layer.group_add(chat_id, self.channel_name)

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
                        },
                    },
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
                        },
                    },
                )

    async def connect(self):
        self.user: dict = self.scope['user']
        service = RedisUserStatus()
        await sync_to_async(service.set_online)(self.user['id'])

        await self.update_chat_groups(ActionType.ADD)
        await self.accept()

    async def disconnect(self, close_code):
        service = RedisUserStatus()
        await sync_to_async(service.set_offline)(self.user['id'])
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
