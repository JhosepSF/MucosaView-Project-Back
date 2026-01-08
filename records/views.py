from django.db import transaction
import logging
from typing import Optional, cast
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import APIException
from rest_framework.decorators import api_view, permission_classes as drf_permission_classes, parser_classes
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from .models import Patient, Visit, Photo
from .serializers import PatientSerializer, VisitSerializer, PhotoSerializer

logger = logging.getLogger("records") 

class Conflict(APIException):
    status_code = status.HTTP_412_PRECONDITION_FAILED
    default_detail = "ETag does not match current resource version."


class IdempotentUpsertMixin:
    """PUT /resource/{uuid}/ crea o actualiza. Para POST se mantiene el comportamiento normal."""
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        try:
            instance = self.get_object()  # type: ignore[attr-defined]
        except Exception:
            instance = None

        if instance is None:
            serializer = self.get_serializer(  # type: ignore[attr-defined]
                data={**request.data, "id": kwargs.get(getattr(self, "lookup_field", "pk"))}
            )
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)  # type: ignore[attr-defined]
            headers = self.get_success_headers(serializer.data)  # type: ignore[attr-defined]
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        # Evita warning de Pylance llamando al base class directamente
        return viewsets.ModelViewSet.update(self, request, *args, partial=partial, **kwargs)  # type: ignore[misc]


class PatientViewSet(IdempotentUpsertMixin, viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by("-created_at")
    serializer_class = PatientSerializer
    lookup_field = "pk"
    permission_classes = [AllowAny]


class VisitViewSet(IdempotentUpsertMixin, viewsets.ModelViewSet):
    queryset = Visit.objects.select_related("patient").all().order_by("-created_at")
    serializer_class = VisitSerializer
    lookup_field = "pk"
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        response = viewsets.ModelViewSet.retrieve(self, request, *args, **kwargs)
        obj: Visit = self.get_object()
        response["ETag"] = f'"v{obj.version}"'
        return response

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception:
            obj = None

        if obj is None:
            return viewsets.ModelViewSet.update(self, request, *args, **kwargs)

        etag = request.headers.get("If-Match")
        current = f'"v{obj.version}"'
        if etag and etag != current:
            raise Conflict()

        response = viewsets.ModelViewSet.update(self, request, *args, **kwargs)
        obj.refresh_from_db()
        obj.version += 1
        obj.save(update_fields=["version"])
        response["ETag"] = f'"v{obj.version}"'
        return response


class PhotoViewSet(IdempotentUpsertMixin, viewsets.ModelViewSet):
    queryset = Photo.objects.select_related("visit", "visit__patient").all().order_by("created_at")
    serializer_class = PhotoSerializer
    lookup_field = "pk"
    permission_classes = [AllowAny]


# === FBV fuera de la clase ===
@api_view(["HEAD"])  # HEAD por hash (deduplicación)
@drf_permission_classes([AllowAny])
def media_by_hash(request, sha256: str):
    exists = Photo.objects.filter(sha256=sha256).exists()
    return Response(status=status.HTTP_200_OK if exists else status.HTTP_404_NOT_FOUND)

@api_view(["POST"])
@drf_permission_classes([AllowAny])
@transaction.atomic
def mucosa_registro(request):
    data = request.data.get("body", request.data)
    logger.info("POST /api/mucosa/registro recibido (keys=%s)", list(data.keys()))

    dp = data.get("datos_personales") or {}
    dobs = data.get("datos_obstetricos") or {}

    patient_id = data.get("client_uuid")

    def _omit_blanks(d: dict) -> dict:
        return {k: v for k, v in d.items() if v is not None and (not isinstance(v, str) or v.strip() != "")}

    raw_patient_payload = {
        "id": patient_id,
        "dni": str(dp.get("dni", "")).strip(),
        "nombre": (dp.get("nombre") or "").strip(),
        "apellido": (dp.get("apellido") or "").strip(),
        "edad": int(dp["edad"]) if dp.get("edad") not in (None, "") else None,
        "region": (dp.get("region") or "").strip(),
        "provincia": (dp.get("provincia") or "").strip(),
        "distrito": (dp.get("distrito") or "").strip(),
        "direccion": (dp.get("direccion") or "").strip(),
        "maps_url": dp.get("mapsUrl"),
    }
    patient_payload = _omit_blanks(raw_patient_payload)

    # ===== Upsert por ID y si no, por DNI =====
    instance = None
    existed = False
    try:
        instance = Patient.objects.get(pk=patient_id)
        existed = True
        logger.info("Upsert por ID: existe patient_id=%s", patient_id)
        ps = PatientSerializer(instance, data=patient_payload, partial=True)
    except Patient.DoesNotExist:
        dni_val = patient_payload.get("dni")
        if dni_val:
            instance = Patient.objects.filter(dni=dni_val).first()
        if instance:
            existed = True
            logger.info("Upsert por DNI: reusando paciente con dni=%s", dni_val)
            ps = PatientSerializer(instance, data=patient_payload, partial=True)
        else:
            logger.info("Creando paciente nuevo con id=%s dni=%s", patient_id, patient_payload.get("dni"))
            ps = PatientSerializer(data=patient_payload)

    if not ps.is_valid():
        logger.warning("Patient validation errors: %s", ps.errors)
        return Response(ps.errors, status=status.HTTP_400_BAD_REQUEST)

    patient: Patient = cast(Patient, ps.save())
    logger.info("Paciente %s: id=%s dni=%s", "ACTUALIZADO" if existed else "CREADO", patient.id, patient.dni)

    # ===== Crear visita =====
    bpm_val = dobs.get("pulsaciones")
    hb_val = dobs.get("hemoglobina")
    spo2_val = dobs.get("oxigeno")
    visit_payload = _omit_blanks({
        "patient": str(patient.id),
        "bpm": int(bpm_val) if bpm_val not in (None, "") else None,
        "hemoglobina": float(hb_val) if hb_val not in (None, "") else None,
        "spo2": int(spo2_val) if spo2_val not in (None, "") else None,
        "lmp_date": dobs.get("fechaUltimoPeriodo"),
    })

    vs = VisitSerializer(data=visit_payload)
    if not vs.is_valid():
        logger.warning("Visit validation errors: %s", vs.errors)
        return Response(vs.errors, status=status.HTTP_400_BAD_REQUEST)

    visit: Visit = cast(Visit, vs.save())
    logger.info("Visita CREADA: id=%s visit_number=%s gest_weeks=%s",
                visit.id, visit.visit_number, visit.gestational_weeks)

    return Response(
        {
            "patient_id": str(patient.id),
            "visit_id": str(visit.id),
            "visit_number": visit.visit_number,
            "gestational_weeks": visit.gestational_weeks,
        },
        status=status.HTTP_201_CREATED,
    )

@api_view(["POST"])
@drf_permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def mucosa_fotos(request, dni: str):
    """
    Espera form-data:
      - file: imagen (obligatorio)
      - type: CONJ | LAB (obligatorio)
      - index: int (opcional, default 1)
      - original_name, content_type: opcional
    """
    # Tipado explícito para Pylance
    patient: Patient = cast(Patient, get_object_or_404(Patient, dni=str(dni).strip()))

    # Evita usar patient.visits si el linter molesta; ve directo por el modelo Visit
    visit: Optional[Visit] = (
        Visit.objects.filter(patient=patient)
        .order_by("-created_at")
        .first()
    )
    if visit is None:
        return Response(
            {"detail": "El paciente no tiene visitas para adjuntar fotos."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    uploaded = request.FILES.get("file")
    if not uploaded:
        return Response({"file": ["Este campo es obligatorio."]},
                        status=status.HTTP_400_BAD_REQUEST)

    photo_type = request.data.get("type")
    if photo_type not in ("CONJ", "LAB"):
        return Response({"type": ["Debe ser 'CONJ' o 'LAB'."]},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        index_val = int(request.data.get("index") or 1)
        if index_val < 1:
            raise ValueError
    except ValueError:
        return Response({"index": ["Debe ser un entero >= 1."]},
                        status=status.HTTP_400_BAD_REQUEST)

    photo_payload = {
        "visit": str(visit.id),
        "type": photo_type,
        "index": index_val,
        "original_name": request.data.get("original_name") or getattr(uploaded, "name", ""),
        "content_type": request.data.get("content_type") or getattr(uploaded, "content_type", ""),
    }

    phs = PhotoSerializer(data={**photo_payload, "file": uploaded})
    if not phs.is_valid():
        return Response(phs.errors, status=status.HTTP_400_BAD_REQUEST)

    photo: Photo = cast(Photo, phs.save())  # <- cast para callar a Pylance

    return Response(
        {
            "photo_id": str(photo.id),
            "visit_id": str(visit.id),
            "stored_as": str(photo.file),  # ruta/nombre final
        },
        status=status.HTTP_201_CREATED,
    )

@api_view(["POST"])
@drf_permission_classes([AllowAny])
@transaction.atomic
def mucosa_visita(request, dni: str):
    """
    Crea una NUEVA visita para el paciente con el DNI dado.
    Body (JSON o dentro de "body"): 
      - datos_obstetricos: { fechaUltimoPeriodo, hemoglobina, oxigeno, pulsaciones }
      - opcional: nro_visita (solo informativo; el servidor asigna la secuencia real)
    Responde: visit_id, visit_number, gestational_weeks
    """
    data = request.data.get("body", request.data)
    dobs = data.get("datos_obstetricos") or {}

    patient = get_object_or_404(Patient, dni=str(dni).strip())

    # Construye payload de visita (el número se asigna en signal)
    def _coerce_int(x):
        return int(x) if x not in (None, "",) else None
    def _coerce_float(x):
        return float(x) if x not in (None, "",) else None

    visit_payload = {
        "patient": str(patient.id),
        "bpm": _coerce_int(dobs.get("pulsaciones")),
        "hemoglobina": _coerce_float(dobs.get("hemoglobina")),
        "spo2": _coerce_int(dobs.get("oxigeno")),
        "lmp_date": dobs.get("fechaUltimoPeriodo"),
    }

    vs = VisitSerializer(data=visit_payload)
    if not vs.is_valid():
        return Response(vs.errors, status=status.HTTP_400_BAD_REQUEST)

    visit: Visit = cast(Visit, vs.save())
    return Response(
        {
            "patient_id": str(patient.id),
            "visit_id": str(visit.id),
            "visit_number": visit.visit_number,          
            "gestational_weeks": visit.gestational_weeks
        },
        status=status.HTTP_201_CREATED,
    )