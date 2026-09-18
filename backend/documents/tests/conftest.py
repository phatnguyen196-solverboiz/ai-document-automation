import fitz
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def make_pdf(text: str, name: str = "shipment.pdf") -> SimpleUploadedFile:
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text, fontsize=11)
    payload = pdf.tobytes()
    pdf.close()
    return SimpleUploadedFile(name, payload, content_type="application/pdf")


@pytest.fixture
def valid_pdf() -> SimpleUploadedFile:
    return make_pdf(
        "Customer: ABC Electronics\n"
        "Container Number: TCLU1234567\n"
        "Origin: Ho Chi Minh City\n"
        "Destination: Singapore\n"
        "Weight: 840 kg\n"
        "Delivery Date: 2026-09-25"
    )
