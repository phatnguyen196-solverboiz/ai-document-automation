from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Document, ProcessingJob
from .serializers import DocumentSerializer, DocumentUploadSerializer, ExtractionSerializer, ProcessingJobSerializer
from .services.automation_service import AutomationService
from .services.document_service import DocumentWorkflowService
from .services.validation_service import validate_extraction


class DocumentViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Document.objects.all()

    def get_serializer_class(self):
        return DocumentUploadSerializer if self.action == "create" else DocumentSerializer

    @action(detail=True, methods=["post"])
    def extract(self, request, pk=None):
        job = DocumentWorkflowService().extract(self.get_object())
        code = status.HTTP_200_OK if job.status == ProcessingJob.Status.SUCCESS else status.HTTP_422_UNPROCESSABLE_ENTITY
        return Response(ProcessingJobSerializer(job).data, status=code)

    @action(detail=True, methods=["get", "patch"], url_path="extraction")
    def extraction(self, request, pk=None):
        document = self.get_object()
        if not hasattr(document, "extraction"):
            return Response({"detail": "Extraction is not available yet."}, status=status.HTTP_404_NOT_FOUND)
        extraction = document.extraction
        if request.method == "GET":
            return Response(ExtractionSerializer(extraction).data)

        serializer = ExtractionSerializer(extraction, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        extraction = serializer.save()
        candidate = {
            "customer": extraction.customer,
            "container_number": extraction.container_number,
            "origin": extraction.origin,
            "destination": extraction.destination,
            "weight_kg": extraction.weight_kg,
            "delivery_date": extraction.delivery_date,
        }
        is_valid, _normalized, errors = validate_extraction(candidate)
        extraction.is_valid = is_valid
        extraction.save(update_fields=["is_valid", "updated_at"])
        document.status = Document.Status.REVIEW_REQUIRED
        document.save(update_fields=["status", "updated_at"])
        response = ExtractionSerializer(extraction).data
        response["validation_errors"] = errors
        return Response(response)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        document = self.get_object()
        if not hasattr(document, "extraction"):
            return Response({"detail": "Run extraction before approval."}, status=status.HTTP_409_CONFLICT)
        extraction = document.extraction
        is_valid, _normalized, errors = validate_extraction({
            "customer": extraction.customer,
            "container_number": extraction.container_number,
            "origin": extraction.origin,
            "destination": extraction.destination,
            "weight_kg": extraction.weight_kg,
            "delivery_date": extraction.delivery_date,
        })
        extraction.is_valid = is_valid
        extraction.save(update_fields=["is_valid", "updated_at"])
        if not is_valid:
            return Response({"detail": "Fix validation errors before approval.", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        document.status = Document.Status.APPROVED
        document.save(update_fields=["status", "updated_at"])
        return Response(DocumentSerializer(document, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def automate(self, request, pk=None):
        document = self.get_object()
        if document.status != Document.Status.APPROVED:
            return Response({"detail": "Human approval is required before automation."}, status=status.HTTP_409_CONFLICT)
        job = AutomationService().automate(document)
        code = status.HTTP_200_OK if job.status == ProcessingJob.Status.SUCCESS else status.HTTP_502_BAD_GATEWAY
        return Response(ProcessingJobSerializer(job).data, status=code)


class ProcessingJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProcessingJob.objects.select_related("document").all()
    serializer_class = ProcessingJobSerializer
    http_method_names = ["get", "head", "options"]
