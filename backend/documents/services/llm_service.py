import json
import os
import re
from datetime import datetime
from decimal import Decimal
from typing import Any

import requests

from .exceptions import LLMServiceError, StructuredOutputError


REQUIRED_FIELDS = ["customer", "container_number", "origin", "destination", "weight_kg", "delivery_date"]


class LLMService:
    def __init__(self, mock: bool | None = None) -> None:
        self.mock = (os.getenv("MOCK_LLM", "true").lower() == "true") if mock is None else mock
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("LLM_MODEL", "gpt-4.1-mini")
        self.api_key = os.getenv("LLM_API_KEY", "")

    def build_prompt(self, document_text: str) -> str:
        return f"""You extract shipment information from business documents.
Return valid JSON only with exactly these fields: customer, container_number, origin, destination, weight_kg, delivery_date.
Never invent missing information. Return null when unavailable. Convert weight to kilograms. Convert dates to YYYY-MM-DD. Do not add commentary.

DOCUMENT:
{document_text}"""

    def extract(self, document_text: str) -> dict[str, Any]:
        if self.mock:
            return self._mock_extract(document_text)
        if not self.api_key:
            raise LLMServiceError("LLM_API_KEY is required when MOCK_LLM=false")
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": self.build_prompt(document_text)}],
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                },
                timeout=45,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            result = json.loads(content)
        except (requests.RequestException, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise LLMServiceError("LLM request or response parsing failed") from exc
        if not isinstance(result, dict):
            raise StructuredOutputError("LLM output must be a JSON object")
        return {field: result.get(field) for field in REQUIRED_FIELDS} | {"confidence": result.get("confidence")}

    def _mock_extract(self, text: str) -> dict[str, Any]:
        def value(label: str) -> str | None:
            match = re.search(rf"^{re.escape(label)}\s*:\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE)
            if not match:
                return None
            found = match.group(1).strip()
            return None if found.lower() in {"n/a", "none", "missing", "-"} else found

        raw_weight = value("Weight")
        weight: Decimal | None = None
        if raw_weight:
            number_match = re.search(r"-?[\d,.]+", raw_weight)
            if number_match:
                weight = Decimal(number_match.group(0).replace(",", ""))
                if re.search(r"\b(lb|lbs|pounds?)\b", raw_weight, re.IGNORECASE):
                    weight = (weight * Decimal("0.45359237")).quantize(Decimal("0.01"))

        raw_date = value("Delivery Date")
        parsed_date = None
        if raw_date:
            for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d %B %Y", "%b %d, %Y"):
                try:
                    parsed_date = datetime.strptime(raw_date, pattern).date().isoformat()
                    break
                except ValueError:
                    continue

        return {
            "customer": value("Customer"),
            "container_number": value("Container Number"),
            "origin": value("Origin"),
            "destination": value("Destination"),
            "weight_kg": weight,
            "delivery_date": parsed_date,
            "confidence": Decimal("0.9700"),
        }
