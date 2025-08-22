from django.contrib import admin
from .models import Agency
# Register your models here later.


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "website", "created_at")
    search_fields = ("name", "city")
    list_filter = ("city",)
