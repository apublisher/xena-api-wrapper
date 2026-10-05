from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, patch

from xena_api_wrappers.workflows.finance.ledger_group_data import LedgerGroupDataWorkflow
from xena_api_wrappers.workflows.finance.ledger_group_data_detail import LedgerGroupDataDetailWorkflow
from xena_api_wrappers.workflows.finance.transaction import TransactionWorkflow, VoucherNotFoundError
from xena_api_wrappers.workflows.partner.partner_ledger import PartnerLedgerError, PartnerLedgerWorkflow
from xena_api_wrappers.workflows.utils import FiscalPeriodWorkflow
from xena_api_wrappers.workflows.utils.ledger_account import LedgerAccountError, LedgerAccountWorkflow


class _ConvertedPayload:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def to_dict(self) -> object:
        return self.payload


class EntityExtractionTests(unittest.TestCase):
    def test_transaction_and_partner_preserve_dict_rows_and_generated_dto_support(self) -> None:
        row: dict[str, Any] = {"Id": 1, "UnmodeledField": "preserved"}
        envelope: dict[str, Any] = {"Entities": [row, None, "invalid", 5]}
        transaction = TransactionWorkflow(object(), "104779")
        finance = Mock()
        partner = PartnerLedgerWorkflow(
            SimpleNamespace(finance=finance), "104779", FiscalPeriodWorkflow(object(), "104779")
        )
        for payload in (envelope, _ConvertedPayload(envelope)):
            with self.subTest(payload=type(payload).__name__):
                with patch.object(transaction, "get_vouchers", return_value=payload):
                    self.assertIs(transaction.get_voucher_by_number(1), row)
                finance.api_ledger_tag__get_currency_difference_tag_get__api__fiscal_fiscal_id__ledger_tag__currency_difference_tag.return_value = payload
                self.assertIs(partner.get_currency_difference_tag(), row)

    def test_transaction_and_partner_preserve_not_found_errors_for_invalid_shapes(self) -> None:
        payloads: list[object] = [None, [], {}, {"Entities": {}}, _ConvertedPayload(None)]
        transaction = TransactionWorkflow(object(), "104779")
        finance = Mock()
        partner = PartnerLedgerWorkflow(
            SimpleNamespace(finance=finance), "104779", FiscalPeriodWorkflow(object(), "104779")
        )
        for payload in payloads:
            with self.subTest(payload=repr(payload)):
                with patch.object(transaction, "get_vouchers", return_value=payload):
                    with self.assertRaises(VoucherNotFoundError):
                        transaction.get_voucher_by_number(1)
                finance.api_ledger_tag__get_currency_difference_tag_get__api__fiscal_fiscal_id__ledger_tag__currency_difference_tag.return_value = payload
                with self.assertRaisesRegex(PartnerLedgerError, "Currency difference tag not found"):
                    partner.get_currency_difference_tag()

    def test_ledger_group_detail_preserves_dict_rows_and_generated_dto_support(self) -> None:
        row: dict[str, Any] = {"AccountNumber": 1280, "UnmodeledField": "preserved"}
        envelope: dict[str, Any] = {"Entities": [row, None, "invalid", 5]}
        groups = LedgerGroupDataWorkflow(object(), "104779")
        workflow = LedgerGroupDataDetailWorkflow(
            object(), "104779", _ledger_group_data_workflow=groups
        )
        summary: dict[str, Any] = {"Assets": {"Entities": [{"Group": "Assets"}]}}
        for payload in (envelope, _ConvertedPayload(envelope)):
            with self.subTest(payload=type(payload).__name__):
                with patch.object(groups, "get_all_groups", return_value=summary):
                    with patch.object(workflow, "get_by_summary_group", return_value=payload):
                        result = workflow.get_all_accounts(
                            date_from=20089, date_to=20453, fiscal_period_id=1
                        )
                self.assertEqual(result, [row])
                self.assertIs(result[0], row)

    def test_ledger_group_detail_preserves_empty_fallback_for_invalid_shapes(self) -> None:
        groups = LedgerGroupDataWorkflow(object(), "104779")
        workflow = LedgerGroupDataDetailWorkflow(
            object(), "104779", _ledger_group_data_workflow=groups
        )
        summary: dict[str, Any] = {"Assets": {"Entities": [{"Group": "Assets"}]}}
        payloads: list[object] = [None, [], {}, {"Entities": {}}, _ConvertedPayload(None)]
        for payload in payloads:
            with self.subTest(payload=repr(payload)):
                with patch.object(groups, "get_all_groups", return_value=summary):
                    with patch.object(workflow, "get_by_summary_group", return_value=payload):
                        self.assertEqual(
                            workflow.get_all_accounts(
                                date_from=20089, date_to=20453, fiscal_period_id=1
                            ),
                            [],
                        )

    def test_ledger_account_preserves_dict_rows_and_generated_dto_support(self) -> None:
        row: dict[str, Any] = {"AccountNumber": 1280, "UnmodeledField": "preserved"}
        envelope: dict[str, Any] = {"Entities": [row, None, "invalid", 5]}
        workflow = LedgerAccountWorkflow(object(), "104779")
        for payload in (envelope, _ConvertedPayload(envelope)):
            with self.subTest(payload=type(payload).__name__):
                with patch.object(workflow, "get_all", return_value=payload):
                    result = workflow.get_entities()
                self.assertEqual(result, [row])
                self.assertIs(result[0], row)

    def test_ledger_account_preserves_errors_for_invalid_shapes(self) -> None:
        workflow = LedgerAccountWorkflow(object(), "104779")
        payloads: list[object] = [None, [], {}, {"Entities": {}}, _ConvertedPayload(None)]
        for payload in payloads:
            with self.subTest(payload=repr(payload)):
                with patch.object(workflow, "get_all", return_value=payload):
                    with self.assertRaisesRegex(LedgerAccountError, "Unexpected LedgerAccount response shape"):
                        workflow.get_entities()


if __name__ == "__main__":
    unittest.main()
