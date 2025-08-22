from django.contrib import admin
from django.urls import path
from core.api import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health", health)
]