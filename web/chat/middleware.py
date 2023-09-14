import httpx
from rest_framework.response import Response
from rest_framework import status
from channels.sessions import CookieMiddleware
from django.conf import settings
class AuthTokenMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        cookies = scope['cookies']
        token = cookies.get(settings.JWT_AUTH_COOKIE)
        if not token:
            return

        print(token)
        # user_id = '' #await self.check_token(token)
        # if not user_id:
        #     return Response(
        #         {'_detail': 'Unathorized user'},
        #         status=status.HTTP_401_UNAUTHORIZED,
        #     )


        # scope['user_id'] = user_id
        return await self.app(scope, receive, send)

    async def check_token_response(self, token):
        pass


def AuthMiddlewareStack(inner):
    return CookieMiddleware(AuthTokenMiddleware(inner))
