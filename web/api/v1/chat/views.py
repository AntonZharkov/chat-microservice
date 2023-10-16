from rest_framework.generics import GenericAPIView
from .serializers import InitSerializer, ChatListSerializer, MessageListSerializer, InitResponseSerializer
from .services import InitService, ChatService, ChatQueryService
from main.services import BlogRequestService, RedisCacheService, cached_result
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

        token = request.COOKIES[settings.JWT_AUTH_COOKIE]

        service_init = InitService(token=token, id=serializer.validated_data['chat_user_id'])
        auth_user_info = service_init.check_token()
        chat_user_info = service_init.check_id_chat_user()

        key_auth = cache.make_key('user', token)
        cache.set(key_auth, auth_user_info, 3600)

        key_chat_user = cache.make_key('user', chat_user_info['id'])
        cache.set(key_chat_user, chat_user_info, 3600)

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
        # TODO: !!! переделал
        token = get_jwt_token_from_request(self.request)
        user = cached_result('user', version=token)(BlogRequestService().verify_jwt_token)(token)
        return ChatQueryService.get_chats_with_user_id(user['id'])

    def get(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        # TODO: !!! переделал
        service = RedisCacheService()
        token = get_jwt_token_from_request(self.request)
        user = cached_result('user', version=token)(BlogRequestService().verify_jwt_token)(token)
        user_id = user['id']

        # TODO: !!!
        user_ids = ChatQueryService.get_ids_list_chat_participants(user_id)
        user_info_data = service.get_users_by_ids(user_ids)

        serializer = self.get_serializer(queryset, context={'user_data': user_info_data, 'user_id': user_id}, many=True)

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
