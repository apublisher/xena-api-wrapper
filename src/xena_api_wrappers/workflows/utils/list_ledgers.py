from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast


class LedgerListError(ValueError):
    """Base error for ledger listing and resolution failures."""


class LedgerNotFoundError(LedgerListError):
    """Raised when no ledger can be matched."""


class LedgerAmbiguousError(LedgerListError):
    """Raised when more than one ledger matches a selector."""


@dataclass
class LedgerListWorkflow:
    """Workflow helper for /Ledger endpoint operations."""

    _client: Any
    _fiscal_id: str

    def get_all(
        self,
        *,
        force_no_paging: bool = True,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        query_string: str | None = None,
        include_defaults: bool | None = None,
    ) -> Any:
        return self._client.finance.api_ledger__get_get__api__fiscal_fiscal_id__ledger(
            fiscal_id=self._fiscal_id,
            querystring=query_string,
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
            raise LedgerListError("Unexpected Ledger response shape: expected dict-like response")

        entities_obj = cast(dict[str, Any], raw).get("Entities")
        if not isinstance(entities_obj, list):
            raise LedgerListError("Unexpected Ledger response shape: could not read Entities list")

        entities: list[dict[str, Any]] = []
        for item in cast(list[Any], entities_obj):
            if isinstance(item, dict):
                entities.append(cast(dict[str, Any], item))

        return entities

    def get_by_id(self, ledger_id: int | str, **kwargs: Any) -> dict[str, Any]:
        expected = str(ledger_id)
        matches = [
            row
            for row in self.get_entities(**kwargs)
            if str(row.get("Id")) == expected
        ]
        if not matches:
            raise LedgerNotFoundError(f"No ledger found for id '{ledger_id}'")
        if len(matches) > 1:
            raise LedgerAmbiguousError(f"More than one ledger matched id '{ledger_id}'")
        return matches[0]

    def get_by_description(self, description: str, **kwargs: Any) -> dict[str, Any]:
        needle = description.strip().casefold()
        matches = [
            row
            for row in self.get_entities(**kwargs)
            if isinstance(row.get("Description"), str)
            and row["Description"].strip().casefold() == needle
        ]
        if not matches:
            raise LedgerNotFoundError(f"No ledger found for description '{description}'")
        if len(matches) > 1:
            raise LedgerAmbiguousError(
                f"More than one ledger matched description '{description}'"
            )
        return matches[0]

    def get_id_by_description(self, description: str, **kwargs: Any) -> int:
        row = self.get_by_description(description, **kwargs)
        ledger_id = row.get("Id")
        if not isinstance(ledger_id, int):
            raise LedgerListError("Ledger response missing integer Id field")
        return ledger_id
