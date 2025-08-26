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


class Brand(models.Model):
    name = models.CharField(max_length=200, unique=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self): return self.name


class Ad(models.Model):
    title = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="ads")
    agency = models.ForeignKey("Agency", on_delete=models.PROTECT, related_name="ads", null=True, blank=True)
    year = models.PositiveIntegerField(blank=True, null=True)
    youtube_url = models.URLField(help_text="Paste a YouTube URL")
    youtube_id = models.CharField(max_length=20, editable=False, db_index=True, unique=True)
    duration_sec = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.CharField(max_length=250, blank=True, help_text="Comma-separated")

    class Meta:
        indexes = [models.Index(fields=["youtube_id"])]
        ordering = ["-year", "title"]

    def __str__(self): return f"{self.title} ({self.brand})"

    @property
    def embed_url(self):
        return f"https://www.youtube.com/embed/{self.youtube_id}"