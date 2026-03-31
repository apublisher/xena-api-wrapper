from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any, cast

from xena_api_wrappers.workflows.finance.ledger_group_data_detail import (
    LedgerGroupDataDetailError,
    LedgerGroupDataDetailWorkflow,
)


class _FakeFinance:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def api_transaction__get_ledger_group_data_detail_get__api__fiscal_fiscal_id__transaction__ledger_group_data_detail(
        self,
        fiscal_id: str,
        ledger_account: str | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        fiscal_period_fiscal_date_from: int | None = None,
        fiscal_period_fiscal_date_to: int | None = None,
        filter_fiscal_period_id: int | None = None,
        filter_ledger_id: int | None = None,
        filter_include_simulated_bookkeeping: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        self.calls.append(
            {
                "fiscal_id": fiscal_id,
                "show_deactivated": list_options_show_deactivated,
                "page": list_options_page,
                "page_size": list_options_page_size,
                "force_no_paging": list_options_force_no_paging,
                "date_from": fiscal_period_fiscal_date_from,
                "date_to": fiscal_period_fiscal_date_to,
                "ledger_account": ledger_account,
                "fiscal_period_id": filter_fiscal_period_id,
                "ledger_id": filter_ledger_id,
                "include_simulated": filter_include_simulated_bookkeeping,
            }
        )
        return {"Count": 1, "Entities": [{"LedgerAccount": ledger_account}]}


class _FakeFiscalPeriodWorkflow:
    def __init__(self, period_id: int = 2586516686) -> None:
        self.period_id = period_id
        self.calls: list[Any] = []

    def get_id_by_date(self, selected_date: Any) -> int:
        self.calls.append(selected_date)
        return self.period_id


class LedgerGroupDataDetailWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_finance = _FakeFinance()
        self.fake_fiscal_period = _FakeFiscalPeriodWorkflow()
        client = SimpleNamespace(finance=self.fake_finance)
        self.workflow = LedgerGroupDataDetailWorkflow(
            client,
            "104779",
            cast(Any, self.fake_fiscal_period),
        )

    def test_get_by_ledger_account_uses_provided_fiscal_period(self) -> None:
        result = self.workflow.get_by_ledger_account(
            "Xena_Domain_Income_Accounts_Administration_Costs",
            fiscal_period_id=2586516686,
            date_from="2025-01-01",
            date_to="2025-12-31",
        )

        self.assertEqual(result["Entities"][0]["LedgerAccount"], "Xena_Domain_Income_Accounts_Administration_Costs")
        self.assertEqual(self.fake_finance.calls[-1]["date_from"], 20089)
        self.assertEqual(self.fake_finance.calls[-1]["date_to"], 20453)
        self.assertEqual(self.fake_finance.calls[-1]["show_deactivated"], True)
        self.assertEqual(self.fake_fiscal_period.calls, [])

    def test_get_by_ledger_account_auto_resolves_fiscal_period(self) -> None:
        self.workflow.get_by_ledger_account(
            "Xena_Domain_Liability_Accounts_Equity",
            date_from="2025-01-01",
            date_to="2025-01-31",
        )

        self.assertEqual(self.fake_fiscal_period.calls, ["2025-01-01"])
        self.assertEqual(self.fake_finance.calls[-1]["fiscal_period_id"], 2586516686)

    def test_get_by_summary_group_reads_group_field(self) -> None:
        summary_group = {"Group": "Xena_Domain_Asset_Accounts_Tangible_Fixed_Asset"}
        result = self.workflow.get_by_summary_group(
            summary_group,
            date_from=20089,
            date_to=20453,
            fiscal_period_id=2586516686,
        )

        self.assertEqual(result["Entities"][0]["LedgerAccount"], "Xena_Domain_Asset_Accounts_Tangible_Fixed_Asset")

    def test_empty_ledger_account_raises(self) -> None:
        with self.assertRaises(LedgerGroupDataDetailError):
            self.workflow.get_by_ledger_account(
                "  ",
                date_from="2025-01-01",
                date_to="2025-01-31",
            )

    def test_summary_group_without_group_raises(self) -> None:
        with self.assertRaises(LedgerGroupDataDetailError):
            self.workflow.get_by_summary_group(
                {"TranslatedGroup": "Egenkapital"},
                date_from="2025-01-01",
                date_to="2025-01-31",
            )


if __name__ == "__main__":
    unittest.main()