from django.contrib import admin
from .models import Patient, Visit, Photo

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("dni","nombre","apellido","region","provincia","distrito","created_at")
    search_fields = ("dni","nombre","apellido")

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("patient","visit_number","bpm","hemoglobina","spo2","lmp_date","version","updated_at")
    list_filter = ("patient",)

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("visit","type","index","sha256","size","created_at")
    search_fields = ("sha256",)