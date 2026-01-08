# records/signals.py
from django.db import transaction
from django.db.models import Max
import hashlib
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Visit, Photo

@receiver(pre_save, sender=Visit)
def assign_visit_number(sender, instance: Visit, **kwargs):
    if instance._state.adding and not instance.visit_number:
        pid = getattr(instance, "patient_id", None)  # linter OK
        if not pid:
            instance.visit_number = 1
            return
        with transaction.atomic():
            last_num = (
                Visit.objects.select_for_update()
                .filter(patient__id=pid)    
                .aggregate(m=Max("visit_number"))
            )["m"] or 0
            instance.visit_number = last_num + 1
            
@receiver(pre_save, sender=Photo)
def fill_photo_metadata(sender, instance: Photo, **kwargs):
    if instance.file and not instance.sha256:
    # Calcula sha256 del archivo subido (streaming)
        hasher = hashlib.sha256()
        for chunk in instance.file.chunks():
            hasher.update(chunk)
        instance.sha256 = hasher.hexdigest()
    if instance.file and not instance.size:
        try:
            instance.size = instance.file.size
        except Exception:
            pass