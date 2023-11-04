from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Prefetch, Q

from chat.models import Chat, Message, UserChat

from main.services import RedisCacheService, RedisUserStatus
from main.utils import get_jwt_token_from_request


class ChatService:
    def __init__(self, user_1: dict, user_2: dict):
        self.user_1 = user_1
        self.user_2 = user_2

    def create_chat(self) -> tuple[Chat, bool]:
        chat = Chat.objects.filter(
            Q(name__has_key=f'id_{self.user_1["id"]}') & Q(name__has_key=f'id_{self.user_2["id"]}')
        ).first()
        created = False

        if not chat:
            chat = Chat.objects.create(
                name={
                    f'id_{self.user_1["id"]}': self.user_2["full_name"],
                    f'id_{self.user_2["id"]}': self.user_1["full_name"],
                }
            )
            created = True

            userchats = [UserChat(user=self.user_1["id"], chat=chat), UserChat(user=self.user_2["id"], chat=chat)]
            UserChat.objects.bulk_create(userchats)

        return chat, created

    def new_chat_event(self, user_id: int, chat_id: str, user_info: dict):
        event_channel_name = settings.WEBSOCKET_EVENT_CHANNEL_NAME.format(user_id=user_id)
        event_data = {
            'type': 'new_chat_event',
            'data': {
                'chat_id': chat_id,
                'user': user_info,
            },
        }
        async_to_sync(get_channel_layer().group_send)(event_channel_name, event_data)


class ChatQueryService:
    @staticmethod
    def get_chats(user_id: int):
        return Chat.objects.filter(user_chats__user=user_id)

    def get_ids_list_chat_participants(user_id: int) -> list:
        return list(
            UserChat.objects.filter(chat__user_chats__user=user_id).exclude(user=user_id).values_list('user', flat=True)
        )

    @staticmethod
    def get_chats_with_user_id(user_id: int):
        return Chat.objects.filter(user_chats__user=user_id).prefetch_related(
            Prefetch('user_chats', UserChat.objects.exclude(user=user_id))
        )

    @staticmethod
    def get_messages_for_chat(chat_id: str):
        return Message.objects.filter(chat=chat_id)


class ChatListService:
    # TODO: доделать
    def __init__(self) -> None:
        self._user = None
        self.redis_service = RedisCacheService()

    def get_user(self, request) -> dict:
        token = get_jwt_token_from_request(request)
        user = self.redis_service.get_user_by_jwt(token)
        return user
