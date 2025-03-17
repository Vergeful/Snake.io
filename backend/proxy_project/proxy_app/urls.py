from django.urls import path
from . import views

urlpatterns = [
    path('create_player/', views.create_player, name='create_player'),
]