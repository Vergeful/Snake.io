from django.db import models

# Create your models here.
class Player(models.Model): 
    name = models.CharField(max_length=100, unique=True) 
    color = models.CharField(max_length=100) 
    speed = models.IntegerField(default=200) 
    score = models.IntegerField(default=0) 

    def __str__(self): 
        return self.name