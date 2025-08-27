from django import forms
from .models import Ad, Review, UserProfile
from .utils import extract_youtube_id
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class AdAdminForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        url = cleaned.get("youtube_url", "")
        yt_id = extract_youtube_id(url or "")
        if not yt_id:
            raise forms.ValidationError("Please paste a valid YouTube URL or ID.")
        cleaned["youtube_id"] = yt_id
        return cleaned
    
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "body")
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 0, "max": 5}),
            "body": forms.Textarea(attrs={"rows": 3}),
        }
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("display_name", "city", "bio", "avatar")