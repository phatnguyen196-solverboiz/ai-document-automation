import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from automation.exceptions import PortalUnavailableError
from documents.models import Document, ExtractedShipmentData, ProcessingJob
from documents.services.automation_service import AutomationService


def extraction_defaults(document: Document, **overrides) -> ExtractedShipmentData:
    values = {
        "customer": "ABC Electronics",
        "container_number": "TCLU1234567",
        "origin": "Ho Chi Minh City",
        "destination": "Singapore",
        "weight_kg": 840,
        "delivery_date": "2026-09-25",
        "confidence": "0.9700",
        "is_valid": True,
    }
    values.update(overrides)
    return ExtractedShipmentData.objects.create(document=document, **values)


@pytest.mark.django_db
def test_pdf_upload(api_client, valid_pdf, settings, tmp_path) -> None:
    settings.MEDIA_ROOT = tmp_path
    response = api_client.post(reverse("document-list"), {"file": valid_pdf}, format="multipart")
    assert response.status_code == 201
    assert response.data["status"] == Document.Status.UPLOADED
    assert response.data["original_filename"] == "shipment.pdf"


@pytest.mark.django_db
def test_invalid_file_rejection(api_client) -> None:
    upload = SimpleUploadedFile("notes.txt", b"not a pdf", content_type="text/plain")
    response = api_client.post(reverse("document-list"), {"file": upload}, format="multipart")
    assert response.status_code == 400
    assert "Only PDF" in str(response.data)


@pytest.mark.django_db
def test_fake_pdf_rejection(api_client) -> None:
    upload = SimpleUploadedFile("fake.pdf", b"not actually a pdf", content_type="application/pdf")
    response = api_client.post(reverse("document-list"), {"file": upload}, format="multipart")
    assert response.status_code == 400
    assert "not a valid PDF" in str(response.data)


@pytest.mark.django_db
def test_extract_endpoint_uses_mock_llm(api_client, valid_pdf, settings, tmp_path) -> None:
    settings.MEDIA_ROOT = tmp_path
    upload = api_client.post(reverse("document-list"), {"file": valid_pdf}, format="multipart")
    response = api_client.post(reverse("document-extract", args=[upload.data["id"]]))
    document = Document.objects.get(pk=upload.data["id"])
    assert response.status_code == 200
    assert response.data["status"] == ProcessingJob.Status.SUCCESS
    assert document.status == Document.Status.REVIEW_REQUIRED
    assert document.extraction.customer == "ABC Electronics"
    assert document.extraction.is_valid is True


@pytest.mark.django_db
def test_human_editing_revalidates_extraction(api_client, valid_pdf, settings, tmp_path) -> None:
    settings.MEDIA_ROOT = tmp_path
    document = Document.objects.create(original_filename="shipment.pdf", file=valid_pdf, status=Document.Status.REVIEW_REQUIRED)
    extraction_defaults(document, destination="", is_valid=False)
    response = api_client.patch(
        reverse("document-extraction", args=[document.pk]),
        {"destination": "Singapore"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["is_valid"] is True
    assert response.data["validation_errors"] == {}


@pytest.mark.django_db
def test_approval_workflow(api_client, valid_pdf, settings, tmp_path) -> None:
    settings.MEDIA_ROOT = tmp_path
    document = Document.objects.create(original_filename="shipment.pdf", file=valid_pdf, status=Document.Status.REVIEW_REQUIRED)
    extraction_defaults(document)
    response = api_client.post(reverse("document-approve", args=[document.pk]))
    document.refresh_from_db()
    assert response.status_code == 200
    assert document.status == Document.Status.APPROVED


@pytest.mark.django_db
def test_approval_rejects_invalid_data(api_client, valid_pdf, settings, tmp_path) -> None:
    settings.MEDIA_ROOT = tmp_path
    document = Document.objects.create(original_filename="shipment.pdf", file=valid_pdf, status=Document.Status.REVIEW_REQUIRED)
    extraction_defaults(document, weight_kg=-2, is_valid=False)
    response = api_client.post(reverse("document-approve", args=[document.pk]))
    assert response.status_code == 400
    assert "weight_kg" in response.data["errors"]


@pytest.mark.django_db
def test_automation_blocked_before_approval(api_client, valid_pdf, settings, tmp_path) -> None:
    settings.MEDIA_ROOT = tmp_path
    document = Document.objects.create(original_filename="shipment.pdf", file=valid_pdf, status=Document.Status.REVIEW_REQUIRED)
    extraction_defaults(document)
    response = api_client.post(reverse("document-automate", args=[document.pk]))
    assert response.status_code == 409
    assert not ProcessingJob.objects.filter(job_type=ProcessingJob.JobType.AUTOMATION).exists()


@pytest.mark.django_db
def test_successful_automation(api_client, valid_pdf, settings, tmp_path, monkeypatch) -> None:
    class FakePortal:
        def create_order(self, extraction) -> str:
            return "SO-2026-00042"

    settings.MEDIA_ROOT = tmp_path
    document = Document.objects.create(original_filename="shipment.pdf", file=valid_pdf, status=Document.Status.APPROVED)
    extraction_defaults(document)
    monkeypatch.setattr("documents.views.AutomationService", lambda: AutomationService(portal_client=FakePortal()))
    response = api_client.post(reverse("document-automate", args=[document.pk]))
    document.refresh_from_db()
    assert response.status_code == 200
    assert response.data["status"] == ProcessingJob.Status.SUCCESS
    assert document.status == Document.Status.AUTOMATED
    assert document.erp_reference == "SO-2026-00042"


@pytest.mark.django_db
def test_failed_automation(api_client, valid_pdf, settings, tmp_path, monkeypatch) -> None:
    class FailedPortal:
        def create_order(self, extraction) -> str:
            raise PortalUnavailableError("portal offline")

    settings.MEDIA_ROOT = tmp_path
    document = Document.objects.create(original_filename="shipment.pdf", file=valid_pdf, status=Document.Status.APPROVED)
    extraction_defaults(document)
    monkeypatch.setattr("documents.views.AutomationService", lambda: AutomationService(portal_client=FailedPortal()))
    response = api_client.post(reverse("document-automate", args=[document.pk]))
    document.refresh_from_db()
    assert response.status_code == 502
    assert response.data["status"] == ProcessingJob.Status.FAILED
    assert document.status == Document.Status.FAILED


@pytest.mark.django_db
def test_document_and_job_endpoints(api_client, valid_pdf, settings, tmp_path) -> None:
    settings.MEDIA_ROOT = tmp_path
    document = Document.objects.create(original_filename="shipment.pdf", file=valid_pdf)
    job = ProcessingJob.objects.create(document=document, job_type=ProcessingJob.JobType.EXTRACTION)
    listing = api_client.get(reverse("document-list"))
    detail = api_client.get(reverse("document-detail", args=[document.pk]))
    job_response = api_client.get(reverse("job-detail", args=[job.pk]))
    assert listing.status_code == detail.status_code == job_response.status_code == 200
    assert detail.data["original_filename"] == "shipment.pdf"
    assert job_response.data["job_type"] == ProcessingJob.JobType.EXTRACTION
