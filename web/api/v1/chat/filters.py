from django_filters import rest_framework as filters
from django.conf import settings
from main.services import BlogRequestService, RedisCacheService
from main.utils import get_jwt_token_from_request

class ChatFilter(filters.FilterSet):
    search = filters.CharFilter(method='search_filter')

    def search_filter(self, queryset, name, value):
        token = get_jwt_token_from_request(self.request)
        service = RedisCacheService()
        user = service.get_user_by_jwt(token)
        return queryset.filter(**{f'name__id_{user["id"]}__icontains': value})
