import requests
import json
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from chat.models import Chat, UserChat, Message
from django.db.models import Q

User = get_user_model()

class InitService:
    def __init__(self, token: str, id: int):
        self.token = token
        self.chat_user_id = id
        self.host = settings.BLOG_URL

    def check_token(self) -> dict:
        data = {'token': self.token}

        response = requests.post(f'{self.host}/api/v1/auth/microauth/', data)
        if response.status_code != 200:
            raise ValidationError('Invalid token')

        return response.json()

    def check_id_chat_user(self) -> dict:
        data = {'chat_user_id': self.chat_user_id}

        response = requests.post(f'{self.host}/api/v1/auth/checkid/', data)
        if response.status_code != 200:
            raise ValidationError('User does not exist')

        return response.json()


class ChatService:
    def __init__(self, user_1: dict, user_2: dict):
        self.user_1 = user_1
        self.user_2 = user_2

    def create_chat(self) -> Chat:
        chat = Chat.objects.filter(Q(name__has_key=f'id_{self.user_1["id"]}') & Q(name__has_key=f'id_{self.user_2["id"]}')).first()

        if not chat:
            chat = Chat.objects.create(name={f'id_{self.user_1["id"]}': self.user_2["full_name"], f'id_{self.user_2["id"]}': self.user_1["full_name"]})

            userchats = [
                UserChat(user=self.user_1["id"], chat=chat),
                UserChat(user=self.user_2["id"], chat=chat)
            ]
            UserChat.objects.bulk_create(userchats)

        return chat

class ChatQueryService:
    @staticmethod
    def get_chats(auth_id: int):
        return Chat.objects.filter(user_chats__user=auth_id)

    @staticmethod
    def get_messages_for_chat(chat_id: str):
        return Message.objects.filter(chat=chat_id)

