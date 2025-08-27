# core/models.py
from django.db import models

# ---------- Core reference tables ----------

class Brand(models.Model):
    name = models.CharField(max_length=200, unique=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Agency(models.Model):
    name = models.CharField(max_length=200, unique=True)
    website = models.URLField(blank=True)
    country = models.CharField(max_length=120, blank=True)  # keep optional for now
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Person(models.Model):
    name = models.CharField(max_length=200, unique=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


# ---------- Ads & interactions ----------

class Ad(models.Model):
    title = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="ads")
    agency = models.ForeignKey(Agency, on_delete=models.PROTECT, related_name="ads",
                               null=True, blank=True)  # single lead agency (optional)
    year = models.PositiveIntegerField(null=True, blank=True)
    youtube_url = models.URLField(help_text="Paste a YouTube URL or ID")
    youtube_id = models.CharField(max_length=20, unique=True, db_index=True, editable=False)
    duration_sec = models.PositiveIntegerField(null=True, blank=True)
    tags = models.CharField(max_length=250, blank=True, help_text="Comma-separated")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["youtube_id"]),
            models.Index(fields=["-year", "title"]),
        ]
        ordering = ["-year", "title"]

    def __str__(self) -> str:
        return f"{self.title} — {self.brand.name}"


ROLE_CHOICES = [
    ("CD", "Creative Director"),
    ("CW", "Copywriter"),
    ("AD", "Art Director"),
    ("DIR", "Director"),
    ("DOP", "Director of Photography"),
    ("EDIT", "Editor"),
    ("CLR", "Colourist"),
    ("PM", "Producer/PM"),
    ("VFX", "VFX Lead"),
]

class Credit(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="credits")
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="credits")
    role = models.CharField(max_length=24, choices=ROLE_CHOICES)
    company = models.ForeignKey(Agency, on_delete=models.PROTECT,
                                null=True, blank=True, related_name="credits")  # optional: where they sat
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("ad", "person", "role")]  # avoids exact duplicate credits
        ordering = ["ad_id", "role", "person__name"]

    def __str__(self) -> str:
        return f"{self.person.name} · {self.get_role_display()} · {self.ad.title}"