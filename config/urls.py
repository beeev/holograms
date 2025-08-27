from django.contrib import admin
from django.urls import path, include
from core.api import health
from core.views import ad_list, ad_detail, review_submit, signup, profile_edit, profile_public,brand_list, brand_detail, agency_list, agency_detail, search


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("ads/", ad_list, name="ad_list"),
    path("ads/<int:pk>/", ad_detail, name="ad_detail"),
    path("ads/<int:pk>/review/", review_submit, name="review_submit"),
    path("accounts/", include("django.contrib.auth.urls")),  # login/logout/etc.
    path("accounts/signup/", signup, name="signup"),
    path("accounts/profile/", profile_edit, name="profile_edit"),
    path("u/<str:username>/", profile_public, name="profile_public"),
    path("search/", search, name="search"),

    path("brands/", brand_list, name="brand_list"),
    path("brands/<slug:slug>/", brand_detail, name="brand_detail"),

    path("agencies/", agency_list, name="agency_list"),
    path("agencies/<slug:slug>/", agency_detail, name="agency_detail"),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:  # only serve media in dev
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)