from django.shortcuts import render
from django.shortcuts import render


def index(request):
    return render(request, "chat/init.html")

def room(request):
    return render(request, "chat/room.html")
