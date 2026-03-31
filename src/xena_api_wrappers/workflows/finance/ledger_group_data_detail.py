from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core import DateInput, to_fiscal_date_int
from .ledger_group_data import LedgerGroupDataWorkflow
from ..utils import FiscalPeriodWorkflow


class LedgerGroupDataDetailError(ValueError):
    """Base error for ledger group data detail workflow operations."""


@dataclass
class LedgerGroupDataDetailWorkflow:
    """Finance workflow helper for /Transaction/LedgerGroupDataDetail endpoint."""

    _client: Any
    _fiscal_id: str
    _fiscal_period_workflow: FiscalPeriodWorkflow | None = None
    _ledger_group_data_workflow: LedgerGroupDataWorkflow | None = None

    def get_by_ledger_account(
        self,
        ledger_account: str,
        *,
        date_from: DateInput,
        date_to: DateInput,
        fiscal_period_id: int | None = None,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
        show_deactivated: bool = True,
        ledger_id: int | None = None,
        include_simulated_bookkeeping: bool = False,
    ) -> Any:
        account_value = ledger_account.strip()
        if not account_value:
            raise LedgerGroupDataDetailError("ledger_account cannot be empty")

        resolved_fiscal_period_id = self._resolve_fiscal_period_id(
            fiscal_period_id=fiscal_period_id,
            date_from=date_from,
        )
        fiscal_date_from = to_fiscal_date_int(date_from)
        fiscal_date_to = to_fiscal_date_int(date_to)

        return self._client.finance.api_transaction__get_ledger_group_data_detail_get__api__fiscal_fiscal_id__transaction__ledger_group_data_detail(
            fiscal_id=self._fiscal_id,
            ledger_account=account_value,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
            fiscal_period_fiscal_date_from=fiscal_date_from,
            fiscal_period_fiscal_date_to=fiscal_date_to,
            filter_fiscal_period_id=resolved_fiscal_period_id,
            filter_ledger_id=ledger_id,
            filter_include_simulated_bookkeeping=include_simulated_bookkeeping,
        )

    def get_by_summary_group(
        self,
        summary_group: dict[str, Any],
        *,
        date_from: DateInput,
        date_to: DateInput,
        fiscal_period_id: int | None = None,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
        show_deactivated: bool = True,
        ledger_id: int | None = None,
        include_simulated_bookkeeping: bool = False,
    ) -> Any:
        ledger_account = summary_group.get("Group")
        if not isinstance(ledger_account, str):
            raise LedgerGroupDataDetailError("summary_group must include string field 'Group'")

        return self.get_by_ledger_account(
            ledger_account,
            date_from=date_from,
            date_to=date_to,
            fiscal_period_id=fiscal_period_id,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
            show_deactivated=show_deactivated,
            ledger_id=ledger_id,
            include_simulated_bookkeeping=include_simulated_bookkeeping,
        )

    def get_accounts(
        self,
        *,
        date_from: DateInput,
        date_to: DateInput,
        account_number_from: int = 1000,
        account_number_to: int = 9999,
        fiscal_period_id: int | None = None,
        force_no_paging: bool = True,
        show_deactivated_summary: bool = False,
        show_deactivated_detail: bool = True,
        include_simulated_bookkeeping: bool = False,
        ledger_id: int | None = None,
    ) -> list[dict[str, Any]]:
        if account_number_from > account_number_to:
            raise LedgerGroupDataDetailError("account_number_from cannot be greater than account_number_to")

        resolved_fiscal_period_id = self._resolve_fiscal_period_id(
            fiscal_period_id=fiscal_period_id,
            date_from=date_from,
        )

        summary_per_top_group = self._get_ledger_group_data_workflow().get_all_groups(
            fiscal_period_id=resolved_fiscal_period_id,
            date_from=date_from,
            date_to=date_to,
            force_no_paging=force_no_paging,
            show_deactivated=show_deactivated_summary,
            include_simulated_bookkeeping=include_simulated_bookkeeping,
            ledger_id=ledger_id,
        )

        unique_accounts: dict[int, dict[str, Any]] = {}
        for summary_payload in summary_per_top_group.values():
            summary_entities = self._extract_entities(summary_payload)
            for summary_group in summary_entities:
                detail_payload = self.get_by_summary_group(
                    summary_group,
                    date_from=date_from,
                    date_to=date_to,
                    fiscal_period_id=resolved_fiscal_period_id,
                    force_no_paging=force_no_paging,
                    show_deactivated=show_deactivated_detail,
                    include_simulated_bookkeeping=include_simulated_bookkeeping,
                    ledger_id=ledger_id,
                )
                detail_entities = self._extract_entities(detail_payload)
                for account_row in detail_entities:
                    account_number = account_row.get("AccountNumber")
                    if isinstance(account_number, int):
                        if account_number_from <= account_number <= account_number_to:
                            unique_accounts[account_number] = account_row

        return [unique_accounts[k] for k in sorted(unique_accounts)]

    def get_all_accounts(
        self,
        *,
        date_from: DateInput,
        date_to: DateInput,
        fiscal_period_id: int | None = None,
        force_no_paging: bool = True,
        show_deactivated_summary: bool = False,
        show_deactivated_detail: bool = True,
        include_simulated_bookkeeping: bool = False,
        ledger_id: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.get_accounts(
            date_from=date_from,
            date_to=date_to,
            account_number_from=1000,
            account_number_to=9999,
            fiscal_period_id=fiscal_period_id,
            force_no_paging=force_no_paging,
            show_deactivated_summary=show_deactivated_summary,
            show_deactivated_detail=show_deactivated_detail,
            include_simulated_bookkeeping=include_simulated_bookkeeping,
            ledger_id=ledger_id,
        )

    def get_balance_accounts(
        self,
        *,
        date_from: DateInput,
        date_to: DateInput,
        fiscal_period_id: int | None = None,
        force_no_paging: bool = True,
        show_deactivated_summary: bool = False,
        show_deactivated_detail: bool = True,
        include_simulated_bookkeeping: bool = False,
        ledger_id: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.get_accounts(
            date_from=date_from,
            date_to=date_to,
            account_number_from=1000,
            account_number_to=2999,
            fiscal_period_id=fiscal_period_id,
            force_no_paging=force_no_paging,
            show_deactivated_summary=show_deactivated_summary,
            show_deactivated_detail=show_deactivated_detail,
            include_simulated_bookkeeping=include_simulated_bookkeeping,
            ledger_id=ledger_id,
        )

    def get_result_accounts(
        self,
        *,
        date_from: DateInput,
        date_to: DateInput,
        fiscal_period_id: int | None = None,
        force_no_paging: bool = True,
        show_deactivated_summary: bool = False,
        show_deactivated_detail: bool = True,
        include_simulated_bookkeeping: bool = False,
        ledger_id: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.get_accounts(
            date_from=date_from,
            date_to=date_to,
            account_number_from=3000,
            account_number_to=9999,
            fiscal_period_id=fiscal_period_id,
            force_no_paging=force_no_paging,
            show_deactivated_summary=show_deactivated_summary,
            show_deactivated_detail=show_deactivated_detail,
            include_simulated_bookkeeping=include_simulated_bookkeeping,
            ledger_id=ledger_id,
        )

    def _resolve_fiscal_period_id(
        self,
        *,
        fiscal_period_id: int | None,
        date_from: DateInput,
    ) -> int:
        if fiscal_period_id is not None:
            return fiscal_period_id
        return self._get_fiscal_period_workflow().get_id_by_date(date_from)

    def _get_fiscal_period_workflow(self) -> FiscalPeriodWorkflow:
        if self._fiscal_period_workflow is None:
            self._fiscal_period_workflow = FiscalPeriodWorkflow(self._client, self._fiscal_id)
        return self._fiscal_period_workflow

    def _get_ledger_group_data_workflow(self) -> LedgerGroupDataWorkflow:
        if self._ledger_group_data_workflow is None:
            self._ledger_group_data_workflow = LedgerGroupDataWorkflow(
                self._client,
                self._fiscal_id,
                None,
                self._get_fiscal_period_workflow(),
            )
        return self._ledger_group_data_workflow

    @staticmethod
    def _extract_entities(raw_payload: Any) -> list[dict[str, Any]]:
        if isinstance(raw_payload, dict):
            entities = raw_payload.get("Entities")
            if isinstance(entities, list):
                return [e for e in entities if isinstance(e, dict)]
        if hasattr(raw_payload, "to_dict"):
            converted = raw_payload.to_dict()
            if isinstance(converted, dict):
                entities = converted.get("Entities")
                if isinstance(entities, list):
                    return [e for e in entities if isinstance(e, dict)]
        return []