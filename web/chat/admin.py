from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from chat.models import Chat, Message, UserChat


class UserChatInline(admin.TabularInline):
    model = UserChat
    readonly_fields = ('user', 'chat', 'created')


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    fields = ('name',)
    list_display = ('id', 'name')
    inlines = [
        UserChatInline,
    ]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('author', 'chat', 'short_body')
    fields = ('author', 'chat', 'body', 'created', 'updated')
    summernote_fields = ('body',)
    readonly_fields = ('created', 'updated')
    list_select_related = ('chat',)
    list_filter = ('chat',)
