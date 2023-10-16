import requests
from requests.adapters import HTTPAdapter, Retry
from django.conf import settings
from urllib.parse import urljoin, urlencode
from django.core.exceptions import ValidationError
from typing import Optional
from django.core.cache import cache
from functools import wraps
from typing import Any, Callable, Union, TypeVar

# TODO: ???
RT = TypeVar('RT')


class BLogAuthService:
    def __init__(self):
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    @property
    def headers(self) -> dict:
        return {
            'Content-Type': 'application/json',
        }

    def request(self, method: str, url: str, data: Optional[dict] = None, json: Optional[dict] = None, params:  Optional[str] = None):
        return self.session.request(method=method, url=url, data=data, json=json, headers=self.headers, params=params)


class BlogRequestService:
    BLOG_URL = settings.BLOG_URL

    def __init__(self):
        self.auth_service = BLogAuthService()

    def _handle_response(self, response: requests.Response) -> dict:
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ValidationError(str(e))
        return response.json()

    def get_url(self, url: str) -> str:
        return urljoin(self.BLOG_URL, url)

    def verify_jwt_token(self, jwt_token: str) -> dict:
        url = self.get_url('/api/v1/auth/microauth/')
        data = {'token': jwt_token}
        response = self.auth_service.request('post', url, json=data)

        return self._handle_response(response)

    def check_id_chat_user(self, user_id: int) -> dict:
        url = self.get_url('/api/v1/auth/checkid/')
        data = {'chat_user_id': user_id}
        response = self.auth_service.request('post', url, data)

        return self._handle_response(response)

    def get_users_info(self, user_ids: list[int]) -> list[dict]:
        params = urlencode([( 'user_id', uid ) for uid in user_ids], doseq=True)
        url = self.get_url('/api/v1/chat/userinfo/')
        data = {'user_ids': user_ids}
        response = self.auth_service.request('get', url, json=data, params=params)

        return self._handle_response(response)

# TODO: ???
def cached_result(
    cache_key: str, timeout: int = 300, version: Union[int, str] = 1, many: bool = False
) -> Callable[[Callable[..., RT]], Callable[..., RT]]:
    def decorator(function: Callable[..., RT]) -> Callable[..., RT]:
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> RT:
            if not many:
                key = cache.make_key(cache_key, version)
                if key in cache:
                    return cache.get(key)
                result = function(*args, **kwargs)
                cache.set(key, result, timeout=timeout)
                print('result:', result)
                return result
            else:
                result = []
                for v in version:
                    key = cache.make_key(cache_key, v)
                    if key not in cache:
                        result = function(*args, **kwargs)
                        for user in result:
                            key = cache.make_key(cache_key, user['id'])
                            cache.set(key, user)
                        return result
                    result.append(cache.get(key))
                return result

        return wrapper

    return decorator


class RedisCacheService:
    def __init__(self) -> None:
        self.service = BlogRequestService()
        self.timeout = 10
    # TODO: !!!
    def _get_key(self, key: str, version: int | str) -> str:
        return cache.make_key(key, version)

    def get_user_by_jwt(self, token: str) -> dict:
        cache_key = self._get_key('user:jwt', token)
        if (cache_value := cache.get(cache_key)) is not None:
            return cache_value
        user_data: dict = self.service.verify_jwt_token(token)

        if not user_data:
            return {}
        cache.set(cache_key, user_data, timeout=self.timeout)
        return user_data

        # return cached_result('user:jwt', version=token)(self.service.verify_jwt_token)(token)

    def get_user_by_id(self, user_id: int) -> dict:
        cache_key = self._get_key('user:id', user_id)
        # TODO: !!! использовал =:
        if (cache_value := cache.get(cache_key)) is not None:
            return cache_value
        response_data: list[dict] = self.service.get_users_info([user_id])

        if not response_data:
            return {}
        user_data: dict = response_data[0]
        cache.set(cache_key, user_data, timeout=self.timeout)
        return user_data

    def get_users_by_ids(self, user_ids: list[int]) -> list[dict]:
        result = []
        for user_id in user_ids:
            cache_key = self._get_key('user:id', user_id)
            if cache_key not in cache:
                result: list = self.service.get_users_info(user_ids)
                for user_data in result:
                    cache_key = self._get_key('user:id', user_data['id'])
                    cache.set(cache_key, user_data, timeout=self.timeout)
                return result
            else:
                result.append(cache.get(cache_key))

        return result
