from channels.sessions import CookieMiddleware
from django.conf import settings
from django.core.cache import cache
from main.services import RedisCacheService

class AuthTokenMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        cookies = scope['cookies']
        token = cookies.get(settings.JWT_AUTH_COOKIE)
        if not token:
            return

        service = RedisCacheService()
        user = service.get_user_by_jwt(token)

        scope['user'] = user

        return await self.app(scope, receive, send)

    async def check_token_response(self, token):
        pass


def AuthMiddlewareStack(inner):
    return CookieMiddleware(AuthTokenMiddleware(inner))
