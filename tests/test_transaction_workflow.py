from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.finance.transaction import (
    TransactionWorkflow,
    VoucherAmbiguousError,
    VoucherNotFoundError,
)


class _FakeFinance:
    def api_voucher__get_get__api__fiscal_fiscal_id__voucher(
        self,
        fiscal_id: str,
        options_query_string: str | None = None,
        options_responsible_id: int | None = None,
        options_voucher_number_from: int | None = None,
        options_voucher_number_to: int | None = None,
        options_fiscal_date_from: int | None = None,
        options_fiscal_date_to: int | None = None,
        options_amount_from: float | None = None,
        options_amount_to: float | None = None,
        options_show_deactivated: bool | None = None,
        options_page: int | None = None,
        options_page_size: int | None = None,
        options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        _ = fiscal_id
        _ = options_query_string
        _ = options_responsible_id
        _ = options_fiscal_date_from
        _ = options_fiscal_date_to
        _ = options_amount_from
        _ = options_amount_to
        _ = options_show_deactivated
        _ = options_page
        _ = options_page_size
        _ = options_force_no_paging

        if options_voucher_number_from == 99999 and options_voucher_number_to == 99999:
            return {"Count": 0, "Entities": []}
        if options_voucher_number_from == 11111 and options_voucher_number_to == 11111:
            return {
                "Count": 2,
                "Entities": [
                    {"Id": 1, "VoucherNumber": 11111},
                    {"Id": 2, "VoucherNumber": 11111},
                ],
            }

        return {
            "Count": 1,
            "Entities": [
                {"Id": 3020754351, "VoucherNumber": options_voucher_number_from},
            ],
        }

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
        _ = fiscal_id
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
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
        _ = fiscal_id
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
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
        _ = fiscal_id
        _ = id
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
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
        _ = fiscal_id
        _ = id
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
        return {"Count": 0, "Entities": []}


class TransactionWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        client = SimpleNamespace(finance=_FakeFinance())
        self.workflow = TransactionWorkflow(client, "104779")

    def test_get_transactions_by_voucher(self) -> None:
        payload = self.workflow.get_transactions_by_voucher(3020754351)
        self.assertEqual(payload["Count"], 1)
        self.assertEqual(payload["Entities"][0]["Id"], 3020754631)

    def test_get_voucher_by_number(self) -> None:
        voucher = self.workflow.get_voucher_by_number(15316)
        self.assertEqual(voucher["Id"], 3020754351)

    def test_get_voucher_id_by_number(self) -> None:
        voucher_id = self.workflow.get_voucher_id_by_number(15316)
        self.assertEqual(voucher_id, 3020754351)

    def test_get_transactions_by_voucher_number(self) -> None:
        payload = self.workflow.get_transactions_by_voucher_number(15316)
        self.assertEqual(payload["Count"], 1)
        self.assertEqual(payload["Entities"][0]["VoucherId"], 3020754351)

    def test_get_voucher_by_number_not_found(self) -> None:
        with self.assertRaises(VoucherNotFoundError):
            self.workflow.get_voucher_by_number(99999)

    def test_get_voucher_by_number_ambiguous(self) -> None:
        with self.assertRaises(VoucherAmbiguousError):
            self.workflow.get_voucher_by_number(11111)

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

    def test_get_posting_details_by_voucher_number(self) -> None:
        payload = self.workflow.get_posting_details_by_voucher_number(15316)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["transaction_id"], 3020754631)


if __name__ == "__main__":
    unittest.main()