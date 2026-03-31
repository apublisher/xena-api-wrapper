from __future__ import annotations

from typing import Any

from ...core import DateInput, to_fiscal_date_int


class BalanceWorkflow:
    """Balance-related orchestrations built from multiple low-level API calls."""

    def __init__(self, client: Any, fiscal_id: str) -> None:
        self._client = client
        self._fiscal_id = fiscal_id

    def get_balance_data(self, date_from: DateInput, date_to: DateInput) -> dict[str, Any]:
        fiscal_date_from = to_fiscal_date_int(date_from)
        fiscal_date_to = to_fiscal_date_int(date_to)

        fiscal_period_from = self._client.finance.api_fiscal_period__get_dates_get__api__fiscal_fiscal_id__fiscal_period__dates(
            fiscal_id=self._fiscal_id,
            date=fiscal_date_from,
        )
        fiscal_period_to = self._client.finance.api_fiscal_period__get_dates_get__api__fiscal_fiscal_id__fiscal_period__dates(
            fiscal_id=self._fiscal_id,
            date=fiscal_date_to,
        )

        ledger_group_data = self._client.finance.api_transaction__get_ledger_group_data_get__api__fiscal_fiscal_id__transaction__ledger_group_data(
            fiscal_id=self._fiscal_id,
            fiscal_period_fiscal_date_from=fiscal_date_from,
            fiscal_period_fiscal_date_to=fiscal_date_to,
            list_options_force_no_paging=True,
        )

        return {
            "fiscal_date_from": fiscal_date_from,
            "fiscal_date_to": fiscal_date_to,
            "fiscal_period_from": fiscal_period_from,
            "fiscal_period_to": fiscal_period_to,
            "ledger_group_data": ledger_group_data,
        }
