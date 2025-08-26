from django import forms
from .models import Ad
from .utils import extract_youtube_id

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