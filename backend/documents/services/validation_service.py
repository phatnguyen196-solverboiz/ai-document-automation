from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


class ShipmentExtraction(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer: str = Field(min_length=1)
    container_number: str = Field(pattern=r"^[A-Z]{4}\d{7}$")
    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    weight_kg: Decimal = Field(gt=0)
    delivery_date: date

    @field_validator("container_number", mode="before")
    @classmethod
    def normalize_container(cls, value: Any) -> Any:
        return value.strip().upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def destination_must_differ(self):
        if self.origin.casefold() == self.destination.casefold():
            raise ValueError("destination must differ from origin")
        return self


def validate_extraction(data: dict[str, Any]) -> tuple[bool, dict[str, Any], dict[str, str]]:
    try:
        validated = ShipmentExtraction.model_validate(data)
        return True, validated.model_dump(), {}
    except ValidationError as exc:
        errors: dict[str, str] = {}
        for error in exc.errors():
            field = str(error["loc"][-1]) if error["loc"] else "form"
            errors[field] = error["msg"]
        return False, sanitize_for_storage(data), errors


def sanitize_for_storage(data: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "customer": str(data.get("customer") or "").strip(),
        "container_number": str(data.get("container_number") or "").strip().upper(),
        "origin": str(data.get("origin") or "").strip(),
        "destination": str(data.get("destination") or "").strip(),
        "weight_kg": None,
        "delivery_date": None,
    }
    try:
        if data.get("weight_kg") not in (None, ""):
            result["weight_kg"] = Decimal(str(data["weight_kg"]))
    except (InvalidOperation, ValueError):
        pass
    raw_date = data.get("delivery_date")
    if isinstance(raw_date, date):
        result["delivery_date"] = raw_date
    elif raw_date:
        try:
            result["delivery_date"] = date.fromisoformat(str(raw_date))
        except ValueError:
            pass
    return result
