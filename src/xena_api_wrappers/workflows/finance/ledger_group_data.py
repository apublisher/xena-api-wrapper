from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core import DateInput, to_fiscal_date_int
from ..utils import FiscalPeriodWorkflow, LedgerGroupNotFoundError, LedgerGroupWorkflow


class LedgerGroupDataError(ValueError):
    """Base error for ledger group data workflow operations."""


@dataclass
class LedgerGroupDataWorkflow:
    """Finance workflow helper for /Transaction/LedgerGroupData endpoint."""

    _client: Any
    _fiscal_id: str
    _ledger_group_workflow: LedgerGroupWorkflow | None = None
    _fiscal_period_workflow: FiscalPeriodWorkflow | None = None
    _cached_group_entities: list[dict[str, str]] | None = field(default=None, init=False)

    def get_by_ledger_group(
        self,
        ledger_group: str,
        *,
        fiscal_period_id: int | None = None,
        date_from: DateInput,
        date_to: DateInput,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
        show_deactivated: bool = False,
        ledger_id: int | None = None,
        include_simulated_bookkeeping: bool = False,
    ) -> Any:
        ledger_group_value = self._resolve_group_value(ledger_group)
        resolved_fiscal_period_id = self._resolve_fiscal_period_id(
            fiscal_period_id=fiscal_period_id,
            date_from=date_from,
        )
        fiscal_date_from = to_fiscal_date_int(date_from)
        fiscal_date_to = to_fiscal_date_int(date_to)

        return self._client.finance.api_transaction__get_ledger_group_data_get__api__fiscal_fiscal_id__transaction__ledger_group_data(
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
            fiscal_period_fiscal_date_from=fiscal_date_from,
            fiscal_period_fiscal_date_to=fiscal_date_to,
            filter_ledger_group=ledger_group_value,
            filter_fiscal_period_id=resolved_fiscal_period_id,
            filter_ledger_id=ledger_id,
            filter_include_simulated_bookkeeping=include_simulated_bookkeeping,
        )

    def get_all_groups(
        self,
        *,
        fiscal_period_id: int | None = None,
        date_from: DateInput,
        date_to: DateInput,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
        show_deactivated: bool = False,
        ledger_id: int | None = None,
        include_simulated_bookkeeping: bool = False,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        resolved_fiscal_period_id = self._resolve_fiscal_period_id(
            fiscal_period_id=fiscal_period_id,
            date_from=date_from,
        )

        for entity in self._get_group_entities():
            value = entity["Value"]
            result[value] = self.get_by_ledger_group(
                value,
                fiscal_period_id=resolved_fiscal_period_id,
                date_from=date_from,
                date_to=date_to,
                page=page,
                page_size=page_size,
                force_no_paging=force_no_paging,
                show_deactivated=show_deactivated,
                ledger_id=ledger_id,
                include_simulated_bookkeeping=include_simulated_bookkeeping,
            )

        return result

    def get_balance_sheet(
        self,
        *,
        date_from: DateInput,
        date_to: DateInput,
        fiscal_period_id: int | None = None,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
        show_deactivated: bool = False,
        ledger_id: int | None = None,
        include_simulated_bookkeeping: bool = False,
    ) -> dict[str, Any]:
        """Convenience helper that returns all balance-report groups for a date range."""
        return self.get_all_groups(
            fiscal_period_id=fiscal_period_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
            show_deactivated=show_deactivated,
            ledger_id=ledger_id,
            include_simulated_bookkeeping=include_simulated_bookkeeping,
        )

    def _resolve_group_value(self, value_or_text: str) -> str:
        candidate = value_or_text.strip()
        if not candidate:
            raise LedgerGroupDataError("ledger_group cannot be empty")

        if candidate.startswith("Xena_Domain_"):
            for entity in self._get_group_entities():
                if entity["Value"] == candidate:
                    return candidate
            raise LedgerGroupNotFoundError(f"No ledger group found for value '{candidate}'")

        return self._get_ledger_group_workflow().get_value_by_text(candidate)

    def _get_group_entities(self) -> list[dict[str, str]]:
        if self._cached_group_entities is None:
            self._cached_group_entities = self._get_ledger_group_workflow().get_entities()
        return self._cached_group_entities

    def _resolve_fiscal_period_id(
        self,
        *,
        fiscal_period_id: int | None,
        date_from: DateInput,
    ) -> int:
        if fiscal_period_id is not None:
            return fiscal_period_id
        return self._get_fiscal_period_workflow().get_id_by_date(date_from)

    def _get_ledger_group_workflow(self) -> LedgerGroupWorkflow:
        if self._ledger_group_workflow is None:
            self._ledger_group_workflow = LedgerGroupWorkflow(self._client, self._fiscal_id)
        return self._ledger_group_workflow

    def _get_fiscal_period_workflow(self) -> FiscalPeriodWorkflow:
        if self._fiscal_period_workflow is None:
            self._fiscal_period_workflow = FiscalPeriodWorkflow(self._client, self._fiscal_id)
        return self._fiscal_period_workflow
