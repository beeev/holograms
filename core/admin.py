from django.contrib import admin
from .models import Brand, Agency, Person, Ad, Credit, Review, UserProfile

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name","website","created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ("name","country","website","created_at")
    search_fields = ("name","country")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name","website","created_at")
    search_fields = ("name",)

class CreditInline(admin.TabularInline):
    model = Credit
    extra = 1
    autocomplete_fields = ("person","company")

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ("title","brand","agency","year","youtube_id","created_at")
    list_filter = ("brand","agency","year")
    search_fields = ("title","brand__name","agency__name","youtube_id")
    autocomplete_fields = ("brand","agency")
    inlines = [CreditInline]

    @admin.register(Review)
    class ReviewAdmin(admin.ModelAdmin):
     list_display = ("ad", "user", "rating", "created_at")
     list_filter = ("rating", "created_at")
     search_fields = ("ad__title", "user__username", "body")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "city", "updated_at")
    search_fields = ("user__username", "display_name", "city")