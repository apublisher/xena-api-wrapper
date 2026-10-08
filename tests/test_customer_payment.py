import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from xena_api_wrappers.workflows.partner.partner_ledger import PartnerLedgerWorkflow, PartnerLedgerError


class CustomerPaymentTests(unittest.TestCase):
    def setUp(self):
        self.finance = Mock()
        self.order = Mock()
        self.workflow = PartnerLedgerWorkflow(SimpleNamespace(finance=self.finance, order=self.order), "42", Mock())
        self.workflow.get_posts = Mock(return_value={"Entities": [{"Id": 10, "PartnerId": 7}]})
        self.row = {"Id": 10, "PartnerId": 7, "RemainingAmount": "123.45", "CurrencyAbbreviation": "NOK"}
        self.workflow.get_unsettled_posts = Mock(return_value={"Entities": [self.row]})
        self.finance.api_ledger_tag__get_settlement_tag_get__api__fiscal_fiscal_id__ledger_tag__settlement_tag.return_value = {
            "Entities": [{"Id": 20, "Number": 1925, "Description": "Bank"}, {"Id": 21, "Number": 1900}]}
        self.finance.api_ledger_tag__get_currency_difference_tag_get__api__fiscal_fiscal_id__ledger_tag__currency_difference_tag.return_value = {
            "Entities": [{"Id": 22, "Number": None}]}
        self.args = dict(partner_id=7, partner_post_ids=[10], amount="123.45", payment_ledger_tag_id=20, pay_date="2026-10-07")

    def test_payload_and_send(self):
        payload = self.workflow.build_customer_payment_payload(**self.args)
        self.assertEqual(payload["payDate"], 20733)
        self.assertEqual(payload["partnerPostIds"], [10])
        self.assertEqual([p["Amount"] for p in payload["ledgerPosts"]], [123.45, 0, 0])
        self.assertEqual(payload["ledgerPosts"][0]["LedgerTagNumber"], 1925)
        self.assertNotIn("partialSettleId", payload)
        self.assertEqual(self.order.mock_calls, [])
        method = self.order.api_order__put_pay_put__api__fiscal_fiscal_id__order__pay
        method.return_value = ""
        self.assertEqual(self.workflow.pay_customer_invoices(**self.args), "")
        method.assert_called_once_with(pay_data=payload, fiscal_id="42")

    def test_rejects_amount_deviations_without_write(self):
        for value in ["123.44", "123.46", "0", "-1", "NaN", "Infinity", "1.001", "bad"]:
            with self.subTest(value=value), self.assertRaises(PartnerLedgerError):
                self.workflow.pay_customer_invoices(**dict(self.args, amount=value))
        self.assertEqual(self.order.mock_calls, [])

    def test_rejects_wrong_partner_closed_currency_and_missing_balance(self):
        for patch in [{"PartnerId": 8}, {"RemainingAmount": 0}, {"CurrencyAbbreviation": "EUR"}, {"RemainingAmount": None}]:
            original = self.row.copy()
            self.row.update(patch)
            with self.subTest(patch=patch), self.assertRaises(PartnerLedgerError):
                self.workflow.pay_customer_invoices(**self.args)
            self.row.clear()
            self.row.update(original)
        self.assertEqual(self.order.mock_calls, [])

    def test_rejects_non_invoice_duplicate_and_wrong_account(self):
        for patch in [{"partner_post_ids": [10, 10]}, {"partner_post_ids": [99]}, {"payment_ledger_tag_id": 99}]:
            with self.assertRaises(PartnerLedgerError):
                self.workflow.pay_customer_invoices(**dict(self.args, **patch))
        self.workflow.get_posts.return_value = {"Entities": []}
        with self.assertRaises(PartnerLedgerError):
            self.workflow.pay_customer_invoices(**self.args)
        self.assertEqual(self.order.mock_calls, [])

    def test_api_failure_is_not_retried(self):
        method = self.order.api_order__put_pay_put__api__fiscal_fiscal_id__order__pay
        method.side_effect = TimeoutError("uncertain outcome")
        with self.assertRaises(TimeoutError):
            self.workflow.pay_customer_invoices(**self.args)
        self.assertEqual(method.call_count, 1)

    def test_multiple_invoices_and_changed_balance(self):
        self.workflow.get_posts.return_value["Entities"].append({"Id": 11, "PartnerId": 7})
        self.workflow.get_unsettled_posts.return_value["Entities"].append(
            {"Id": 11, "PartnerId": 7, "RemainingAmount": "0.55", "CurrencyAbbreviation": "NOK"})
        args = dict(self.args, partner_post_ids=[10, 11], amount="124.00")
        self.assertEqual(self.workflow.build_customer_payment_payload(**args)["partnerPostIds"], [10, 11])
        self.row["RemainingAmount"] = "100"
        with self.assertRaises(PartnerLedgerError):
            self.workflow.pay_customer_invoices(**args)
        self.assertEqual(self.order.mock_calls, [])
