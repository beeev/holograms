from django.contrib import admin
from django.urls import path
from core.api import health
from core.views import ad_list, ad_detail


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("ads/", ad_list, name="ad_list"),
    path("ads/<int:pk>/", ad_detail, name="ad_detail"),
]