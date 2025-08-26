from django.contrib import admin
from .models import Agency, Brand, Ad
from .forms import AdAdminForm
# Register your models here later.


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "website", "created_at")
    search_fields = ("name", "city")
    list_filter = ("city",)
    
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "website", "created_at")
    search_fields = ("name",)

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    form = AdAdminForm
    list_display = ("title", "brand", "agency", "year", "youtube_id", "created_at")
    list_filter = ("brand", "year")
    search_fields = ("title", "brand__name", "youtube_id")
    autocomplete_fields = ("brand", "agency")