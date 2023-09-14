from rest_framework.generics import GenericAPIView
from .serializers import InitSerializer
from .services import InitService, ChatService
from rest_framework.response import Response
from django.conf import settings
from django.core.cache import cache
from rest_framework import status

class InitView(GenericAPIView):
    serializer_class = InitSerializer
    permission_classes = ()

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)


        service_init = InitService(token=request.COOKIES[settings.JWT_AUTH_COOKIE], id=serializer.validated_data['chat_user_id'])
        auth_user_info = service_init.check_token()
        chat_user_info = service_init.check_id_chat_user()

        key = cache.make_key('user_info', auth_user_info['id'])
        print(f'KEY = {key}')
        print(f'{key=}')

        cache.set('auth_user_info', auth_user_info, 3600)

        service_chat = ChatService(auth_user_info, chat_user_info)
        service_chat.create_chat()


        return Response(
            {'detail': True},
            status=status.HTTP_200_OK
        )

