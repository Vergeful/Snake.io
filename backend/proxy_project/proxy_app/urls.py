from django.urls import path
from . import views

urlpatterns = [
    path('create_player/', views.create_player, name='create_player'),
    path('trigger_election/', views.trigger_leader_election, name="trigger_election")
]