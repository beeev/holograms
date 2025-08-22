from django.http import JsonResponse

def health(_):
    return JsonResponse({"status": "ok"})