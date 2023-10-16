import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from typing import TypedDict, NamedTuple
from dataclasses import dataclass
from api.v1.chat.services import ChatQueryService
from enum import Enum
from .models import Message

class ReceivedData(TypedDict):
    command: str
    data: dict


class ActionType(Enum):
    ADD = 1
    DISCARD = -1

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def new_message_handler(self, data: dict):
        print('new message handler', data)
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
        print('write_message_handler', data)

    async def new_message_event(self, event: dict):
        print('new_message_event', event)
        await self.send_json(event)


    commands = {
        'new_message': new_message_handler,
        'write_message': write_message_handler,
    }

    async def update_chat_groups(self, action: ActionType):

        service = ChatQueryService()
        chats = service.get_chats(self.user['id'])

        if action == ActionType.ADD:
            async for chat in chats:
                await self.channel_layer.group_add(chat.id, self.channel_name)
        elif action == ActionType.DISCARD:
            async for chat in chats:
                await self.channel_layer.group_discard(chat.id, self.channel_name)

    async def connect(self):
        self.user: dict = self.scope['user']
        await self.update_chat_groups(ActionType.ADD)
        await self.accept()

    async def disconnect(self, close_code):
        await self.update_chat_groups(ActionType.DISCARD)

    # Receive message from WebSocket
    async def receive_json(self, data: ReceivedData):
        # self.send_json(data, close=True)

        command = data['command']
        handler = self.commands[command]
        await handler(self, data['data'])
        # Send message to room group
        # await self.channel_layer.group_send(
        #     self.room_group_name, {"type": "chat.message", "message": message}
        # )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))
