from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast


class VatError(ValueError):
    """Base error for VAT workflow operations."""


class VatNotFoundError(VatError):
    """Raised when no VAT row can be matched."""


class VatAmbiguousError(VatError):
    """Raised when more than one VAT row matches a selector."""


@dataclass
class VatWorkflow:
    """Workflow helper for /Vat endpoint operations."""

    _client: Any
    _fiscal_id: str

    def get_all(
        self,
        *,
        query_string: str | None = None,
        include_defaults: bool | None = None,
        excluded_vat_id: int | None = None,
        exclude_import_type: bool | None = None,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self._client.finance.api_vat__get_get__api__fiscal_fiscal_id__vat(
            fiscal_id=self._fiscal_id,
            querystring=query_string,
            include_defaults=include_defaults,
            excluded_vat_id=excluded_vat_id,
            exclude_import_type=exclude_import_type,
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
            raise VatError("Unexpected VAT response shape: expected dict-like response")

        entities_obj = cast(dict[str, Any], raw).get("Entities")
        if not isinstance(entities_obj, list):
            raise VatError("Unexpected VAT response shape: could not read Entities list")

        entities: list[dict[str, Any]] = []
        for item in cast(list[Any], entities_obj):
            if isinstance(item, dict):
                entities.append(cast(dict[str, Any], item))
        return entities

    def get_by_id(self, vat_id: int) -> Any:
        return self._client.finance.api_vat__get_get__api__fiscal_fiscal_id__vat_id(
            id=vat_id,
            fiscal_id=self._fiscal_id,
        )

    def get_types(
        self,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self._client.finance.api_vat__get_vat_type_get__api__fiscal_fiscal_id__vat__vat_type(
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_by_type(
        self,
        vat_type: str,
        *,
        query_string: str | None = None,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self._client.finance.api_vat__get_by_type_get__api__fiscal_fiscal_id__vat__by_type(
            fiscal_id=self._fiscal_id,
            query_string=query_string,
            vat_type=vat_type,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_by_abbreviation(self, abbreviation: str, **kwargs: Any) -> dict[str, Any]:
        needle = abbreviation.strip().casefold()
        matches = [
            row
            for row in self.get_entities(**kwargs)
            if isinstance(row.get("Abbreviation"), str)
            and row["Abbreviation"].strip().casefold() == needle
        ]
        if not matches:
            raise VatNotFoundError(f"No VAT found for abbreviation '{abbreviation}'")
        if len(matches) > 1:
            raise VatAmbiguousError(
                f"More than one VAT row matched abbreviation '{abbreviation}'"
            )
        return matches[0]

    def get_id_by_abbreviation(self, abbreviation: str, **kwargs: Any) -> int:
        row = self.get_by_abbreviation(abbreviation, **kwargs)
        vat_id = row.get("Id")
        if not isinstance(vat_id, int):
            raise VatError("VAT response missing integer Id field")
        return vat_id
