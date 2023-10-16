from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid4

User = get_user_model()

def hex_uuid() -> str:
    return uuid4().hex

class Chat(models.Model):
    '''
    format of name is
    {'id_<userId>': 'chat_name', 'id_<userId>': 'chat_name'}
    '''
    id = models.CharField(max_length=32, primary_key=True, db_index=True, editable=False, default=hex_uuid)
    name = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return str(self.name)

    def get_name(self, user_id: int):
        return self.name[f'id_{user_id}']


class UserChat(models.Model):
    user = models.PositiveIntegerField()
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='user_chats')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'chat'), name='unique_user_in_chat')]

class Message(models.Model):
    author = models.PositiveIntegerField()
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created']

    @property
    def short_body(self):
        return self.body[:50]
