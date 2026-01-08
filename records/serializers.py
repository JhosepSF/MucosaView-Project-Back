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
    class Meta:
        model = Photo
        fields = [
            "id","visit","type","index","file","original_name",
            "content_type","size","sha256","created_at",
        ]
        read_only_fields = ["size","sha256","created_at"]