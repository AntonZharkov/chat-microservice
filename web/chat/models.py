from django.db import models
from django.contrib.auth import get_user_model
from uuid import uuid4

User = get_user_model()

def hex_uuid() -> str:
    return uuid4().hex

class Chat(models.Model):
    # TODO: docstring
    id = models.CharField(max_length=32, primary_key=True, db_index=True, editable=False, default=hex_uuid)
    name = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    @classmethod
    def choose_name(cls, queryset, auth_id: str):
        for obj in queryset:
            obj.name = obj.name[auth_id]
        return queryset


class UserChat(models.Model):
    user = models.PositiveIntegerField()
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='user_chats')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'chat'), name='unique_user_in_chat')]

class Message(models.Model):
    author = models.ForeignKey(User, related_name='messages', on_delete=models.SET_NULL, null=True)
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)

    @property
    def short_body(self):
        return self.body[:50]
