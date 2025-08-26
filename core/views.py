from django.shortcuts import get_object_or_404, render
from .models import Ad

def ad_list(request):
    qs = Ad.objects.select_related("brand").order_by("-year", "title")[:50]
    return render(request, "ads/list.html", {"ads": qs})

def ad_detail(request, pk: int):
    ad = get_object_or_404(Ad.objects.select_related("brand"), pk=pk)
    return render(request, "ads/detail.html", {"ad": ad})