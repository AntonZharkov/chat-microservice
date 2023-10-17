from rest_framework.generics import GenericAPIView
from .serializers import ChatListSerializer, MessageListSerializer, InitSerializer, InitResponseSerializer
from .services import ChatService, ChatQueryService
from main.services import BlogRequestService, RedisCacheService
from rest_framework.response import Response
from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ChatFilter
from .pagination import BasePageNumberPagination
from main.utils import get_jwt_token_from_request

class InitView(GenericAPIView):
    serializer_class = InitSerializer
    permission_classes = ()

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # TODO: !!!
        token = get_jwt_token_from_request(request)

        service_cache = RedisCacheService()
        auth_user_info = service_cache.get_user_by_jwt(token)
        chat_user_info = service_cache.get_user_by_id(serializer.validated_data['chat_user_id'])

        service_chat = ChatService(auth_user_info, chat_user_info)
        chat = service_chat.create_chat()

        data = {
            'user': auth_user_info,
            'chat_id': chat.id,
        }

        serializer_username = InitResponseSerializer(data)

        return Response(
            serializer_username.data,
            status=status.HTTP_200_OK
        )


class ChatListView(GenericAPIView):
    serializer_class = ChatListSerializer
    # TODO: ??? как здесь работает permission_classes
    permission_classes = ()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ChatFilter

    def get_queryset(self):
        # TODO: ??? повтор ниже
        token = get_jwt_token_from_request(self.request)
        service = RedisCacheService()
        user = service.get_user_by_jwt(token)
        return ChatQueryService.get_chats_with_user_id(user['id'])

    def get(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        # TODO: ??? повтор выше
        token = get_jwt_token_from_request(self.request)
        service = RedisCacheService()
        user = service.get_user_by_jwt(token)
        user_id = user['id']

        # TODO: !!!
        user_ids = ChatQueryService.get_ids_list_chat_participants(user_id)
        user_info_data = service.get_users_by_ids(user_ids)

        serializer = self.get_serializer(queryset, context={'user_data': user_info_data, 'user_id': user_id, 'user_ids': user_ids}, many=True)

        return Response(serializer.data)



class MessagesListView(GenericAPIView):
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
        reversed(paginated_queryset)
        serializer = self.get_serializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)
