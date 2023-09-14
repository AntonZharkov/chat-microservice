from django.urls import path

from . import views


urlpatterns = [
    path("init/", views.index, name="init"),
    path("", views.room, name="room"),
]
