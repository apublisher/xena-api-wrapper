from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, cast

from ...core import DateInput, to_fiscal_date_int


class FiscalPeriodError(ValueError):
    """Base error for fiscal period resolution failures."""


class FiscalPeriodNotFoundError(FiscalPeriodError):
    """Raised when no fiscal period can be matched."""


class FiscalPeriodAmbiguousError(FiscalPeriodError):
    """Raised when more than one fiscal period matches."""


@dataclass(frozen=True)
class FiscalPeriodWorkflow:
    """Workflow helper for FiscalPeriod endpoint operations."""

    _client: Any
    _fiscal_id: str

    def get_all(self) -> Any:
        """Return full raw response from GET /FiscalPeriod."""
        return self._client.finance.api_fiscal_period__get_get__api__fiscal_fiscal_id__fiscal_period(
            fiscal_id=self._fiscal_id,
            list_options_force_no_paging=True,
        )

    def get_id_by_date(self, selected_date: DateInput) -> int:
        period = self.get_by_date(selected_date)
        period_id = period.get("Id")
        if not isinstance(period_id, int):
            raise FiscalPeriodError("Fiscal period response missing integer Id field")
        return period_id

    def get_by_date(self, selected_date: DateInput) -> dict[str, Any]:
        selected_day = to_fiscal_date_int(selected_date)
        entities = self._get_period_entities()

        matches = [period for period in entities if self._is_within_period(selected_day, period)]

        if not matches:
            friendly = self._friendly_selected_value(selected_date)
            raise FiscalPeriodNotFoundError(
                f"No fiscal period found for {friendly}. "
                "Selected fiscal year does not exist and needs to be set up in Xena."
            )

        if len(matches) > 1:
            raise FiscalPeriodAmbiguousError(
                f"More than one fiscal period matched date '{selected_date}'. "
                "Use an exact fiscal date and verify fiscal setup in Xena."
            )

        return matches[0]

    def get_id_by_year(self, year: int | str) -> int:
        period = self.get_by_year(year)
        period_id = period.get("Id")
        if not isinstance(period_id, int):
            raise FiscalPeriodError("Fiscal period response missing integer Id field")
        return period_id

    def get_by_year(self, year: int | str) -> dict[str, Any]:
        year_value = self._normalize_year(year)
        entities = self._get_period_entities()

        matches = [
            period
            for period in entities
            if str(period.get("Description", "")).strip() == str(year_value)
        ]

        if not matches:
            raise FiscalPeriodNotFoundError(
                f"No fiscal period found for year '{year_value}'. "
                "Selected fiscal year does not exist and needs to be set up in Xena."
            )

        if len(matches) > 1:
            raise FiscalPeriodAmbiguousError(
                f"More than one fiscal period matched year '{year_value}'. "
                "Use get_by_date(...) for explicit matching."
            )

        return matches[0]

    def _get_period_entities(self) -> list[dict[str, Any]]:
        raw: Any = self.get_all()

        if hasattr(raw, "to_dict"):
            raw = raw.to_dict()

        if not isinstance(raw, dict):
            raise FiscalPeriodError("Unexpected FiscalPeriod response shape: expected dict-like response")

        raw_dict = cast(dict[str, Any], raw)
        entities_obj = raw_dict.get("Entities")
        if not isinstance(entities_obj, list):
            raise FiscalPeriodError("Unexpected FiscalPeriod response shape: could not read Entities list")

        entities_list = cast(list[Any], entities_obj)
        entities: list[dict[str, Any]] = []
        for item in entities_list:
            if isinstance(item, dict):
                entities.append(cast(dict[str, Any], item))

        if entities:
            return entities

        raise FiscalPeriodError("Unexpected FiscalPeriod response shape: could not read Entities list")

    @staticmethod
    def _is_within_period(selected_day: int, period: dict[str, Any]) -> bool:
        start_day = period.get("FiscalPeriodStartDays")
        end_day = period.get("FiscalPeriodEndDays")

        if not isinstance(start_day, int) or not isinstance(end_day, int):
            return False

        return start_day <= selected_day <= end_day

    @staticmethod
    def _normalize_year(value: int | str) -> int:
        if isinstance(value, int):
            year_value = value
        else:
            cleaned = value.strip()
            if not (cleaned.isdigit() and len(cleaned) == 4):
                raise FiscalPeriodError(
                    f"Year must be YYYY format. Got: {value!r}. Use get_by_date(...) for full date matching."
                )
            year_value = int(cleaned)

        if year_value < 1900 or year_value > 3000:
            raise FiscalPeriodError(f"Year out of supported range: {year_value}")

        return year_value

    @staticmethod
    def _friendly_selected_value(value: DateInput) -> str:
        if isinstance(value, int):
            return str(date.fromordinal(date(1970, 1, 1).toordinal() + value))
        return str(value)
