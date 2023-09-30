from django_filters import rest_framework as filters


class ChatFilter(filters.FilterSet):
    def __init__(self, *args, user_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id

    search = filters.CharFilter(method='search_filter')

    def search_filter(self, queryset, name, value):
        return queryset.filter(**{f'name__id_{self.user_id}__icontains': value})
