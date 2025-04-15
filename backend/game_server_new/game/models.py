from django.db import models

class Player(models.Model): 
    name = models.CharField(max_length=100, unique=True) 
    x = models.IntegerField(default=400) 
    y = models.IntegerField(default=300) 
    size = models.IntegerField(default=40) 
    speed = models.IntegerField(default=150) 
    score = models.IntegerField(default=0) 
    color = models.CharField(max_length=100) 


    def __str__(self): 
        return self.name