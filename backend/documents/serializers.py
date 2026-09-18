from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from .models import Document, ExtractedShipmentData, ProcessingJob


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "file", "original_filename", "status", "created_at"]
        read_only_fields = ["id", "original_filename", "status", "created_at"]

    def validate_file(self, value):
        allowed_content_types = {"", "application/pdf", "application/x-pdf", "application/octet-stream"}
        if Path(value.name).suffix.lower() != ".pdf" or (value.content_type or "") not in allowed_content_types:
            raise serializers.ValidationError("Only PDF files are accepted.")
        if value.size > settings.MAX_PDF_SIZE_BYTES:
            raise serializers.ValidationError("PDF must be 10 MB or smaller.")
        position = value.tell()
        header = value.read(5)
        value.seek(position)
        if header != b"%PDF-":
            raise serializers.ValidationError("The uploaded file is not a valid PDF.")
        return value

    def create(self, validated_data):
        uploaded = validated_data["file"]
        return Document.objects.create(original_filename=uploaded.name, **validated_data)


class DocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "original_filename", "file", "file_url", "raw_text", "status", "erp_reference", "created_at", "updated_at"]
        read_only_fields = fields

    def get_file_url(self, obj: Document) -> str:
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request and obj.file else ""


class ExtractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedShipmentData
        fields = [
            "id", "document", "customer", "container_number", "origin", "destination",
            "weight_kg", "delivery_date", "confidence", "is_valid", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "document", "confidence", "is_valid", "created_at", "updated_at"]
        extra_kwargs = {
            "customer": {"allow_blank": True, "required": False},
            "container_number": {"allow_blank": True, "required": False},
            "origin": {"allow_blank": True, "required": False},
            "destination": {"allow_blank": True, "required": False},
            "weight_kg": {"allow_null": True, "required": False},
            "delivery_date": {"allow_null": True, "required": False},
        }


class ProcessingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingJob
        fields = ["id", "document", "job_type", "status", "error_message", "created_at", "started_at", "finished_at"]
        read_only_fields = fields
