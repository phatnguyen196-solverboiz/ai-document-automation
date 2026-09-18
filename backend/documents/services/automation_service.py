import logging

from django.db import transaction
from django.utils import timezone

from automation.portal_client import PortalClient
from documents.models import Document, ProcessingJob
from documents.services.exceptions import InvalidWorkflowState

logger = logging.getLogger(__name__)


class AutomationService:
    def __init__(self, portal_client: PortalClient | None = None) -> None:
        self.portal_client = portal_client or PortalClient()

    def automate(self, document: Document) -> ProcessingJob:
        with transaction.atomic():
            document = Document.objects.select_for_update().select_related("extraction").get(pk=document.pk)
            if document.status != Document.Status.APPROVED:
                raise InvalidWorkflowState("Human approval is required before automation.")
            if not hasattr(document, "extraction"):
                raise InvalidWorkflowState("Run extraction before automation.")
            document.status = Document.Status.PROCESSING
            document.save(update_fields=["status", "updated_at"])
            job = ProcessingJob.objects.create(
                document=document,
                job_type=ProcessingJob.JobType.AUTOMATION,
                status=ProcessingJob.Status.RUNNING,
                started_at=timezone.now(),
            )
        try:
            reference = self.portal_client.create_order(document.extraction)
            with transaction.atomic():
                document.erp_reference = reference
                document.status = Document.Status.AUTOMATED
                document.save(update_fields=["erp_reference", "status", "updated_at"])
                job.status = ProcessingJob.Status.SUCCESS
                job.finished_at = timezone.now()
                job.save(update_fields=["status", "finished_at"])
            logger.info("ERP automation succeeded document=%s reference=%s", document.pk, reference)
        except Exception as exc:
            logger.exception("ERP automation failed document=%s", document.pk)
            with transaction.atomic():
                document = Document.objects.select_for_update().get(pk=document.pk)
                document.status = Document.Status.APPROVED
                document.save(update_fields=["status", "updated_at"])
                job.status = ProcessingJob.Status.FAILED
                job.error_message = str(exc) or "ERP automation failed. Please retry."
                job.finished_at = timezone.now()
                job.save(update_fields=["status", "error_message", "finished_at"])
        return job
