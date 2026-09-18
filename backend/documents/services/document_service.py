import logging

from django.db import transaction
from django.utils import timezone

from documents.models import Document, ExtractedShipmentData, ProcessingJob

from .llm_service import LLMService
from .pdf_service import extract_pdf_text
from .validation_service import sanitize_for_storage, validate_extraction

logger = logging.getLogger(__name__)


class DocumentWorkflowService:
    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm_service = llm_service or LLMService()

    def extract(self, document: Document) -> ProcessingJob:
        job = ProcessingJob.objects.create(document=document, job_type=ProcessingJob.JobType.EXTRACTION)
        job.status = ProcessingJob.Status.RUNNING
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at"])
        document.status = Document.Status.PROCESSING
        document.save(update_fields=["status", "updated_at"])

        try:
            raw_text = extract_pdf_text(document.file)
            llm_data = self.llm_service.extract(raw_text)
            is_valid, normalized, _errors = validate_extraction(llm_data)
            storage = normalized if is_valid else sanitize_for_storage(llm_data)
            with transaction.atomic():
                document.raw_text = raw_text
                document.status = Document.Status.REVIEW_REQUIRED
                document.save(update_fields=["raw_text", "status", "updated_at"])
                ExtractedShipmentData.objects.update_or_create(
                    document=document,
                    defaults={**storage, "confidence": llm_data.get("confidence"), "is_valid": is_valid},
                )
                job.status = ProcessingJob.Status.SUCCESS
                job.finished_at = timezone.now()
                job.error_message = ""
                job.save(update_fields=["status", "finished_at", "error_message"])
            logger.info("Document extraction completed document=%s valid=%s", document.pk, is_valid)
        except Exception as exc:
            logger.exception("Document extraction failed document=%s", document.pk)
            document.status = Document.Status.FAILED
            document.save(update_fields=["status", "updated_at"])
            job.status = ProcessingJob.Status.FAILED
            job.finished_at = timezone.now()
            job.error_message = str(exc)
            job.save(update_fields=["status", "finished_at", "error_message"])
        return job
