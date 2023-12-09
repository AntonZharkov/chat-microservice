import datetime
from dataclasses import dataclass
from typing import Any, Optional, TypeVar
from urllib.parse import urlencode, urljoin

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from requests.adapters import HTTPAdapter, Retry

RT = TypeVar('RT')

@dataclass
class UserData:
    id: int
    full_name: str
    avatar: str


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

    def request(
        self,
        method: str,
        url: str,
        data: Optional[dict] = None,
        json: Optional[dict] = None,
        params: Optional[str] = None,
    ):
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
        params = urlencode([('user_id', uid) for uid in user_ids], doseq=True)
        url = self.get_url('/api/v1/chat/userinfo/')
        data = {'user_ids': user_ids}
        response = self.auth_service.request('get', url, json=data, params=params)

        return self._handle_response(response)


class RedisCacheService:
    def __init__(self) -> None:
        self.service = BlogRequestService()
        self.timeout = 10

    def _get_key(self, key: str, version: int | str) -> str:
        return cache.make_key(key, version)

    def get_user_by_jwt(self, token: str) -> dict:
        cache_key = self._get_key('user:jwt', token)
        if (cache_value := cache.get(cache_key)) is not None:
            return cache_value
        user_data: dict = self.service.verify_jwt_token(token)
        print(user_data)

        if not user_data:
            return {}
        cache.set(cache_key, user_data, timeout=self.timeout)
        return user_data

    def get_user_by_id(self, user_id: int) -> dict:
        cache_key = self._get_key('user:id', user_id)

        if cache_value := cache.get(cache_key):
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


class RedisUserStatus:
    def _get_key(self, user_id: int) -> str:
        return cache.make_key('user:status', user_id)

    def _get_data(self, online: bool, user_id: int, date=None):
        return {
            'online': online,
            'date': date,
            'id': user_id,
        }

    def set_online(self, user_id: int):
        key = self._get_key(user_id)
        data = self._get_data(online=True, user_id=user_id)
        cache.set(key, data, timeout=None)

    def set_offline(self, user_id: int):
        key = self._get_key(user_id)
        data = self._get_data(online=False, user_id=user_id, date=datetime.datetime.now())
        cache.set(key, data, timeout=None)

    def get_status(self, user_id: int) -> dict:
        key = self._get_key(user_id)
        return cache.get(key)

    def get_status_by_ids(self, user_ids: list[int]) -> list[dict]:
        result = []
        for user_id in user_ids:
            cache_key = self._get_key(user_id)
            user_status_data = cache.get(cache_key)
            if user_status_data:
                result.append(cache.get(cache_key))
            else:
                data = self._get_data(online=False, user_id=user_id)
                result.append(data)

        return result
