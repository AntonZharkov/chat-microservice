from rest_framework import serializers

class InitSerializer(serializers.Serializer):
    chat_user_id = serializers.IntegerField()
