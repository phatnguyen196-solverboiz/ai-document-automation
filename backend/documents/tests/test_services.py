from datetime import date
from decimal import Decimal

import pytest

from documents.services.llm_service import LLMService
from documents.services.pdf_service import extract_pdf_text
from documents.services.validation_service import validate_extraction

from .conftest import make_pdf


def test_pdf_text_extraction() -> None:
    text = extract_pdf_text(make_pdf("Customer: ACME Logistics\nOrigin: Bangkok"))
    assert "ACME Logistics" in text
    assert "Origin: Bangkok" in text


def test_mock_llm_extraction() -> None:
    result = LLMService(mock=True).extract(
        "Customer: ABC Electronics\nContainer Number: TCLU1234567\nOrigin: Ho Chi Minh City\n"
        "Destination: Singapore\nWeight: 1,000 lbs\nDelivery Date: 25/09/2026"
    )
    assert result["customer"] == "ABC Electronics"
    assert result["weight_kg"] == Decimal("453.59")
    assert result["delivery_date"] == "2026-09-25"


def test_valid_structured_extraction() -> None:
    valid, normalized, errors = validate_extraction({
        "customer": "ABC Electronics",
        "container_number": "tclu1234567",
        "origin": "Ho Chi Minh City",
        "destination": "Singapore",
        "weight_kg": "840",
        "delivery_date": "2026-09-25",
    })
    assert valid is True
    assert errors == {}
    assert normalized["container_number"] == "TCLU1234567"
    assert normalized["delivery_date"] == date(2026, 9, 25)


@pytest.mark.parametrize(
    ("field", "value"),
    [("customer", None), ("container_number", None), ("destination", None)],
)
def test_missing_fields_require_review(field: str, value) -> None:
    payload = {
        "customer": "ABC Electronics", "container_number": "TCLU1234567",
        "origin": "Bangkok", "destination": "Singapore", "weight_kg": 840,
        "delivery_date": "2026-09-25",
    }
    payload[field] = value
    valid, _normalized, errors = validate_extraction(payload)
    assert valid is False
    assert field in errors


def test_invalid_weight() -> None:
    valid, _normalized, errors = validate_extraction({
        "customer": "ABC", "container_number": "TCLU1234567", "origin": "A",
        "destination": "B", "weight_kg": -4, "delivery_date": "2026-09-25",
    })
    assert not valid
    assert "weight_kg" in errors


def test_invalid_date() -> None:
    valid, _normalized, errors = validate_extraction({
        "customer": "ABC", "container_number": "TCLU1234567", "origin": "A",
        "destination": "B", "weight_kg": 4, "delivery_date": "not-a-date",
    })
    assert not valid
    assert "delivery_date" in errors


def test_origin_and_destination_must_differ() -> None:
    valid, _normalized, errors = validate_extraction({
        "customer": "ABC", "container_number": "TCLU1234567", "origin": "Singapore",
        "destination": "singapore", "weight_kg": 4, "delivery_date": "2026-09-25",
    })
    assert not valid
    assert "form" in errors or "destination" in errors
