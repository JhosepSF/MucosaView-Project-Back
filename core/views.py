import shutil
from django.http import JsonResponse
from records.models import Photo

def diagnostics(request):
    total, used, free = shutil.disk_usage(".")
    out = {
        "photos": Photo.objects.count(),
        "disk_free_gb": round(free / (1024**3), 2),
    }
    return JsonResponse(out)