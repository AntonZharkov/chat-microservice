from django.urls import include, path

app_name = 'v1'

urlpatterns = [
    path('chat/', include('api.v1.chat.urls')),
]
