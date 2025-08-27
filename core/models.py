# core/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ValidationError
from datetime import date
from .utils import extract_youtube_id

# ---------- Core reference tables ----------

class Brand(models.Model):
    name = models.CharField(max_length=200, unique=True)
    website = models.URLField(blank=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self): return self.name
    def get_absolute_url(self):
        return reverse("brand_detail", args=[self.slug])


class Agency(models.Model):
    name = models.CharField(max_length=200, unique=True)
    website = models.URLField(blank=True)
    country = models.CharField(max_length=120, blank=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self): return self.name
    def get_absolute_url(self):
        return reverse("agency_detail", args=[self.slug])


class Person(models.Model):
    name = models.CharField(max_length=200, unique=True)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


# ---------- Ads & interactions ----------

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    def __str__(self): return self.name

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
    tags_m2m = models.ManyToManyField(Tag, blank=True, related_name="ads")
    created_at = models.DateTimeField(auto_now_add=True)
    def clean(self):
        # Year sanity
        if self.year and (self.year < 1900 or self.year > date.today().year + 1):
            raise ValidationError({"year": "Year looks out of range."})

        # Normalise YouTube and enforce uniqueness at the form/ORM level
        yt_input = (self.youtube_url or "").strip()
        yt_id = extract_youtube_id(yt_input)
        if not yt_id:
            raise ValidationError({"youtube_url": "Please enter a valid YouTube URL or ID."})

        self.youtube_id = yt_id  # ensure the unique field is populated

        # Optional: keep youtube_url as a canonical watch url
        self.youtube_url = f"https://www.youtube.com/watch?v={yt_id}"

        # Check for duplicates in DB (exclude self when editing)
        qs = Ad.objects.filter(youtube_id=yt_id)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError({"youtube_url": "This YouTube video is already in Holograms."})

    def save(self, *args, **kwargs):
        # Belt-and-braces: ensure youtube_id is set before saving
        if not self.youtube_id:
            yt_id = extract_youtube_id((self.youtube_url or "").strip())
            if yt_id:
                self.youtube_id = yt_id
                # keep canonical form
                self.youtube_url = f"https://www.youtube.com/watch?v={yt_id}"
        super().save(*args, **kwargs)

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
    

class Review(models.Model):
    ad = models.ForeignKey("Ad", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(default=0)  # 0–5
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("ad", "user")]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} → {self.ad} ({self.rating})"
    
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)  # needs MEDIA config
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def get_absolute_url(self):
        return reverse("profile_public", args=[self.user.username])

    def __str__(self) -> str:
        return self.display_name or self.user.username
    
