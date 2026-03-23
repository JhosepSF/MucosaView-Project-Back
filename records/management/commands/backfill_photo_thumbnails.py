from django.core.management.base import BaseCommand

from records.image_utils import ensure_photo_thumbnail
from records.models import Photo


class Command(BaseCommand):
    help = "Genera thumbnails para fotos ya existentes en el storage configurado."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Procesa como máximo N fotos.",
        )
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="Procesa solo fotos sin thumbnail registrado.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenera thumbnails aunque ya existan.",
        )

    def handle(self, *args, **options):
        queryset = Photo.objects.select_related("visit", "visit__patient").order_by("created_at")

        if options["only_missing"] and not options["force"]:
            queryset = queryset.filter(thumbnail="")

        limit = options["limit"]
        if limit:
            queryset = queryset[:limit]

        total = queryset.count() if limit is None else len(queryset)
        generated = 0
        skipped = 0

        self.stdout.write(self.style.NOTICE(f"Procesando {total} fotos..."))

        for photo in queryset:
            created = ensure_photo_thumbnail(photo, force=options["force"])
            if created:
                generated += 1
                self.stdout.write(f"[OK] {photo.pk} -> {photo.thumbnail.name}")
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Miniaturas generadas: {generated}. Omitidas: {skipped}."
            )
        )