from django.contrib import admin
from chat.models import Chat, Message, UserChat
from django_summernote.admin import SummernoteModelAdmin


class UserChatInline(admin.TabularInline):
    model = UserChat
    readonly_fields = ('user', 'chat', 'created')

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    fields = ('name',)
    inlines = [
        UserChatInline,
    ]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('author', 'chat', 'short_body')
    fields = ('author', 'chat', 'body', 'created', 'updated')
    summernote_fields = ('body',)
    readonly_fields = ('created', 'updated')
    list_select_related = ('chat', 'author')
    list_filter = ('chat',)
