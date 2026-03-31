from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast


class LedgerGroupError(ValueError):
    """Base error for ledger group resolution failures."""


class LedgerGroupNotFoundError(LedgerGroupError):
    """Raised when no ledger group can be matched."""


class LedgerGroupAmbiguousError(LedgerGroupError):
    """Raised when more than one ledger group matches."""


@dataclass(frozen=True)
class LedgerGroupWorkflow:
    """Utility workflow for Fiscal LedgerGroup endpoint operations."""

    _client: Any
    _fiscal_id: str

    def get_all(self) -> Any:
        """Return full raw response from GET /LedgerTag/LedgerGroup."""
        return self._client.finance.api_ledger_tag__get_ledger_group_list_get__api__fiscal_fiscal_id__ledger_tag__ledger_group(
            fiscal_id=self._fiscal_id,
            list_option_force_no_paging=True,
        )

    def get_entities(self) -> list[dict[str, str]]:
        raw: Any = self.get_all()

        if hasattr(raw, "to_dict"):
            raw = raw.to_dict()

        if not isinstance(raw, dict):
            raise LedgerGroupError("Unexpected LedgerGroup response shape: expected dict-like response")

        entities_obj = cast(dict[str, Any], raw).get("Entities")
        if not isinstance(entities_obj, list):
            raise LedgerGroupError("Unexpected LedgerGroup response shape: could not read Entities list")

        entities_list = cast(list[Any], entities_obj)
        entities: list[dict[str, str]] = []
        for item in entities_list:
            if not isinstance(item, dict):
                continue
            item_dict = cast(dict[str, Any], item)
            value = item_dict.get("Value")
            text = item_dict.get("Text")
            if isinstance(value, str) and isinstance(text, str):
                entities.append({"Value": value, "Text": text})

        if not entities:
            raise LedgerGroupError("LedgerGroup response did not contain any valid entities")

        return entities

    def get_by_value(self, value: str) -> dict[str, str]:
        matches = [entity for entity in self.get_entities() if entity["Value"] == value]
        return self._single_match(matches, f"value '{value}'")

    def get_value_by_text(self, text: str) -> str:
        matches = [entity for entity in self.get_entities() if entity["Text"] == text]
        entity = self._single_match(matches, f"text '{text}'")
        return entity["Value"]

    @staticmethod
    def _single_match(matches: list[dict[str, str]], label: str) -> dict[str, str]:
        if not matches:
            raise LedgerGroupNotFoundError(f"No ledger group found for {label}")
        if len(matches) > 1:
            raise LedgerGroupAmbiguousError(f"More than one ledger group matched {label}")
        return matches[0]
