from django.db import models
from django.contrib import admin 

class Agency(models.Model):
    name = models.CharField(max_length=200, unique=True)
    city = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name