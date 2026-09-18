import logging

from django.db import transaction
from django.utils import timezone

from automation.portal_client import PortalClient
from documents.models import Document, ProcessingJob

logger = logging.getLogger(__name__)


class AutomationService:
    def __init__(self, portal_client: PortalClient | None = None) -> None:
        self.portal_client = portal_client or PortalClient()

    def automate(self, document: Document) -> ProcessingJob:
        job = ProcessingJob.objects.create(document=document, job_type=ProcessingJob.JobType.AUTOMATION)
        job.status = ProcessingJob.Status.RUNNING
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at"])
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
            document.status = Document.Status.FAILED
            document.save(update_fields=["status", "updated_at"])
            job.status = ProcessingJob.Status.FAILED
            job.error_message = str(exc)
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "error_message", "finished_at"])
        return job
