from rest_framework import serializers
from chat.models import Chat, Message
from django.core.cache import cache

class InitSerializer(serializers.Serializer):
    chat_user_id = serializers.IntegerField()


class ChatListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ('id', 'name', )

    def get_name(self, obj):
        # TODO: ????
        user_id = self.context.get('user_id')
        return obj.get_name(user_id)

class MessageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('author', 'body', 'created')


class UserDataSerializer(serializers.Serializer):
    # TODO: add avatar
    full_name = serializers.CharField()
    id = serializers.IntegerField()


class InitResponseSerializer(serializers.Serializer):
    user = UserDataSerializer()
    chat_id = serializers.CharField()
