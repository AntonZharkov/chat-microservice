from rest_framework import serializers
from chat.models import Chat, UserChat, Message
from django.core.cache import cache

class InitSerializer(serializers.Serializer):
    chat_user_id = serializers.IntegerField()


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ('name', )
