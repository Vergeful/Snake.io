from django.urls import path, include
from . import views

urlpatterns = [
    path("create_player/", views.create_player, name= "create_player"),
]
