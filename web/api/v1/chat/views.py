from rest_framework.generics import GenericAPIView
from .serializers import InitSerializer, ChatListSerializer, MessageListSerializer, InitResponseSerializer
from .services import InitService, ChatService, ChatQueryService
from rest_framework.response import Response
from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ChatFilter
from .pagination import BasePageNumberPagination

class InitView(GenericAPIView):
    serializer_class = InitSerializer
    permission_classes = ()

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = request.COOKIES[settings.JWT_AUTH_COOKIE]

        service_init = InitService(token=token, id=serializer.validated_data['chat_user_id'])
        auth_user_info = service_init.check_token()
        chat_user_info = service_init.check_id_chat_user()

        key = cache.make_key('user_info', token)

        cache.set(key, auth_user_info, 3600)

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
        key = cache.make_key('user_info', self.request.COOKIES[settings.JWT_AUTH_COOKIE])
        user_id = cache.get(key)['id']
        return ChatQueryService.get_chats(user_id)

    def get(self, request):
        queryset = self.get_queryset()
        key = cache.make_key('user_info', self.request.COOKIES[settings.JWT_AUTH_COOKIE])
        user_id = cache.get(key)['id']
        filtered_queryset = self.filterset_class(self.request.GET, queryset=queryset, user_id=user_id).qs

        serializer = self.get_serializer(filtered_queryset, context={'user_id': user_id}, many=True)

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
        serializer = self.get_serializer(paginated_queryset, many=True)

        return paginator.get_paginated_response(serializer.data)
