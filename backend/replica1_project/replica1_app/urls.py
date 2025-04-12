from django.urls import path
from . import views

urlpatterns = [
    path("create_player/", views.create_player, name= "create_player"),
    path("health_check/", views.health_check, name= "health_check"),
    path("update_primary/", views.update_primary, name= "update_primary"),
    path("update_food_list/", views.update_local_food_list, name= "update_local_food_list")
]