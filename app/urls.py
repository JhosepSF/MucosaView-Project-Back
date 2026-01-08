from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from records.views import PatientViewSet, VisitViewSet, PhotoViewSet, media_by_hash, mucosa_registro, mucosa_fotos, mucosa_visita

router = DefaultRouter()
router.register(r"patients", PatientViewSet, basename="patients")
router.register(r"visits", VisitViewSet, basename="visits")
router.register(r"photos", PhotoViewSet, basename="photos")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/media/by-hash/<str:sha256>", media_by_hash, name="media-by-hash"),
    path("api/mucosa/registro", mucosa_registro),
    path("api/mucosa/registro/<str:dni>/fotos", mucosa_fotos),
    path("api/mucosa/registro/<str:dni>/visita", mucosa_visita), 
]