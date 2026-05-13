import os
import csv
import shutil
import zipfile
from pathlib import Path
from io import StringIO
from django.core.management.base import BaseCommand
from django.conf import settings
from records.models import Patient, Visit, Photo


class Command(BaseCommand):
    help = 'Exporta un dataset anonimizado con fotos y datos obstétricos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='anonymized_dataset',
            help='Nombre de la carpeta de salida (sin extensión .zip)',
        )
        parser.add_argument(
            '--include-photos',
            action='store_true',
            help='Incluir fotos en el dataset',
        )

    def handle(self, *args, **options):
        output_name = options['output']
        include_photos = options['include_photos']
        
        # Crear directorio temporal
        base_dir = Path(settings.BASE_DIR)
        temp_dir = base_dir / f"temp_{output_name}"
        output_dir = temp_dir / output_name
        photos_dir = output_dir / "photos"
        
        # Limpiar y crear directorios
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if include_photos:
            photos_dir.mkdir(parents=True, exist_ok=True)

        # Crear mapeo de anonimización
        patients = Patient.objects.all()
        anonymization_map = {}
        reverse_map = {}  # Para referencia
        
        for idx, patient in enumerate(patients, 1):
            anon_id = f"PAT_{idx:04d}"
            anonymization_map[patient.id] = anon_id
            reverse_map[anon_id] = {
                'original_dni': patient.dni,
                'original_name': f"{patient.nombre} {patient.apellido}"
            }

        # Crear CSV
        csv_path = output_dir / "patients_data.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'patient_id',
                'edad',
                'hemoglobina_gdl',
                'spo2_percent',
                'bpm',
                'gestational_weeks',
                'visit_number',
                'visit_date',
                'photo_types',
                'photo_count'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Obtener todas las visitas
            visits = Visit.objects.select_related('patient').prefetch_related('photos')
            
            for visit in visits:
                patient_id = visit.patient.id
                anon_patient_id = anonymization_map[patient_id]
                
                # Datos del paciente
                age = visit.patient.edad
                hemoglobina = visit.hemoglobina or ''
                spo2 = visit.spo2 or ''
                bpm = visit.bpm or ''
                gestational_weeks = visit.gestational_weeks or ''
                
                # Fotos asociadas
                photos = visit.photos.all()  # type: ignore[attr-defined]
                photo_types = ','.join([photo.get_type_display() for photo in photos])
                photo_count = photos.count()
                
                writer.writerow({
                    'patient_id': anon_patient_id,
                    'edad': age,
                    'hemoglobina_gdl': hemoglobina,
                    'spo2_percent': spo2,
                    'bpm': bpm,
                    'gestational_weeks': gestational_weeks,
                    'visit_number': visit.visit_number,
                    'visit_date': visit.created_at.date(),
                    'photo_types': photo_types,
                    'photo_count': photo_count,
                })

                # Copiar fotos si está habilitado
                if include_photos:
                    for photo in photos:
                        source_path = base_dir / photo.file.name
                        if source_path.exists():
                            # Crear estructura: photos/PAT_0001/Conjuntiva_1.jpg
                            patient_photos_dir = photos_dir / anon_patient_id
                            patient_photos_dir.mkdir(exist_ok=True)
                            
                            photo_type_name = photo.get_type_display()
                            ext = Path(source_path).suffix
                            dest_filename = f"{photo_type_name}_{photo.index}{ext}"
                            dest_path = patient_photos_dir / dest_filename
                            
                            shutil.copy2(source_path, dest_path)
                            self.stdout.write(f"  ✓ Copiada foto: {dest_filename}")

        # Crear archivo de mapeo de referencia (para auditoría, sin DNI real)
        mapping_path = output_dir / "MAPPING_REFERENCE.txt"
        with open(mapping_path, 'w', encoding='utf-8') as f:
            f.write("MAPEO DE ANONIMIZACIÓN (SOLO PARA AUDITORÍA - NO INCLUIR EN PUBLICACIÓN)\n")
            f.write("=" * 70 + "\n\n")
            for anon_id in sorted(reverse_map.keys()):
                info = reverse_map[anon_id]
                f.write(f"{anon_id}: {info['original_name']}\n")

        # Crear ZIP
        zip_path = base_dir / f"{output_name}.zip"
        if zip_path.exists():
            zip_path.unlink()
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in output_dir.rglob('*'):
                if file.is_file():
                    arcname = file.relative_to(temp_dir)
                    zipf.write(file, arcname)
        
        # Limpiar directorio temporal
        shutil.rmtree(temp_dir)
        
        # Información final
        self.stdout.write(self.style.SUCCESS('\n✓ Dataset anonimizado creado exitosamente'))
        self.stdout.write(f"📦 Archivo: {zip_path}")
        self.stdout.write(f"📊 Registros: {visits.count()} visitas")
        self.stdout.write(f"👥 Pacientes: {len(anonymization_map)}")
        if include_photos:
            total_photos = Photo.objects.count()
            self.stdout.write(f"📸 Fotos incluidas: {total_photos}")
        self.stdout.write(f"\n💾 Tamaño: {zip_path.stat().st_size / (1024*1024):.2f} MB")
        self.stdout.write(f"\n⚠️  IMPORTANTE: El archivo MAPPING_REFERENCE.txt contiene identificadores")
        self.stdout.write(f"   reales. ¡NO incluirlo en publicaciones! Almacenarlo de forma segura.")
