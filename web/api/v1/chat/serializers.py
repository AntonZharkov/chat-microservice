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

    class Meta:
        model = Chat
        fields = ('id', 'name', 'user_chats')
        prefetch_related_fields = ('user_chats', )

    # TODO: !!!! переделал
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_id = representation.pop('user_chats')[0]['user']
        user_info = find_dict_in_list(self.context.get('user_data'), 'id', user_id)
        if user_info:
            representation['avatar'] = user_info['avatar']
            representation['user_id'] = user_info['id']
        else:
            representation['name'] = 'Unknown user'
            representation['avatar'] = 'address'
            representation['user_id'] = user_id
        return representation

    def get_name(self, obj):
        user_id = self.context.get('user_id')
        return obj.get_name(user_id)


class MessageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('author', 'body', 'created')


class UserSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    id = serializers.IntegerField()
    avatar = serializers.CharField()


class InitResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    chat_id = serializers.CharField()
