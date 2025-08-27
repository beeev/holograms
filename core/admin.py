from django.contrib import admin, messages
from django import forms
from django.utils.text import slugify
from .models import Brand, Agency, Person, Ad, Review, UserProfile, Tag, Credit
from django.contrib.admin.helpers import ActionForm


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name","website","created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ("name","country","website","created_at")
    search_fields = ("name","country")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

class CreditInline(admin.TabularInline):
    model = Credit
    extra = 1
    autocomplete_fields = ("person",)
    fields = ("person", "role", "company")

class ApplyTagActionForm(ActionForm):
    tag = forms.CharField(required=True, help_text="Type a tag name, e.g. ‘automotive’")

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ("title","brand","agency","year","youtube_id","created_at")
    list_filter = ("brand","agency","year")
    search_fields = ("title","brand__name","agency__name","youtube_id")
    autocomplete_fields = ("brand","agency")
    inlines = [CreditInline]
    filter_horizontal = ("tags_m2m",)
    actions = ["apply_tag"]
    action_form = ApplyTagActionForm  # 👈 adds a text box to the actions bar

    def apply_tag(self, request, queryset):
        tag_name = (request.POST.get("tag") or "").strip()
        if not tag_name:
            messages.error(request, "Please type a tag name before running the action.")
            return
        tag, _ = Tag.objects.get_or_create(slug=slugify(tag_name), defaults={"name": tag_name})
        updated = 0
        for ad in queryset:
            ad.tags_m2m.add(tag)
            updated += 1
        self.message_user(request, f"Applied tag “{tag.name}” to {updated} ad(s).", level=messages.SUCCESS)

    apply_tag.short_description = "Apply tag (enter name in box, then run)"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("ad", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("ad__title", "user__username", "body")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "city", "updated_at")
    search_fields = ("user__username", "display_name", "city")
