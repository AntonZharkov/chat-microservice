from django.urls import path

from api.v1.chat import views

app_name = 'chat'

urlpatterns = [
    path('initialization/', views.InitView.as_view(), name='initialization'),
    path('chatlist/', views.ChatListView.as_view(), name='chatnames'),
    path('messages/<str:chat_id>/', views.MessagesListView.as_view(), name='messages'),
]
