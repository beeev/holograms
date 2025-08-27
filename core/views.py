from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ReviewForm, UserCreationForm, UserProfileForm
from .models import Ad, Review, Brand, Agency, Tag
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.paginator import Paginator

def ad_list(request):
    qs = (Ad.objects
          .select_related("brand", "agency")
          .annotate(avg_rating=Avg("reviews__rating"), num_reviews=Count("reviews"))
          .order_by("-year", "title")[:50])
    return render(request, "ads/list.html", {"ads": qs})

def ad_detail(request, pk: int):
    ad = get_object_or_404(
        Ad.objects.select_related("brand", "agency")
        .annotate(avg_rating=Avg("reviews__rating"), num_reviews=Count("reviews")),
        pk=pk,
    )
    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(ad=ad, user=request.user).first()
    form = ReviewForm(instance=user_review)
    return render(request, "ads/detail.html", {"ad": ad, "form": form, "user_review": user_review})

@login_required
def review_submit(request, pk: int):
    ad = get_object_or_404(Ad, pk=pk)
    if request.method != "POST":
        return HttpResponseForbidden("POST only")
    instance = Review.objects.filter(ad=ad, user=request.user).first()
    form = ReviewForm(request.POST, instance=instance)
    if form.is_valid():
        review = form.save(commit=False)
        review.ad = ad
        review.user = request.user
        review.save()
        messages.success(request, "Your review has been saved.")
    else:
        messages.error(request, "Please fix the errors in your review.")
    return redirect("ad_detail", pk=ad.pk)

@login_required
def profile_edit(request):
    profile = request.user.profile  # created by signal
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("profile_edit")
    else:
        form = UserProfileForm(instance=profile)
    return render(request, "accounts/profile_edit.html", {"form": form})

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log them in straight away
            return redirect("ad_list")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

def profile_public(request, username: str):
    user = get_object_or_404(User.objects.select_related("profile"), username=username)
    # Latest reviews with ads & brands preloaded
    reviews = (
        Review.objects.filter(user=user)
        .select_related("ad", "ad__brand", "ad__agency")
        .order_by("-created_at")[:20]
    )
    return render(request, "accounts/profile_public.html", {
        "profile_user": user,
        "reviews": reviews,
    })  

def brand_list(request):
    brands = (
        Brand.objects
        .annotate(num_ads=Count("ads", distinct=True),
                  avg_rating=Avg("ads__reviews__rating"))
        .order_by("name")
    )
    return render(request, "brands/list.html", {"brands": brands})

def brand_detail(request, slug: str):
    brand = get_object_or_404(
        Brand.objects.annotate(
            num_ads=Count("ads", distinct=True),
            avg_rating=Avg("ads__reviews__rating"),
        ),
        slug=slug,
    )
    qs = (Ad.objects.filter(brand=brand)
          .select_related("brand", "agency")
          .annotate(avg_rating=Avg("reviews__rating"))
          .order_by("-year", "title"))
    page = Paginator(qs, 24).get_page(request.GET.get("page"))
    return render(request, "brands/detail.html", {"brand": brand, "page": page})


def agency_list(request):
    agencies = (
        Agency.objects
        .annotate(num_ads=Count("ads", distinct=True),
                  avg_rating=Avg("ads__reviews__rating"))
        .order_by("name")
    )
    return render(request, "agencies/list.html", {"agencies": agencies})


def agency_detail(request, slug: str):
    agency = get_object_or_404(
        Agency.objects.annotate(
            num_ads=Count("ads", distinct=True),
            avg_rating=Avg("ads__reviews__rating"),
        ),
        slug=slug,
    )
    qs = (Ad.objects.filter(agency=agency)
          .select_related("brand", "agency")
          .annotate(avg_rating=Avg("reviews__rating"))
          .order_by("-year", "title"))
    page = Paginator(qs, 24).get_page(request.GET.get("page"))
    return render(request, "agencies/detail.html", {"agency": agency, "page": page})

def search(request):
    q = (request.GET.get("q") or "").strip()
    tag = request.GET.get("tag") or ""
    year = request.GET.get("year") or ""
    qs = (Ad.objects.select_related("brand","agency")
          .prefetch_related("tags_m2m")
          .order_by("-year","title"))
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(brand__name__icontains=q) | Q(agency__name__icontains=q))
    if tag:
        qs = qs.filter(tags_m2m__slug=tag)
    if year.isdigit():
        qs = qs.filter(year=int(year))
    page = Paginator(qs.distinct(), 24).get_page(request.GET.get("page"))
    return render(request, "search/results.html", {
        "page": page, "q": q, "tag": tag, "year": year, "tags": Tag.objects.order_by("name"),
    })