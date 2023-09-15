from rest_framework.generics import GenericAPIView
from .serializers import InitSerializer, ChatSerializer
from .services import InitService, ChatService
from rest_framework.response import Response
from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from chat.models import Chat

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
        service_chat.create_chat()


        return Response(
            {'detail': True},
            status=status.HTTP_200_OK
        )


class ChatListView(GenericAPIView):
    serializer_class = ChatSerializer
    # TODO: ??? как здесь работает права доступа
    # permission_classes = ()

    def get_queryset(self):
        key = cache.make_key('user_info', self.request.COOKIES[settings.JWT_AUTH_COOKIE])
        auth_id = cache.get(key)['id']
        return Chat.choose_name(Chat.objects.filter(user_chats__user=auth_id), str(auth_id))

    def get(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)
