from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.utils.ledger_account import (
    LedgerAccountAmbiguousError,
    LedgerAccountNotFoundError,
    LedgerAccountWorkflow,
)


class _FakeFinance:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def api_ledger_account__get_list_get__api__fiscal_fiscal_id__ledger_account(
        self,
        fiscal_id: str,
        ledger_account: str | None = None,
        query_string: str | None = None,
        include_default: bool | None = None,
        exclude_vats: bool | None = None,
        exclude_article_groups: bool | None = None,
        exclude_ledger_tags: bool | None = None,
        exclude_system_accounts: bool | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        _ = ledger_account
        _ = query_string
        _ = include_default
        _ = exclude_vats
        _ = exclude_article_groups
        _ = exclude_ledger_tags
        _ = exclude_system_accounts
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
        self.calls.append({"fiscal_id": fiscal_id})
        return {
            "Count": 5,
            "Entities": [
                {"Id": "id-950", "AccountNumber": 950, "Description": "outside"},
                {"Id": "id-1280", "AccountNumber": 1280, "Description": "balance"},
                {"Id": "id-1920", "AccountNumber": 1920, "Description": "bank"},
                {"Id": "id-3001", "AccountNumber": 3001, "Description": "result"},
                {"Id": "id-10000", "AccountNumber": 10000, "Description": "outside"},
            ],
        }


class LedgerAccountWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_finance = _FakeFinance()
        client = SimpleNamespace(finance=self.fake_finance)
        self.workflow = LedgerAccountWorkflow(client, "104779")

    def test_get_all_accounts_filters_1000_to_9999(self) -> None:
        rows = self.workflow.get_all_accounts()
        self.assertEqual([r["AccountNumber"] for r in rows], [1280, 1920, 3001])

    def test_get_balance_accounts_filters_1000_to_2999(self) -> None:
        rows = self.workflow.get_balance_accounts()
        self.assertEqual([r["AccountNumber"] for r in rows], [1280, 1920])

    def test_get_result_accounts_filters_3000_to_9999(self) -> None:
        rows = self.workflow.get_result_accounts()
        self.assertEqual([r["AccountNumber"] for r in rows], [3001])

    def test_get_by_account_number_and_get_id(self) -> None:
        row = self.workflow.get_by_account_number(1920)
        self.assertEqual(row["Description"], "bank")
        self.assertEqual(self.workflow.get_id_by_account_number(1920), "id-1920")

    def test_get_by_account_number_not_found(self) -> None:
        with self.assertRaises(LedgerAccountNotFoundError):
            self.workflow.get_by_account_number(7777)

    def test_get_by_account_number_ambiguous(self) -> None:
        original = self.fake_finance.api_ledger_account__get_list_get__api__fiscal_fiscal_id__ledger_account

        def _dup(*args: Any, **kwargs: Any) -> dict[str, Any]:
            data = original(*args, **kwargs)
            data["Entities"].append({"Id": "dup-1920", "AccountNumber": 1920, "Description": "dup"})
            return data

        self.fake_finance.api_ledger_account__get_list_get__api__fiscal_fiscal_id__ledger_account = _dup  # type: ignore[method-assign]

        with self.assertRaises(LedgerAccountAmbiguousError):
            self.workflow.get_by_account_number(1920)


if __name__ == "__main__":
    unittest.main()