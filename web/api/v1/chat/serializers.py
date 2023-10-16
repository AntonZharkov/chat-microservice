from rest_framework import serializers
from chat.models import Chat, Message, UserChat
from django.core.cache import cache
from main.utils import find_dict_in_list
class InitSerializer(serializers.Serializer):
    chat_user_id = serializers.IntegerField()


class UserChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserChat
        fields = ('user', )


class ChatListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    user_chats = UserChatSerializer(many=True)
    # avatar = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ('id', 'name', 'user_chats')
        prefetch_related_fields = ('user_chats', )

    # TODO: ???
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_id = representation.pop('user_chats')[0]['user']
        user_info = find_dict_in_list(self.context.get('user_data'), 'id', user_id)
        representation['avatar'] = user_info['avatar']
        return representation

    def get_name(self, obj):
        user_id = self.context.get('user_id')
        return obj.get_name(user_id)


class MessageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('author', 'body', 'created')


class UserDataSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    id = serializers.IntegerField()
    avatar = serializers.CharField()


class InitResponseSerializer(serializers.Serializer):
    user = UserDataSerializer()
    chat_id = serializers.CharField()
