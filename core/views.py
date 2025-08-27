from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ReviewForm, UserCreationForm, UserProfileForm
from .models import Ad, Review, Brand, Agency, Tag
from django.contrib.auth import login, get_user_model
from django.contrib.auth.models import User
from django.core.paginator import Paginator

User = get_user_model()

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
def review_submit(request, pk):
    ad = get_object_or_404(Ad, pk=pk)
    rating = int(request.POST.get("rating", 0))
    body = (request.POST.get("body") or "").strip()
    if rating < 0 or rating > 5:
        messages.error(request, "Rating must be 0–5.")
        return redirect(ad.get_absolute_url())
    Review.objects.update_or_create(
        ad=ad, user=request.user,
        defaults={"rating": rating, "body": body},
    )
    messages.success(request, "Review saved.")
    return redirect(ad.get_absolute_url())

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

def profile_public(request, username):
    user = get_object_or_404(User, username=username)
    profile = getattr(user, "profile", None)

    reviews_qs = (user.reviews   # related_name="reviews" on Review.user
                  .select_related("ad", "ad__brand")
                  .order_by("-created_at"))

    paginator = Paginator(reviews_qs, 10)  # 10 per page
    page = paginator.get_page(request.GET.get("page"))

    stats = {
        "num_reviews": reviews_qs.count(),
    }

    return render(request, "accounts/profile_public.html", {
        "profile_user": user,
        "profile": profile,
        "page": page,
        "stats": stats,
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