from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any, cast

from xena_api_wrappers.workflows.finance.ledger_group_data import LedgerGroupDataWorkflow


class _FakeFinance:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def api_transaction__get_ledger_group_data_get__api__fiscal_fiscal_id__transaction__ledger_group_data(
        self,
        fiscal_id: str,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        fiscal_period_fiscal_date_from: int | None = None,
        fiscal_period_fiscal_date_to: int | None = None,
        filter_bearer_id: list[Any] | None = None,
        filter_department_id: list[Any] | None = None,
        filter_purpose_id: list[Any] | None = None,
        filter_ledger_group: str | None = None,
        filter_fiscal_period_id: int | None = None,
        filter_ledger_id: int | None = None,
        filter_include_simulated_bookkeeping: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = filter_bearer_id
        _ = filter_department_id
        _ = filter_purpose_id
        _ = kwargs
        self.calls.append(
            {
                "fiscal_id": fiscal_id,
                "force_no_paging": list_options_force_no_paging,
                "page": list_options_page,
                "page_size": list_options_page_size,
                "show_deactivated": list_options_show_deactivated,
                "date_from": fiscal_period_fiscal_date_from,
                "date_to": fiscal_period_fiscal_date_to,
                "ledger_group": filter_ledger_group,
                "fiscal_period_id": filter_fiscal_period_id,
                "ledger_id": filter_ledger_id,
                "include_simulated": filter_include_simulated_bookkeeping,
            }
        )
        return {"Count": 1, "Entities": [{"Group": filter_ledger_group}]}


class _FakeLedgerGroupWorkflow:
    def __init__(self) -> None:
        self.entities_calls = 0

    def get_entities(self) -> list[dict[str, str]]:
        self.entities_calls += 1
        return [
            {"Value": "Xena_Domain_Income_Accounts", "Text": "Resultatregnskap"},
            {"Value": "Xena_Domain_Asset_Accounts", "Text": "Eiendeler"},
            {"Value": "Xena_Domain_Liability_Accounts", "Text": "Egenkapital + Gjeld"},
        ]

    def get_value_by_text(self, text: str) -> str:
        for e in self.get_entities():
            if e["Text"] == text:
                return e["Value"]
        raise ValueError("not found")


class LedgerGroupDataWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_finance = _FakeFinance()
        self.fake_ledger_group = _FakeLedgerGroupWorkflow()
        client = SimpleNamespace(finance=self.fake_finance)
        self.workflow = LedgerGroupDataWorkflow(
            client,
            "104779",
            cast(Any, self.fake_ledger_group),
        )

    def test_get_by_ledger_group_accepts_value(self) -> None:
        result = self.workflow.get_by_ledger_group(
            "Xena_Domain_Income_Accounts",
            fiscal_period_id=2586516686,
            date_from="2025-01-01",
            date_to="2025-12-31",
        )

        self.assertEqual(result["Entities"][0]["Group"], "Xena_Domain_Income_Accounts")
        self.assertEqual(self.fake_finance.calls[-1]["date_from"], 20089)
        self.assertEqual(self.fake_finance.calls[-1]["date_to"], 20453)

    def test_get_by_ledger_group_accepts_text(self) -> None:
        result = self.workflow.get_by_ledger_group(
            "Resultatregnskap",
            fiscal_period_id=2586516686,
            date_from="01.01.2025",
            date_to="31.12.2025",
        )

        self.assertEqual(result["Entities"][0]["Group"], "Xena_Domain_Income_Accounts")

    def test_get_all_groups_merges_all_three_groups(self) -> None:
        result = self.workflow.get_all_groups(
            fiscal_period_id=2586516686,
            date_from=20089,
            date_to=20453,
        )

        self.assertEqual(set(result.keys()), {
            "Xena_Domain_Income_Accounts",
            "Xena_Domain_Asset_Accounts",
            "Xena_Domain_Liability_Accounts",
        })
        self.assertEqual(len(self.fake_finance.calls), 3)

    def test_group_entities_cached(self) -> None:
        self.workflow.get_by_ledger_group(
            "Xena_Domain_Income_Accounts",
            fiscal_period_id=2586516686,
            date_from=20089,
            date_to=20453,
        )
        self.workflow.get_by_ledger_group(
            "Xena_Domain_Asset_Accounts",
            fiscal_period_id=2586516686,
            date_from=20089,
            date_to=20453,
        )

        self.assertEqual(self.fake_ledger_group.entities_calls, 1)


if __name__ == "__main__":
    unittest.main()
