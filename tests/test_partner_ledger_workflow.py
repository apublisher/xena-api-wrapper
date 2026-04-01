from __future__ import annotations

import unittest
from datetime import date
from types import SimpleNamespace
from typing import Any, cast

from xena_api_wrappers.workflows.partner.partner_ledger import PartnerLedgerError, PartnerLedgerWorkflow


class _FakeFinance:
    def __init__(self) -> None:
        self.last_call: dict[str, Any] | None = None
        self.last_unsettled_call: dict[str, Any] | None = None
        self.last_currency_tag_call: dict[str, Any] | None = None
        self.unsettled_entities: list[dict[str, Any]] = [
            {
                "Id": 3020754398,
                "PartnerId": 2247873100,
                "CurrencyAbbreviation": "NOK",
                "RemainingAmount": 2603.12,
                "Amount": 2603.12,
            },
            {
                "Id": 2900254804,
                "PartnerId": 2247873100,
                "CurrencyAbbreviation": "NOK",
                "RemainingAmount": -2603.12,
                "Amount": -2603.12,
            },
        ]

    def api_transaction__get_partner_posts_by_partner_get__api__fiscal_fiscal_id__transaction__partner_id__partner_post(
        self,
        id: int,
        fiscal_id: str,
        context_type: str | None = None,
        fiscal_date_from: int | None = None,
        fiscal_date_to: int | None = None,
        is_settled: bool | None = None,
        post_type: str | None = None,
        is_parked: bool | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        self.last_call = {
            "id": id,
            "fiscal_id": fiscal_id,
            "context_type": context_type,
            "fiscal_date_from": fiscal_date_from,
            "fiscal_date_to": fiscal_date_to,
            "is_settled": is_settled,
            "post_type": post_type,
            "is_parked": is_parked,
            "show_deactivated": list_options_show_deactivated,
            "page": list_options_page,
            "page_size": list_options_page_size,
            "force_no_paging": list_options_force_no_paging,
        }
        return {"Count": 1, "Entities": [{"PartnerId": id, "ContextType": context_type}]}

    def api_payment__get_unsettled_partner_post_get__api__fiscal_fiscal_id__partner_id__unsettled_post(
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
        self.last_unsettled_call = {
            "id": id,
            "fiscal_id": fiscal_id,
            "show_deactivated": list_options_show_deactivated,
            "page": list_options_page,
            "page_size": list_options_page_size,
            "force_no_paging": list_options_force_no_paging,
        }
        return {"Count": len(self.unsettled_entities), "Entities": list(self.unsettled_entities)}

    def api_ledger_tag__get_currency_difference_tag_get__api__fiscal_fiscal_id__ledger_tag__currency_difference_tag(
        self,
        fiscal_id: str,
        include_default: bool | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        _ = include_default
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        self.last_currency_tag_call = {
            "fiscal_id": fiscal_id,
            "force_no_paging": list_options_force_no_paging,
        }
        return {
            "Count": 1,
            "Entities": [
                {
                    "Id": 2180183781,
                    "Number": None,
                    "LedgerTagNumber": None,
                    "Description": "Valutakursdifferanse",
                }
            ],
        }


class _FakeOrder:
    def __init__(self) -> None:
        self.last_pay_data: dict[str, Any] | None = None
        self.last_pay_fiscal_id: str | None = None

    def api_order__put_pay_put__api__fiscal_fiscal_id__order__pay(
        self,
        pay_data: dict[str, Any],
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        self.last_pay_data = pay_data
        self.last_pay_fiscal_id = fiscal_id
        return {"ok": True, "pay_data": pay_data}


class _FakeFiscalPeriodWorkflow:
    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        self.last_year: int | str | None = None
        self.payload = payload or {
            "Id": 2586516686,
            "Description": "2025",
            "FiscalPeriodStartDays": 20089,
            "FiscalPeriodEndDays": 20453,
        }

    def get_by_year(self, year: int | str) -> dict[str, Any]:
        self.last_year = year
        return dict(self.payload)


class PartnerLedgerWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_finance = _FakeFinance()
        self.fake_order = _FakeOrder()
        self.fake_period = _FakeFiscalPeriodWorkflow()
        client = SimpleNamespace(finance=self.fake_finance, order=self.fake_order)
        self.workflow = PartnerLedgerWorkflow(client, "104779", self.fake_period)

    def test_get_posts_forwards_filters_and_converts_dates(self) -> None:
        payload = self.workflow.get_posts(
            2247873100,
            context_type="ContextType_Customer",
            fiscal_date_from=date(2025, 1, 1),
            fiscal_date_to="2025-12-31",
            is_settled=False,
            post_type="PartnerPostType_CustomerInvoice",
            is_parked=True,
            show_deactivated=False,
            page=2,
            page_size=50,
            force_no_paging=False,
        )

        self.assertEqual(payload["Count"], 1)
        self.assertIsNotNone(self.fake_finance.last_call)
        call = cast(dict[str, Any], self.fake_finance.last_call)
        self.assertEqual(call["id"], 2247873100)
        self.assertEqual(call["context_type"], "ContextType_Customer")
        self.assertEqual(call["fiscal_date_from"], 20089)
        self.assertEqual(call["fiscal_date_to"], 20453)
        self.assertEqual(call["is_settled"], False)
        self.assertEqual(call["post_type"], "PartnerPostType_CustomerInvoice")
        self.assertEqual(call["is_parked"], True)
        self.assertEqual(call["page"], 2)
        self.assertEqual(call["page_size"], 50)

    def test_get_posts_for_year_uses_period_bounds(self) -> None:
        self.workflow.get_posts_for_year(
            2247873100,
            2025,
            context_type="ContextType_Customer",
            is_settled=None,
            post_type="PartnerPostType_CustomerPayment",
            is_parked=None,
        )

        self.assertEqual(self.fake_period.last_year, 2025)
        self.assertIsNotNone(self.fake_finance.last_call)
        call = cast(dict[str, Any], self.fake_finance.last_call)
        self.assertEqual(call["fiscal_date_from"], 20089)
        self.assertEqual(call["fiscal_date_to"], 20453)
        self.assertEqual(call["post_type"], "PartnerPostType_CustomerPayment")

    def test_get_posts_rejects_fiscal_period_id_argument(self) -> None:
        with self.assertRaises(PartnerLedgerError):
            self.workflow.get_posts(2247873100, fiscal_period_id=2586516686)

    def test_get_posts_for_year_raises_on_invalid_period_shape(self) -> None:
        bad_period = _FakeFiscalPeriodWorkflow(payload={"Id": "oops", "FiscalPeriodStartDays": 1, "FiscalPeriodEndDays": 2})
        workflow = PartnerLedgerWorkflow(SimpleNamespace(finance=self.fake_finance), "104779", bad_period)

        with self.assertRaises(PartnerLedgerError):
            workflow.get_posts_for_year(2247873100, 2025)

    def test_context_convenience_methods(self) -> None:
        self.workflow.get_customer_posts(2247873100)
        self.assertIsNotNone(self.fake_finance.last_call)
        self.assertEqual(cast(dict[str, Any], self.fake_finance.last_call)["context_type"], "ContextType_Customer")

        self.workflow.get_supplier_posts(2247873100)
        self.assertIsNotNone(self.fake_finance.last_call)
        self.assertEqual(cast(dict[str, Any], self.fake_finance.last_call)["context_type"], "ContextType_Supplier")

    def test_aliases_map_to_xena_enums(self) -> None:
        self.workflow.get_posts(
            2247873100,
            context_type="customer",
            post_type="invoice",
        )

        self.assertIsNotNone(self.fake_finance.last_call)
        call = cast(dict[str, Any], self.fake_finance.last_call)
        self.assertEqual(call["context_type"], "ContextType_Customer")
        self.assertEqual(call["post_type"], "PartnerPostType_CustomerInvoice")

    def test_aliases_keep_explicit_enum_values(self) -> None:
        self.workflow.get_posts(
            2247873100,
            context_type="ContextType_Supplier",
            post_type="PartnerPostType_SupplierPayment",
        )

        self.assertIsNotNone(self.fake_finance.last_call)
        call = cast(dict[str, Any], self.fake_finance.last_call)
        self.assertEqual(call["context_type"], "ContextType_Supplier")
        self.assertEqual(call["post_type"], "PartnerPostType_SupplierPayment")

    def test_build_settlement_payload_safe(self) -> None:
        payload = self.workflow.build_settlement_payload_safe(
            2247873100,
            [3020754398, 2900254804],
            pay_date="2025-12-19",
        )
        self.assertEqual(payload["partnerPostIds"], [3020754398, 2900254804])
        self.assertEqual(payload["currencyAbbreviation"], "NOK")
        self.assertEqual(payload["partialSettleId"], 3020754398)
        self.assertEqual(payload["ledgerPosts"][0]["LedgerTagId"], 2180183781)
        self.assertEqual(payload["ledgerPosts"][0]["Amount"], 0)

    def test_build_settlement_payload_safe_rejects_unbalanced_sum(self) -> None:
        self.fake_finance.unsettled_entities = [
            {
                "Id": 3020754398,
                "PartnerId": 2247873100,
                "CurrencyAbbreviation": "NOK",
                "RemainingAmount": 100,
            },
            {
                "Id": 2900254804,
                "PartnerId": 2247873100,
                "CurrencyAbbreviation": "NOK",
                "RemainingAmount": -99,
            },
        ]

        with self.assertRaises(PartnerLedgerError):
            self.workflow.build_settlement_payload_safe(
                2247873100,
                [3020754398, 2900254804],
                pay_date="2025-12-19",
            )

    def test_settle_partner_posts_safe_calls_order_pay(self) -> None:
        response = self.workflow.settle_partner_posts_safe(
            2247873100,
            [3020754398, 2900254804],
            pay_date="2025-12-19",
        )
        self.assertEqual(response["ok"], True)
        self.assertIsNotNone(self.fake_order.last_pay_data)
        self.assertEqual(self.fake_order.last_pay_fiscal_id, "104779")

    def test_build_settlement_payload_safe_rejects_unknown_partner_post(self) -> None:
        with self.assertRaises(PartnerLedgerError):
            self.workflow.build_settlement_payload_safe(
                2247873100,
                [3020754398, 9999999999],
                pay_date="2025-12-19",
            )


if __name__ == "__main__":
    unittest.main()
