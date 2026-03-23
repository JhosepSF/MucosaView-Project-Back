from __future__ import annotations

from io import BytesIO
import logging

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

from .models import Photo

logger = logging.getLogger("records")

THUMBNAIL_MAX_SIZE = (420, 420)
THUMBNAIL_FORMAT = "WEBP"
THUMBNAIL_QUALITY = 80


def ensure_photo_thumbnail(photo: Photo, force: bool = False) -> bool:
    if not photo.file:
        return False

    if not force and photo.thumbnail and photo.thumbnail.storage.exists(photo.thumbnail.name):
        return False

    try:
        with photo.file.open("rb") as source_stream:
            image = Image.open(source_stream)
            image = ImageOps.exif_transpose(image)
            if image.mode != "RGB":
                image = image.convert("RGB")
            image.thumbnail(THUMBNAIL_MAX_SIZE)

            output = BytesIO()
            image.save(output, format=THUMBNAIL_FORMAT, quality=THUMBNAIL_QUALITY, optimize=True)
    except (FileNotFoundError, UnidentifiedImageError, OSError) as exc:
        logger.warning("No se pudo generar thumbnail para photo_id=%s: %s", photo.pk, exc)
        return False

    thumbnail_name = photo._meta.get_field("thumbnail").generate_filename(photo, photo.file.name)
    photo.thumbnail.save(thumbnail_name, ContentFile(output.getvalue()), save=False)
    Photo.objects.filter(pk=photo.pk).update(thumbnail=photo.thumbnail.name)
    return True