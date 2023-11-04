from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import CursorPagination, LimitOffsetPagination
from rest_framework.response import Response

from .filters import ChatFilter
from .pagination import BasePageNumberPagination
from .serializers import ChatListSerializer, InitResponseSerializer, InitSerializer, MessageListSerializer
from .services import ChatQueryService, ChatService
from main.services import RedisCacheService, RedisUserStatus
from main.utils import get_jwt_token_from_request


class InitView(GenericAPIView):
    serializer_class = InitSerializer
    permission_classes = ()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = get_jwt_token_from_request(request)

        service_cache = RedisCacheService()
        auth_user_info = service_cache.get_user_by_jwt(token)
        chat_user_info = service_cache.get_user_by_id(serializer.validated_data['chat_user_id'])

        service_chat = ChatService(auth_user_info, chat_user_info)
        chat, created = service_chat.create_chat()

        if created:
            service_chat.new_chat_event(user_id=chat_user_info['id'], chat_id=chat.id, user_info=auth_user_info)

        data = {
            'user': auth_user_info,
            'chat_id': chat.id,
        }

        serializer_username = InitResponseSerializer(data)

        return Response(serializer_username.data, status=status.HTTP_200_OK)


class ChatListView(GenericAPIView):
    serializer_class = ChatListSerializer
    # TODO: ??? как здесь работает permission_classes
    permission_classes = ()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ChatFilter

    def get_queryset(self):
        # TODO: ??? повтор ниже
        token = get_jwt_token_from_request(self.request)
        service_cache = RedisCacheService()
        user = service_cache.get_user_by_jwt(token)
        return ChatQueryService.get_chats_with_user_id(user['id'])

    def get(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        # TODO: ??? повтор выше
        token = get_jwt_token_from_request(self.request)
        service_cache = RedisCacheService()
        user = service_cache.get_user_by_jwt(token)
        user_id = user['id']

        user_ids = ChatQueryService.get_ids_list_chat_participants(user_id)
        user_info_data = service_cache.get_users_by_ids(user_ids)

        service_redis = RedisUserStatus()
        users_status = service_redis.get_status_by_ids(user_ids)

        serializer = self.get_serializer(
            queryset,
            many=True,
            context={
                'user_data': user_info_data,
                'users_status': users_status,
                'user_id': user_id,
                'user_ids': user_ids,
            },
        )

        return Response(serializer.data)


class MessagesListView(GenericAPIView):
    # TODO: ??? нужно переделать ответ
    serializer_class = MessageListSerializer
    permission_classes = ()
    pagination_class = BasePageNumberPagination

    def get_queryset(self):
        return ChatQueryService.get_messages_for_chat(self.kwargs['chat_id'])

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        # TODO: !!! развернул список
        reversed_paginated_queryset = paginated_queryset[::-1]
        serializer = self.get_serializer(reversed_paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)
