import uuid
from pathlib import Path
from django.db import models
from django.utils import timezone

class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dni = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.PositiveSmallIntegerField()
    region = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    distrito = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    maps_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.dni} - {self.nombre} {self.apellido}"

class Visit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="visits")

    # Datos Obstétricos
    bpm = models.PositiveSmallIntegerField(null=True, blank=True) # Pulsaciones por minuto
    hemoglobina = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True) # g/dL
    spo2 = models.PositiveSmallIntegerField(null=True, blank=True) # % Oxígeno en sangre
    lmp_date = models.DateField(null=True, blank=True) # Fecha del último periodo (FUR)

    # Control de versiones (optimistic locking via ETag)
    version = models.PositiveIntegerField(default=1)

    # Número de visita por paciente (para el nombre de fotos)
    visit_number = models.PositiveSmallIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["patient", "visit_number"], name="uniq_patient_visitnumber"),
        ]

    @property
    def gestational_weeks(self):
        if not self.lmp_date:
            return None
        today = timezone.localdate()
        days = (today - self.lmp_date).days
        return max(0, days // 7)

    def __str__(self):
        return f"Visit {self.visit_number} of {self.patient.dni}"

def photo_upload_to(instance, filename):
    dni = instance.visit.patient.dni
    if instance.type == Photo.TYPE_CONJ:
        tipo = "Conjuntiva"
    elif instance.type == Photo.TYPE_LAB:
        tipo = "Labio"
    else:
        tipo = "Indice"
    v = instance.visit.visit_number
    n = instance.index
    ext = Path(filename).suffix.lower()
    base = f"{dni}_{tipo}_{v}_{n}{ext}"
    return f"photos/{dni}/{base}"

class Photo(models.Model):
    TYPE_CONJ = "CONJ"
    TYPE_LAB = "LAB"
    TYPE_INDICE = "IND"
    TYPE_CHOICES = [
        (TYPE_CONJ, "Conjuntiva"),
        (TYPE_LAB, "Labio"),
        (TYPE_INDICE, "Índice"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="photos")
    type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    index = models.PositiveSmallIntegerField(default=1) # NmrFoto

    file = models.FileField(upload_to=photo_upload_to)
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(default=0)

    # Deduplicación / HEAD por hash
    sha256 = models.CharField(max_length=64, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("visit", "type", "index")]

    def __str__(self):
        label = dict(self.TYPE_CHOICES).get(self.type, self.type)
        return f"{self.visit.patient.dni}-{label}-{self.visit.visit_number}-{self.index}"
