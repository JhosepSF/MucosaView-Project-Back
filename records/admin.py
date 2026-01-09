from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Patient, Visit, Photo

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("dni", "nombre_completo", "edad", "ubicacion", "total_visitas", "created_at")
    list_filter = ("region", "provincia", "created_at")
    search_fields = ("dni", "nombre", "apellido", "direccion")
    readonly_fields = ("id", "created_at", "updated_at", "maps_link")
    
    fieldsets = (
        ("Información Personal", {
            "fields": ("dni", "nombre", "apellido", "edad")
        }),
        ("Ubicación", {
            "fields": ("region", "provincia", "distrito", "direccion", "maps_url", "maps_link")
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = "Nombre Completo"
    
    def ubicacion(self, obj):
        return f"{obj.distrito}, {obj.provincia}"
    ubicacion.short_description = "Ubicación"
    
    def total_visitas(self, obj):
        count = obj.visits.count()
        url = reverse("admin:records_visit_changelist") + f"?patient__id__exact={obj.id}"
        return format_html('<a href="{}">{} visitas</a>', url, count)
    total_visitas.short_description = "Visitas"
    
    def maps_link(self, obj):
        if obj.maps_url:
            return format_html('<a href="{}" target="_blank">Ver en Google Maps</a>', obj.maps_url)
        return "-"
    maps_link.short_description = "Mapa"

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("paciente_info", "visit_number", "datos_clinicos", "semanas_gestacion", "total_fotos", "updated_at")
    list_filter = ("visit_number", "created_at", "patient__region")
    search_fields = ("patient__dni", "patient__nombre", "patient__apellido")
    readonly_fields = ("id", "gestational_weeks", "created_at", "updated_at", "patient_link")
    
    fieldsets = (
        ("Paciente", {
            "fields": ("patient", "patient_link", "visit_number")
        }),
        ("Datos Clínicos", {
            "fields": ("bpm", "hemoglobina", "spo2", "lmp_date", "gestational_weeks")
        }),
        ("Control de Versión", {
            "fields": ("version",),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("id", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    
    def paciente_info(self, obj):
        url = reverse("admin:records_patient_change", args=[obj.patient.id])
        return format_html('<a href="{}">{} - {} {}</a>', url, obj.patient.dni, obj.patient.nombre, obj.patient.apellido)
    paciente_info.short_description = "Paciente"
    
    def datos_clinicos(self, obj):
        return format_html(
            '<span style="color: #e74c3c;">❤️ {}</span> | '
            '<span style="color: #c0392b;">🩸 {}</span> | '
            '<span style="color: #3498db;">💨 {}%</span>',
            obj.bpm, obj.hemoglobina, obj.spo2
        )
    datos_clinicos.short_description = "Signos Vitales"
    
    def semanas_gestacion(self, obj):
        if obj.gestational_weeks:
            color = "#27ae60" if obj.gestational_weeks >= 37 else "#e67e22"
            return format_html('<span style="color: {}; font-weight: bold;">🤰 {} semanas</span>', color, obj.gestational_weeks)
        return "-"
    semanas_gestacion.short_description = "Gestación"
    
    def total_fotos(self, obj):
        count = obj.photos.count()
        url = reverse("admin:records_photo_changelist") + f"?visit__id__exact={obj.id}"
        if count == 6:
            return format_html('<a href="{}">📸 {} fotos ✅</a>', url, count)
        else:
            return format_html('<a href="{}" style="color: #e74c3c;">📸 {} fotos ⚠️</a>', url, count)
    total_fotos.short_description = "Fotos"
    
    def patient_link(self, obj):
        url = reverse("admin:records_patient_change", args=[obj.patient.id])
        return format_html('<a href="{}">Ver paciente completo</a>', url)
    patient_link.short_description = "Ir a Paciente"

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("miniatura", "paciente_info", "tipo_index", "tamano", "created_at", "acciones")
    list_filter = ("type", "created_at", "visit__patient__region")
    search_fields = ("visit__patient__dni", "visit__patient__nombre", "original_name", "sha256")
    readonly_fields = ("id", "sha256", "size", "content_type", "created_at", "preview", "visit_link", "patient_link")
    
    fieldsets = (
        ("Relación", {
            "fields": ("visit", "visit_link", "patient_link")
        }),
        ("Clasificación", {
            "fields": ("type", "index")
        }),
        ("Archivo", {
            "fields": ("file", "preview", "original_name", "content_type", "size", "sha256")
        }),
        ("Metadata", {
            "fields": ("id", "created_at"),
            "classes": ("collapse",)
        }),
    )
    
    def miniatura(self, obj):
        if obj.file:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />', obj.file.url)
        return "-"
    miniatura.short_description = "Vista"
    
    def paciente_info(self, obj):
        patient = obj.visit.patient
        url = reverse("admin:records_patient_change", args=[patient.id])
        return format_html('<a href="{}">{} - {} {}</a><br/><small>Visita #{}</small>', 
                          url, patient.dni, patient.nombre, patient.apellido, obj.visit.visit_number)
    paciente_info.short_description = "Paciente"
    
    def tipo_index(self, obj):
        tipos = {"CONJ": "👁️ Conjuntiva", "LAB": "👄 Labio", "IND": "👆 Índice"}
        tipo_text = tipos.get(obj.type, obj.type)
        return format_html('<strong>{}</strong> #{}', tipo_text, obj.index)
    tipo_index.short_description = "Tipo"
    
    def tamano(self, obj):
        if obj.size:
            mb = obj.size / (1024 * 1024)
            color = "#27ae60" if mb < 2 else "#e67e22"
            return format_html('<span style="color: {};">{} MB</span>', color, f'{mb:.2f}')
        return "-"
    tamano.short_description = "Tamaño"
    
    def acciones(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" style="margin-right: 10px;">🔍 Ver</a>'
                '<a href="{}" download>⬇️ Descargar</a>',
                obj.file.url, obj.file.url
            )
        return "-"
    acciones.short_description = "Acciones"
    
    def preview(self, obj):
        if obj.file:
            return format_html('<img src="{}" style="max-width: 400px; max-height: 400px;" />', obj.file.url)
        return "-"
    preview.short_description = "Preview"
    
    def visit_link(self, obj):
        url = reverse("admin:records_visit_change", args=[obj.visit.id])
        return format_html('<a href="{}">Ver visita completa</a>', url)
    visit_link.short_description = "Ir a Visita"
    
    def patient_link(self, obj):
        url = reverse("admin:records_patient_change", args=[obj.visit.patient.id])
        return format_html('<a href="{}">Ver paciente completo</a>', url)
    patient_link.short_description = "Ir a Paciente"