from __future__ import annotations

from typing import Any, cast


def as_dict(value: Any, error_type: type[ValueError], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            value = to_dict()
    if not isinstance(value, dict):
        raise error_type(f"Unexpected {label} response: expected a dict")
    return cast(dict[str, Any], value)


def extract_entities(value: Any, error_type: type[ValueError], label: str) -> list[dict[str, Any]]:
    entities = as_dict(value, error_type, label).get("Entities")
    if not isinstance(entities, list):
        raise error_type(f"Unexpected {label} response: expected an Entities list of dictionaries")
    rows = cast(list[object], entities)
    if any(not isinstance(row, dict) for row in rows):
        raise error_type(f"Unexpected {label} response: expected an Entities list of dictionaries")
    return cast(list[dict[str, Any]], entities)


def positive_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def non_negative_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def boolean_param(value: object, label: str) -> str:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean")
    return str(value).lower()


def non_empty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value
