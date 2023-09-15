from django.urls import path

from api.v1.chat import views

app_name = 'chat'

urlpatterns = [
    path('initialization/', views.InitView.as_view(), name='initialization'),
    path('chatnames/', views.ChatListView.as_view(), name='chatnames'),
]
