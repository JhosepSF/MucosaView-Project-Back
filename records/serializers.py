from rest_framework import serializers
from .models import Patient, Visit, Photo

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "id","dni","nombre","apellido","edad",
            "region","provincia","distrito","direccion","maps_url",
            "created_at","updated_at",
        ]
        
class VisitSerializer(serializers.ModelSerializer):
    gestational_weeks = serializers.IntegerField(read_only=True)

    class Meta:
        model = Visit
        fields = [
            "id","patient","bpm","hemoglobina","spo2","lmp_date",
            "gestational_weeks","version","visit_number",
            "created_at","updated_at",
        ]
    read_only_fields = ["version","visit_number"]

class PhotoSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    has_thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = [
            "id","visit","type","index","file","original_name",
            "content_type","size","sha256","created_at",
            "thumbnail","file_url","thumbnail_url","has_thumbnail",
        ]
        read_only_fields = ["size","sha256","created_at","thumbnail","file_url","thumbnail_url","has_thumbnail"]

    def _build_absolute_url(self, field_file):
        if not field_file:
            return None

        try:
            url = field_file.url
        except Exception:
            return None

        request = self.context.get("request")
        if request is None:
            return url
        return request.build_absolute_uri(url)

    def get_file_url(self, obj):
        return self._build_absolute_url(obj.file)

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            thumbnail_url = self._build_absolute_url(obj.thumbnail)
            if thumbnail_url:
                return thumbnail_url
        return self.get_file_url(obj)

    def get_has_thumbnail(self, obj):
        return bool(obj.thumbnail)