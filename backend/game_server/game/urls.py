from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("create_player/", views.create_player, name= "create_player"),
]
