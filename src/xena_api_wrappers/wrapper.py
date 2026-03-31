from __future__ import annotations

import importlib
from typing import Any

from .core import ClientFactory, DateInput, default_client_factory
from .credentials import XenaCredentials
from .workflows import (
    FiscalPeriodWorkflow,
    LedgerAccountWorkflow,
    LedgerGroupDataWorkflow,
    LedgerGroupDataDetailWorkflow,
    LedgerGroupWorkflow,
    LedgerPostWorkflow,
)



class XenaApiWrapper:
    """High-level, task-oriented wrapper on top of xena-client."""

    def __init__(
        self,
        api_key: str | None = None,
        fiscal_id: str | None = None,
        *,
        credentials: XenaCredentials | None = None,
        client_factory: ClientFactory | None = None,
    ) -> None:
        if credentials is None:
            if not api_key or not fiscal_id:
                raise ValueError("Provide either credentials or both api_key and fiscal_id")
            credentials = XenaCredentials(api_key=api_key, fiscal_id=str(fiscal_id))

        self._credentials = credentials
        factory = client_factory or default_client_factory
        self._client = factory(self._credentials.api_key, self._credentials.fiscal_id)
        self._fiscal_period_workflow: FiscalPeriodWorkflow | None = None
        self._ledger_account_workflow: LedgerAccountWorkflow | None = None
        self._ledger_group_workflow: LedgerGroupWorkflow | None = None
        self._ledger_group_data_workflow: LedgerGroupDataWorkflow | None = None
        self._ledger_group_data_detail_workflow: LedgerGroupDataDetailWorkflow | None = None
        self._ledger_post_workflow: LedgerPostWorkflow | None = None

    @classmethod
    def from_env(
        cls,
        *,
        prefix: str = "",
        load_dotenv: bool = False,
        dotenv_path: str | None = None,
        client_factory: ClientFactory | None = None,
    ) -> "XenaApiWrapper":
        if load_dotenv:
            try:
                dotenv_module = importlib.import_module("dotenv")
            except ImportError as exc:
                raise ImportError(
                    "python-dotenv is not installed. Install with: pip install xena-api-wrappers[dotenv]"
                ) from exc

            dotenv_load = getattr(dotenv_module, "load_dotenv")
            dotenv_load(dotenv_path=dotenv_path)

        creds = XenaCredentials.from_env(prefix=prefix)
        return cls(credentials=creds, client_factory=client_factory)

    @property
    def client(self) -> Any:
        """Expose the underlying xena-client for advanced use cases."""
        return self._client

    @property
    def fiscal_id(self) -> str:
        return self._credentials.fiscal_id

    @property
    def fiscal_period(self) -> FiscalPeriodWorkflow:
        if self._fiscal_period_workflow is None:
            self._fiscal_period_workflow = FiscalPeriodWorkflow(self._client, self.fiscal_id)
        return self._fiscal_period_workflow

    def get_fiscal_periods(self) -> Any:
        # Backward-compatible facade method.
        return self.fiscal_period.get_all()

    def get_fiscal_period_id_by_date(self, selected_date: DateInput) -> int:
        # Backward-compatible facade method.
        return self.fiscal_period.get_id_by_date(selected_date)

    @property
    def ledger_account(self) -> LedgerAccountWorkflow:
        if self._ledger_account_workflow is None:
            self._ledger_account_workflow = LedgerAccountWorkflow(self._client, self.fiscal_id)
        return self._ledger_account_workflow

    @property
    def ledger_group(self) -> LedgerGroupWorkflow:
        if self._ledger_group_workflow is None:
            self._ledger_group_workflow = LedgerGroupWorkflow(self._client, self.fiscal_id)
        return self._ledger_group_workflow

    def get_ledger_groups(self) -> Any:
        return self.ledger_group.get_all()

    @property
    def ledger_group_data(self) -> LedgerGroupDataWorkflow:
        if self._ledger_group_data_workflow is None:
            self._ledger_group_data_workflow = LedgerGroupDataWorkflow(
                self._client,
                self.fiscal_id,
                self.ledger_group,
                self.fiscal_period,
            )
        return self._ledger_group_data_workflow

    @property
    def ledger_group_data_detail(self) -> LedgerGroupDataDetailWorkflow:
        if self._ledger_group_data_detail_workflow is None:
            self._ledger_group_data_detail_workflow = LedgerGroupDataDetailWorkflow(
                self._client,
                self.fiscal_id,
                self.fiscal_period,
                self.ledger_group_data,
            )
        return self._ledger_group_data_detail_workflow

    @property
    def ledger_post(self) -> LedgerPostWorkflow:
        if self._ledger_post_workflow is None:
            self._ledger_post_workflow = LedgerPostWorkflow(
                self._client,
                self.fiscal_id,
                self.ledger_account,
            )
        return self._ledger_post_workflow

    def get_all_accounts(self) -> list[dict[str, Any]]:
        return self.ledger_account.get_all_accounts()

    def get_balance_accounts(self) -> list[dict[str, Any]]:
        return self.ledger_account.get_balance_accounts()

    def get_result_accounts(self) -> list[dict[str, Any]]:
        return self.ledger_account.get_result_accounts()

    def get_all_report_accounts(self, date_from: DateInput, date_to: DateInput) -> list[dict[str, Any]]:
        return self.ledger_group_data_detail.get_all_accounts(
            date_from=date_from,
            date_to=date_to,
        )

    def get_balance_report_accounts(self, date_from: DateInput, date_to: DateInput) -> list[dict[str, Any]]:
        return self.ledger_group_data_detail.get_balance_accounts(
            date_from=date_from,
            date_to=date_to,
        )

    def get_result_report_accounts(self, date_from: DateInput, date_to: DateInput) -> list[dict[str, Any]]:
        return self.ledger_group_data_detail.get_result_accounts(
            date_from=date_from,
            date_to=date_to,
        )

    def get_entries_by_account(
        self,
        account: int | str,
        date_from: DateInput,
        date_to: DateInput,
        *,
        include_running_totals: bool = True,
        force_no_paging: bool = False,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
        show_reconciled: bool | None = None,
        reverse_date_sort: bool | None = None,
    ) -> Any:
        return self.ledger_post.get_entries_by_account(
            account,
            date_from,
            date_to,
            include_running_totals=include_running_totals,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
            show_reconciled=show_reconciled,
            reverse_date_sort=reverse_date_sort,
        )

    def get_transactions_by_voucher(
        self,
        voucher_id: int,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self.ledger_post.get_transactions_by_voucher(
            voucher_id,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

    def get_posting_details(
        self,
        transaction_id: int,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> dict[str, Any]:
        return self.ledger_post.get_posting_details(
            transaction_id,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

    def get_posting_details_by_voucher(
        self,
        voucher_id: int,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> list[dict[str, Any]]:
        return self.ledger_post.get_posting_details_by_voucher(
            voucher_id,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )
