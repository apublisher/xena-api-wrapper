from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any, cast

from xena_api_wrappers.workflows.finance.ledger_post import LedgerPostError, LedgerPostWorkflow


class _FakeFinance:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def api_ledger_post__get_by_ledger_tag_get__api__fiscal_fiscal_id__ledger_tag_id__ledger_post(
        self,
        id: int,
        fiscal_id: str,
        include_running_totals: bool | None = None,
        fiscal_date_from: int | None = None,
        fiscal_date_to: int | None = None,
        show_reconciled: bool | None = None,
        reverse_date_sort: bool | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        self.calls.append(
            {
                "id": id,
                "fiscal_id": fiscal_id,
                "include_running_totals": include_running_totals,
                "fiscal_date_from": fiscal_date_from,
                "fiscal_date_to": fiscal_date_to,
                "show_reconciled": show_reconciled,
                "reverse_date_sort": reverse_date_sort,
                "show_deactivated": list_options_show_deactivated,
                "page": list_options_page,
                "page_size": list_options_page_size,
                "force_no_paging": list_options_force_no_paging,
            }
        )
        return {"Count": 1, "Entities": [{"Id": 1}]}


class _FakeLedgerAccountWorkflow:
    def get_by_account_number(self, account_number: int, *, show_deactivated: bool = True) -> dict[str, Any]:
        _ = show_deactivated
        return {
            "AccountNumber": account_number,
            "Id": f"104779-LedgerAccountIndexType_LedgerTag-{2252605348 + account_number}",
            "LedgerTagId": 2252605348,
        }

    def get_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        _ = kwargs
        return [
            {
                "AccountNumber": 1920,
                "Id": "104779-LedgerAccountIndexType_LedgerTag-2252605348",
                "LedgerTagId": 2252605348,
            }
        ]


class LedgerPostWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_finance = _FakeFinance()
        self.fake_ledger_account = _FakeLedgerAccountWorkflow()
        client = SimpleNamespace(finance=self.fake_finance)
        self.workflow = LedgerPostWorkflow(
            client,
            "104779",
            cast(Any, self.fake_ledger_account),
        )

    def test_get_entries_by_account_numeric_string(self) -> None:
        result = self.workflow.get_entries_by_account(
            "1920",
            "2025-01-01",
            "2025-12-31",
            include_running_totals=True,
            force_no_paging=False,
            page=0,
            page_size=100,
            show_deactivated=False,
        )

        self.assertEqual(result["Count"], 1)
        call = self.fake_finance.calls[-1]
        self.assertEqual(call["id"], 2252605348)
        self.assertEqual(call["fiscal_date_from"], 20089)
        self.assertEqual(call["fiscal_date_to"], 20453)
        self.assertEqual(call["include_running_totals"], True)

    def test_get_entries_by_account_accepts_ledger_account_id_string(self) -> None:
        self.workflow.get_entries_by_account(
            "104779-LedgerAccountIndexType_LedgerTag-2252605348",
            "2025-01-01",
            "2025-01-31",
        )

        self.assertEqual(self.fake_finance.calls[-1]["id"], 2252605348)

    def test_get_entries_by_account_unknown_identifier_raises(self) -> None:
        with self.assertRaises(LedgerPostError):
            self.workflow.get_entries_by_account("unknown", "2025-01-01", "2025-01-31")


if __name__ == "__main__":
    unittest.main()