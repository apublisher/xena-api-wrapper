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

    def api_voucher__get_transactions_by_voucher_get__api__fiscal_fiscal_id__voucher_id__transaction(
        self,
        id: int,
        fiscal_id: str,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        self.calls.append(
            {
                "op": "voucher_transaction",
                "id": id,
                "fiscal_id": fiscal_id,
                "show_deactivated": list_options_show_deactivated,
                "page": list_options_page,
                "page_size": list_options_page_size,
                "force_no_paging": list_options_force_no_paging,
            }
        )
        return {"Count": 1, "Entities": [{"Id": 3020754631, "VoucherId": id}]}

    def api_transaction__get_ledger_post_by_transaction_get__api__fiscal_fiscal_id__transaction_id__ledger_post(
        self,
        id: int,
        fiscal_id: str,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
        _ = fiscal_id
        return {"Count": 2, "Entities": [{"TransactionId": id, "Type": "Ledger"}]}

    def api_transaction__get_partner_post_by_transaction_get__api__fiscal_fiscal_id__transaction_id__partner_post(
        self,
        id: int,
        fiscal_id: str,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
        _ = fiscal_id
        return {"Count": 0, "Entities": []}

    def api_transaction__get_article_post_by_transaction_get__api__fiscal_fiscal_id__transaction_id__article_post(
        self,
        id: int,
        fiscal_id: str,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
        _ = fiscal_id
        return {"Count": 0, "Entities": []}


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

    def test_get_transactions_by_voucher(self) -> None:
        payload = self.workflow.get_transactions_by_voucher(3020754351)
        self.assertEqual(payload["Count"], 1)
        self.assertEqual(payload["Entities"][0]["Id"], 3020754631)

    def test_get_posting_details_returns_all_post_types(self) -> None:
        payload = self.workflow.get_posting_details(3020754631)

        self.assertEqual(payload["transaction_id"], 3020754631)
        self.assertEqual(payload["ledger_post"]["Count"], 2)
        self.assertEqual(payload["partner_post"]["Count"], 0)
        self.assertEqual(payload["article_post"]["Count"], 0)

    def test_get_posting_details_by_voucher(self) -> None:
        payload = self.workflow.get_posting_details_by_voucher(3020754351)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["transaction_id"], 3020754631)


if __name__ == "__main__":
    unittest.main()