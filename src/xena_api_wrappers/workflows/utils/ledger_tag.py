from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast


class LedgerTagError(ValueError):
    """Base error for ledger tag workflow operations."""


class LedgerTagNotFoundError(LedgerTagError):
    """Raised when no ledger tag can be matched."""


class LedgerTagAmbiguousError(LedgerTagError):
    """Raised when more than one ledger tag matches a selector."""


@dataclass
class LedgerTagWorkflow:
    """Workflow helper for /LedgerTag endpoint operations."""

    _client: Any
    _fiscal_id: str

    def get_all(
        self,
        *,
        ledger_account: str | None = None,
        query_string: str | None = None,
        include_defaults: bool | None = None,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self._client.finance.api_ledger_tag__get_get__api__fiscal_fiscal_id__ledger_tag(
            fiscal_id=self._fiscal_id,
            ledger_account=ledger_account,
            query_string=query_string,
            include_defaults=include_defaults,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        raw: Any = self.get_all(**kwargs)
        if not isinstance(raw, dict):
            if hasattr(raw, "to_dict"):
                raw = raw.to_dict()

        if not isinstance(raw, dict):
            raise LedgerTagError("Unexpected LedgerTag response shape: expected dict-like response")

        entities_obj = cast(dict[str, Any], raw).get("Entities")
        if not isinstance(entities_obj, list):
            raise LedgerTagError("Unexpected LedgerTag response shape: could not read Entities list")

        entities: list[dict[str, Any]] = []
        for item in cast(list[Any], entities_obj):
            if isinstance(item, dict):
                entities.append(cast(dict[str, Any], item))
        return entities

    def get_by_id(self, ledger_tag_id: int) -> Any:
        return self._client.finance.api_ledger_tag__get_get__api__fiscal_fiscal_id__ledger_tag_id(
            id=ledger_tag_id,
            fiscal_id=self._fiscal_id,
        )

    def get_by_number(self, number: int | str, **kwargs: Any) -> dict[str, Any]:
        expected = self._normalize_number(number)
        matches = [
            row
            for row in self.get_entities(**kwargs)
            if self._extract_number(row) == expected
        ]

        if not matches:
            raise LedgerTagNotFoundError(f"No ledger tag found for number {expected}")
        if len(matches) > 1:
            raise LedgerTagAmbiguousError(f"More than one ledger tag matched number {expected}")
        return matches[0]

    def get_id_by_number(self, number: int | str, **kwargs: Any) -> int:
        row = self.get_by_number(number, **kwargs)
        tag_id = row.get("Id")
        if not isinstance(tag_id, int):
            raise LedgerTagError("LedgerTag response missing integer Id field")
        return tag_id

    def get_settlement_tags(
        self,
        *,
        include_default: bool | None = None,
        query_string: str | None = None,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self._client.finance.api_ledger_tag__get_settlement_tag_get__api__fiscal_fiscal_id__ledger_tag__settlement_tag(
            fiscal_id=self._fiscal_id,
            include_default=include_default,
            query_string=query_string,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    @staticmethod
    def _normalize_number(number: int | str) -> int:
        if isinstance(number, int):
            if number < 0:
                raise LedgerTagError("Ledger tag number must be non-negative")
            return number

        cleaned = number.strip()
        if not cleaned.isdigit():
            raise LedgerTagError(f"Ledger tag number must be numeric. Got: {number!r}")
        return int(cleaned)

    @staticmethod
    def _extract_number(row: dict[str, Any]) -> int | None:
        candidates = (
            row.get("Number"),
            row.get("TagNumber"),
            row.get("LedgerTagNumber"),
            row.get("AccountNumber"),
        )
        for value in candidates:
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.strip().isdigit():
                return int(value.strip())
        return None
