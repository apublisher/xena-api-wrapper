from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.order.order_write import (
    OrderDistributionError,
    OrderWriteHydrationError,
    OrderWriteWorkflow,
)


class _FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict[str, Any]:
        return dict(self._payload)


class _FakeSession:
    def __init__(self) -> None:
        self.last_post_url: str | None = None
        self.last_post_json: dict[str, Any] | None = None

    def post(self, url: str, json: dict[str, Any] | None = None, **kwargs: Any) -> _FakeResponse:
        _ = kwargs
        self.last_post_url = url
        self.last_post_json = dict(json) if isinstance(json, dict) else None
        return _FakeResponse({"Success": True})


class _FakeOrderApi:
    def __init__(self) -> None:
        self.base_url = "https://my.xena.biz"
        self.session = _FakeSession()
        self.last_create_data: dict[str, Any] | None = None
        self.last_update_data: dict[str, Any] | None = None
        self.last_update_id: str | None = None
        self.last_offer_data: dict[str, Any] | None = None
        self.last_offer_id: int | None = None
        self.last_confirm_data: dict[str, Any] | None = None
        self.last_confirm_id: int | None = None
        self.last_deliver_data: dict[str, Any] | None = None
        self.last_deliver_id: int | None = None
        self.last_bookkeep_data: dict[str, Any] | None = None
        self.last_bookkeep_id: int | None = None
        self.last_delete_id: int | None = None
        self.created_lines: list[dict[str, Any]] = []
        self.last_send_electronic_data: dict[str, Any] | None = None
        self.journal_entities: list[dict[str, Any]] = [
            {
                "Id": 3038320382,
                "EntryType": "OrderJournalEntry",
                "DocumentId": 3038297310,
                "OrderInvoiceTransactionId": 3038185190,
                "VoucherNumber": 100277,
            }
        ]

    def api_order__post_post__api__fiscal_fiscal_id__order(self, create_data: dict[str, Any], fiscal_id: str, **kwargs: Any) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_create_data = dict(create_data)
        return {"Id": 4001, "Version": 1, **create_data}

    def api_order__put_put__api__fiscal_fiscal_id__order_id(
        self,
        order_dto: dict[str, Any],
        fiscal_id: str,
        id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_update_data = dict(order_dto)
        self.last_update_id = id
        return {"Id": int(id), **order_dto}

    def api_order__put_offer_put__api__fiscal_fiscal_id__order_id__offer(
        self,
        id: int,
        create_data: dict[str, Any],
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_offer_id = id
        self.last_offer_data = dict(create_data)
        return {"Id": id, "State": "Offered"}

    def api_order__put_confirmation_put__api__fiscal_fiscal_id__order_id__confirmation(
        self,
        id: int,
        create_data: dict[str, Any],
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_confirm_id = id
        self.last_confirm_data = dict(create_data)
        return {"Id": id, "State": "Confirmed"}

    def api_order__put_deliver_put__api__fiscal_fiscal_id__order_id__deliver(
        self,
        id: int,
        deliver_data: dict[str, Any],
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_deliver_id = id
        self.last_deliver_data = dict(deliver_data)
        return {"Id": id, "State": "Delivered"}

    def api_order__put_bookkeep_put__api__fiscal_fiscal_id__order_id__bookkeep(
        self,
        id: int,
        bookkeep_data: dict[str, Any],
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_bookkeep_id = id
        self.last_bookkeep_data = dict(bookkeep_data)
        return {"Id": id, "State": "Invoiced"}

    def api_order__delete_delete__api__fiscal_fiscal_id__order_id(self, id: int, fiscal_id: str, **kwargs: Any) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_delete_id = id
        return {"Deleted": id, "Success": True}

    def api_order_task__get_by_order_get__api__fiscal_fiscal_id__order_id__order_task(
        self,
        id: int,
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (id, fiscal_id, kwargs)
        return {"Entities": [{"Id": 9001}]}

    def api_order_line__post_post__api__fiscal_fiscal_id__order_line(
        self,
        line_dto: dict[str, Any],
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.created_lines.append(dict(line_dto))
        return {"Id": 7000 + len(self.created_lines), **line_dto}

    def api_order__get_order_journal_get__api__fiscal_fiscal_id__order_id__journal(
        self,
        id: int,
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (id, fiscal_id, kwargs)
        return {"Count": len(self.journal_entities), "Entities": list(self.journal_entities)}

    def api_order__get_default_electronic_invoice_data_get__api__fiscal_fiscal_id__order__default_electronic_invoice_data(
        self,
        journal_ids: list[Any],
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (journal_ids, fiscal_id, kwargs)
        return {
            "Count": 1,
            "Entities": [
                {
                    "OrderInvoiceTransactionId": 3038185190,
                    "PartnerName": "Gj System Da",
                    "PartnerAccountNumber": 10010,
                    "InvoiceNumber": 100277,
                    "GLNNumber": "995361108",
                    "RecipientAddress": "995361108",
                    "OrgNumber": "",
                    "PartyIdentifications": None,
                }
            ],
        }

    def api_order__put_send_electronic_invoices_put__api__fiscal_fiscal_id__order__invoice__send_electronic_invoice(
        self,
        invoice_data: dict[str, Any],
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_send_electronic_data = dict(invoice_data)
        return {"Success": True}


class _FakePartnerWorkflow:
    def get_by_id(self, partner_id: int) -> dict[str, Any]:
        _ = partner_id
        return {
            "Id": 2251919792,
            "AccountNumber": 10010,
            "LongDescription": "10010 - Gj System Da",
            "ShortDescription": "10010",
            "PartnerCustomerContextInvoiceMail": "invoice@gj-system.no",
            "PhoneNumber": "12345678",
            "Attention": "Attn",
            "Note": "Partner note",
            "GLNNumber": "995361108",
            "PartnerType": "xena_partnertype_company",
            "IsVatExcept": False,
            "Address": {
                "Name": "Gj System Da",
                "Street": "Espelandsvegen 27",
                "Zip": "5258",
                "City": "BLOMSTERDALEN",
                "CountryName": "NO",
                "CountryDisplayName": "Norge",
                "PlaceName": "",
                "Description": "Gj System Da - Espelandsvegen 27, 5258 BLOMSTERDALEN",
            },
        }

    def get_by_account_number(self, account_number: int) -> dict[str, Any]:
        _ = account_number
        return self.get_by_id(2251919792)


class _FakeArticleWorkflow:
    def get_by_id(self, article_id: int) -> dict[str, Any]:
        _ = article_id
        return {
            "Id": 2188837687,
            "ArticleNumber": "1020",
            "Description": "Secura KS - Kvalitetsstyring",
            "SalesSetup": {
                "DefaultQuantity": 1,
                "DefaultUnitId": 10,
                "PriceEach": 750,
            },
        }

    def get_by_number(self, article_number: str) -> dict[str, Any]:
        _ = article_number
        return self.get_by_id(2188837687)


class _FakePartnerWorkflowMissingEmailAndGln(_FakePartnerWorkflow):
    def get_by_id(self, partner_id: int) -> dict[str, Any]:
        partner = super().get_by_id(partner_id)
        partner["PartnerCustomerContextInvoiceMail"] = None
        partner["GLNNumber"] = ""
        return partner


class OrderWriteWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = _FakeOrderApi()
        self.workflow = OrderWriteWorkflow(SimpleNamespace(order=self.api), "104779")

    def test_create_and_update(self) -> None:
        created = self.workflow.create({"PartnerId": 9001, "ContextType": "ContextType_Customer"})
        self.assertEqual(created["Id"], 4001)
        assert self.api.last_create_data is not None
        self.assertEqual(self.api.last_create_data["PartnerId"], 9001)

        updated = self.workflow.update(4001, {"Description": "Updated", "Version": 1})
        self.assertEqual(updated["Id"], 4001)
        self.assertEqual(self.api.last_update_id, "4001")

    def test_hydrator_supports_setters_and_submission(self) -> None:
        hydrator = self.workflow.new_hydrator()
        hydrator.set_customer(9002)
        hydrator.set_dates(order_date="2026-04-05", due_date="2026-05-05")
        hydrator.set_field("Description", "Invoice draft")
        hydrator.set_article(article_id=3038211807, quantity=2, unit_net_price=350)
        hydrator.setArticle(article_number=2500, quantity=1, description="Service article")

        dto = hydrator.to_dict()
        self.assertEqual(dto["PartnerId"], 9002)
        self.assertEqual(dto["ContextType"], "ContextType_Customer")
        self.assertEqual(len(dto["OrderTaskLines"]), 2)

        created = self.workflow.create_hydrated(hydrator)
        self.assertEqual(created["Id"], 4001)
        assert self.api.last_create_data is not None
        self.assertEqual(self.api.last_create_data["PartnerId"], 9002)
        self.assertEqual(len(self.api.last_create_data["OrderTaskLines"]), 2)

        hydrator.set_field("Version", 1)
        updated = self.workflow.update_hydrated(4001, hydrator)
        self.assertEqual(updated["Id"], 4001)
        assert self.api.last_update_data is not None
        self.assertEqual(self.api.last_update_data["Version"], 1)

    def test_hydrator_supports_raw_hydrate_and_article_errors(self) -> None:
        hydrator = self.workflow.new_hydrator(
            {"PartnerId": 42, "OrderTaskLines": [{"ArticleNumber": "1000", "Quantity": 1}]}
        )
        self.assertEqual(hydrator.get_field("PartnerId"), 42)
        self.assertEqual(len(hydrator.get_articles()), 1)

        hydrator.hydrate({"Description": "Merged"})
        self.assertEqual(hydrator.get_field("Description"), "Merged")

        hydrator.hydrate({"PartnerId": 99}, replace=True)
        self.assertEqual(hydrator.to_dict(), {"PartnerId": 99})

        with self.assertRaises(OrderWriteHydrationError):
            hydrator.set_article(quantity=1)

    def test_hydrator_can_manipulate_full_order_state(self) -> None:
        hydrator = self.workflow.new_hydrator({"OrderTaskLines": []})

        hydrator.set_customer(2251919792)
        hydrator.set_customer_fields(
            account_number=10010,
            name="Gj System Da",
            gln_number="995361108",
            invoice_email="invoice@example.test",
            our_reference="Jarle",
            your_reference="Gunnar",
        )
        hydrator.set_order_date("2026-04-05")
        hydrator.set_due_date("2026-04-13")
        hydrator.set_notes(internal_note="Internal", delivery_note="Leave at reception")
        hydrator.set_delivery_contact(
            contact_name="Gunnar",
            phone="12345678",
            email="delivery@example.test",
        )
        hydrator.set_delivery_address(
            name="Gj System Da",
            street="Espelandsvegen 27",
            zip_code="5258",
            city="BLOMSTERDALEN",
            country_display_name="Norge",
        )

        hydrator.add_order_line({"ArticleId": 2188837687, "Quantity": 1})
        hydrator.edit_order_line(0, Quantity=2, Description="Line 1")
        hydrator.set_order_line(0, {"ArticleId": 2188837687, "Quantity": 3})
        removed = hydrator.remove_order_line(0)

        self.assertEqual(removed["Quantity"], 3)
        self.assertEqual(hydrator.get_order_lines(), [])

        customer_fields = hydrator.get_customer_fields()
        self.assertEqual(customer_fields["PartnerId"], 2251919792)
        self.assertEqual(customer_fields["GLNNumber"], "995361108")

        dto = hydrator.to_dict()
        self.assertEqual(dto["PartnerName"], "Gj System Da")
        self.assertEqual(dto["DeliveryAddress"]["Zip"], "5258")
        self.assertEqual(dto["DeliveryContactName"], "Gunnar")

    def test_hydrator_line_index_validation(self) -> None:
        hydrator = self.workflow.new_hydrator({"OrderTaskLines": []})
        with self.assertRaises(OrderWriteHydrationError):
            hydrator.edit_order_line(0, Quantity=1)

        with self.assertRaises(OrderWriteHydrationError):
            hydrator.remove_order_line(0)

    def test_hydrator_order_line_pricing_controls_totals(self) -> None:
        hydrator = self.workflow.new_hydrator(
            {
                "OrderTaskLines": [
                    {
                        "Quantity": 3,
                        "PriceEach": 750,
                        "Totals": {
                            "PriceNettTotal": 2250,
                            "DiscountTotalPct": 0,
                            "DiscountTotalRatio": 0,
                            "DiscountTotal": 0,
                        },
                    }
                ]
            }
        )

        hydrator.set_order_line_price(0, price_each=900, quantity=1)
        line = hydrator.get_order_lines()[0]
        self.assertEqual(line["PriceEach"], 900.0)
        self.assertEqual(line["Quantity"], 1.0)
        # Price-only update leaves totals unchanged unless discount/net is set explicitly.
        self.assertEqual(line["Totals"]["PriceNettTotal"], 2250)

        hydrator.set_order_line_pricing(0, price_each=1000, quantity=1, discount_pct=10)
        line2 = hydrator.get_order_lines()[0]
        self.assertEqual(line2["Totals"]["PriceNettTotal"], 900.0)
        self.assertEqual(line2["Totals"]["DiscountTotalPct"], 10.0)

        hydrator.set_order_line_pricing(0, price_each=1000, quantity=1, net_total=800)
        line3 = hydrator.get_order_lines()[0]
        self.assertEqual(line3["Totals"]["PriceNettTotal"], 800.0)

        with self.assertRaises(OrderWriteHydrationError):
            hydrator.set_order_line_pricing(0, price_each=1000, quantity=1, discount_pct=10, net_total=900)

    def test_hydrator_accepts_business_friendly_order_line_dict(self) -> None:
        hydrator = self.workflow.new_hydrator()
        hydrator.add_order_line(
            {
                "article_number": "22555",
                "description": "article description",
                "quantity": 2,
                "price_each": 500,
            }
        )

        line = hydrator.get_order_lines()[0]
        self.assertEqual(line["ArticleNumber"], "22555")
        self.assertEqual(line["Description"], "article description")
        self.assertEqual(line["Quantity"], 2)
        self.assertEqual(line["PriceEach"], 500)
        self.assertTrue("Totals" not in line or isinstance(line["Totals"], dict))

    def test_hydrator_set_order_lines_supports_bulk_replace(self) -> None:
        hydrator = self.workflow.new_hydrator({"OrderTaskLines": [{"ArticleNumber": "1000", "Quantity": 1}]})
        hydrator.set_order_lines(
            [
                {"article_number": "22555", "quantity": 1, "price_each": 900},
                {"article_id": 1234, "description": "service", "quantity": 3},
            ],
            clear_existing=True,
        )

        lines = hydrator.get_order_lines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["ArticleNumber"], "22555")
        self.assertEqual(lines[1]["ArticleId"], 1234)

    def test_hydrator_business_line_rejects_ambiguous_discount_inputs(self) -> None:
        hydrator = self.workflow.new_hydrator()
        with self.assertRaises(OrderWriteHydrationError):
            hydrator.add_order_line(
                {
                    "article_number": "22555",
                    "quantity": 1,
                    "price_each": 900,
                    "discount_pct": 10,
                    "net_total": 810,
                }
            )

    def test_assist_hydrate_fills_partner_and_article_defaults(self) -> None:
        hydrator = self.workflow.new_hydrator(
            {
                "PartnerId": 2251919792,
                "OrderTaskLines": [{"article_number": "1020"}],
            }
        )
        self.workflow._partner_workflow = _FakePartnerWorkflow()  # type: ignore[assignment]
        self.workflow._article_workflow = _FakeArticleWorkflow()  # type: ignore[assignment]

        metadata = self.workflow.assist_hydrate(
            hydrator,
            hydrate_partner=True,
            hydrate_articles=True,
        )

        dto = hydrator.to_dict()
        self.assertEqual(dto["PartnerName"], "Gj System Da")
        self.assertEqual(dto["Address"]["Zip"], "5258")
        self.assertEqual(dto["GLNNumber"], "995361108")

        line = hydrator.get_order_lines()[0]
        self.assertEqual(line["ArticleId"], 2188837687)
        self.assertEqual(line["Description"], "Secura KS - Kvalitetsstyring")
        self.assertEqual(line["Quantity"], 1)
        self.assertEqual(line["PriceEach"], 750)
        self.assertEqual(line["Totals"]["DiscountTotalPct"], 0.0)

        self.assertTrue(metadata["partner_fields_filled"])
        self.assertTrue(metadata["article_fields_filled"])

    def test_assist_hydrate_respects_explicit_values(self) -> None:
        hydrator = self.workflow.new_hydrator(
            {
                "PartnerId": 2251919792,
                "PartnerName": "Explicit Name",
                "Address": {
                    "Name": "Explicit Address Name",
                    "Street": "",
                },
                "OrderTaskLines": [
                    {
                        "article_number": "1020",
                        "PriceEach": 900,
                        "Quantity": 2,
                    }
                ],
            }
        )
        self.workflow._partner_workflow = _FakePartnerWorkflow()  # type: ignore[assignment]
        self.workflow._article_workflow = _FakeArticleWorkflow()  # type: ignore[assignment]

        self.workflow.assist_hydrate(hydrator, hydrate_partner=True, hydrate_articles=True)

        dto = hydrator.to_dict()
        self.assertEqual(dto["PartnerName"], "Explicit Name")
        # Explicit subfield should be preserved; missing subfields should be auto-filled.
        self.assertEqual(dto["Address"]["Name"], "Explicit Address Name")
        self.assertEqual(dto["Address"]["Street"], "Espelandsvegen 27")
        self.assertEqual(dto["Address"]["Zip"], "5258")
        line = hydrator.get_order_lines()[0]
        self.assertEqual(line["PriceEach"], 900)
        self.assertEqual(line["Quantity"], 2)

    def test_assist_hydrate_partner_only_fills_missing_subfields(self) -> None:
        hydrator = self.workflow.new_hydrator(
            {
                "PartnerAccountNumber": 10010,
                "Address": {
                    "Name": "Custom Name",
                    "City": "",
                },
            }
        )
        self.workflow._partner_workflow = _FakePartnerWorkflow()  # type: ignore[assignment]

        meta = self.workflow.assist_hydrate(hydrator, hydrate_partner=True, hydrate_articles=False)
        dto = hydrator.to_dict()

        self.assertEqual(dto["Address"]["Name"], "Custom Name")
        self.assertEqual(dto["Address"]["City"], "BLOMSTERDALEN")
        self.assertEqual(dto["Address"]["Street"], "Espelandsvegen 27")
        self.assertEqual(dto["PartnerName"], "Gj System Da")
        self.assertTrue(any(str(item).startswith("Address.") for item in meta["partner_fields_filled"]))

    def test_create_hydrated_assisted_returns_result_and_assist_metadata(self) -> None:
        hydrator = self.workflow.new_hydrator(
            {
                "PartnerId": 2251919792,
                "OrderTaskLines": [{"article_number": "1020"}],
            }
        )
        self.workflow._partner_workflow = _FakePartnerWorkflow()  # type: ignore[assignment]
        self.workflow._article_workflow = _FakeArticleWorkflow()  # type: ignore[assignment]

        response = self.workflow.create_hydrated_assisted(
            hydrator,
            hydrate_partner=True,
            hydrate_articles=True,
        )

        self.assertIn("result", response)
        self.assertIn("assist", response)
        self.assertEqual(response["result"]["Id"], 4001)
        assert self.api.last_create_data is not None
        self.assertEqual(self.api.last_create_data["PartnerName"], "Gj System Da")
        self.assertTrue(response["assist"]["partner_fields_filled"])

    def test_update_hydrated_assisted_returns_result_and_assist_metadata(self) -> None:
        hydrator = self.workflow.new_hydrator(
            {
                "PartnerId": 2251919792,
                "OrderTaskLines": [{"article_number": "1020"}],
            }
        )
        self.workflow._partner_workflow = _FakePartnerWorkflow()  # type: ignore[assignment]
        self.workflow._article_workflow = _FakeArticleWorkflow()  # type: ignore[assignment]

        response = self.workflow.update_hydrated_assisted(
            4001,
            hydrator,
            hydrate_partner=True,
            hydrate_articles=True,
        )

        self.assertIn("result", response)
        self.assertIn("assist", response)
        self.assertEqual(response["result"]["Id"], 4001)
        assert self.api.last_update_data is not None
        self.assertEqual(self.api.last_update_data["PartnerName"], "Gj System Da")
        self.assertTrue(response["assist"]["article_fields_filled"])

    def test_explicit_transition_methods(self) -> None:
        offered = self.workflow.offer(4001, {"Message": "Offer"})
        self.assertEqual(offered["State"], "Offered")

        confirmed = self.workflow.confirm(4001, {"Message": "Confirm"})
        self.assertEqual(confirmed["State"], "Confirmed")

        delivered = self.workflow.deliver(4001, {"DeliveryDateDays": 20543})
        self.assertEqual(delivered["State"], "Delivered")

        invoiced = self.workflow.bookkeep(4001, {"BookkeepDateDays": 20543})
        self.assertEqual(invoiced["State"], "Invoiced")

    def test_delete(self) -> None:
        result = self.workflow.delete(4001)
        self.assertTrue(result["Success"])
        self.assertEqual(self.api.last_delete_id, 4001)

    def test_create_simple_order_creates_header_and_lines(self) -> None:
        self.workflow._partner_workflow = _FakePartnerWorkflow()  # type: ignore[assignment]
        self.workflow._article_workflow = _FakeArticleWorkflow()  # type: ignore[assignment]

        response = self.workflow.create_simple_order(
            customer_account_number=10010,
            our_reference="JW",
            your_reference="GB",
            order_date="15.04.2026",
            gln_number="995361108",
            lines=[
                {
                    "article_number": 1020,
                    "quantity": 1,
                    "price_each": 1,
                }
            ],
        )

        assert self.api.last_create_data is not None
        assert self.api.last_update_data is not None
        self.assertEqual(self.api.last_create_data["PartnerId"], 2251919792)
        self.assertEqual(self.api.last_update_data["OurReference"], "JW")
        self.assertEqual(self.api.last_update_data["YourReference"], "GB")
        self.assertEqual(self.api.last_update_data["GLNNumber"], "995361108")
        self.assertEqual(len(self.api.created_lines), 1)

        created_line = self.api.created_lines[0]
        self.assertEqual(created_line["OrderTaskId"], 9001)
        self.assertEqual(created_line["ArticleNumber"], "1020")
        self.assertEqual(created_line["ArticleId"], 2188837687)
        self.assertEqual(created_line["Quantity"], 1)
        self.assertEqual(created_line["UnitNetPrice"], 1)

        self.assertIn("order", response)
        self.assertIn("lines", response)
        self.assertEqual(len(response["lines"]), 1)

    def test_bookkeep_and_distribute_none(self) -> None:
        response = self.workflow.bookkeep_and_distribute(
            4001,
            bookkeep_data={"version": 2, "doDeliver": False},
            distribution="none",
        )

        self.assertEqual(response["distribution"], "none")
        self.assertIsNone(response["distribution_result"])
        self.assertEqual(self.api.last_bookkeep_id, 4001)

    def test_bookkeep_and_distribute_email_uses_document_from_journal(self) -> None:
        response = self.workflow.bookkeep_and_distribute(
            4001,
            bookkeep_data={"version": 2, "doDeliver": False},
            distribution="email",
            email_to_addresses="jarle@gj-system.no",
        )

        self.assertEqual(response["distribution"], "email")
        self.assertEqual(self.api.session.last_post_url, "https://my.xena.biz/Api/Fiscal/104779/Email/Send")
        assert self.api.session.last_post_json is not None
        self.assertEqual(self.api.session.last_post_json["ToAddresses"], "jarle@gj-system.no")
        self.assertEqual(self.api.session.last_post_json["DocumentIds"], [3038297310])
        self.assertTrue(self.api.session.last_post_json["Subject"].startswith("Faktura "))

    def test_bookkeep_and_distribute_email_requires_recipient(self) -> None:
        with self.assertRaises(OrderDistributionError):
            self.workflow.bookkeep_and_distribute(
                4001,
                bookkeep_data={"version": 2, "doDeliver": False},
                distribution="email",
            )

    def test_bookkeep_and_distribute_ehf_builds_payload_from_defaults(self) -> None:
        response = self.workflow.bookkeep_and_distribute(
            4001,
            bookkeep_data={"version": 2, "doDeliver": False},
            distribution="ehf",
        )

        self.assertEqual(response["distribution"], "ehf")
        assert self.api.last_send_electronic_data is not None
        self.assertEqual(self.api.last_send_electronic_data["OrderInvoiceTransactionId"], 3038185190)
        self.assertEqual(self.api.last_send_electronic_data["PartnerAccountNumber"], 10010)
        self.assertEqual(
            self.api.last_send_electronic_data["Endpoint"],
            {
                "RecipientAddressType": "NOORG",
                "RecipientAddress": "NO995361108",
            },
        )

    def test_create_and_send_invoice_simple_skips_email_when_no_email(self) -> None:
        self.workflow._partner_workflow = _FakePartnerWorkflowMissingEmailAndGln()  # type: ignore[assignment]
        self.workflow._article_workflow = _FakeArticleWorkflow()  # type: ignore[assignment]

        response = self.workflow.create_and_send_invoice_simple(
            customer_account_number=10010,
            distribution="email",
            order_date="15.04.2026",
            lines=[{"article_number": 1020, "quantity": 1, "price_each": 1}],
        )

        self.assertEqual(response["distribution_requested"], "email")
        self.assertEqual(response["distribution_effective"], "none")
        self.assertTrue(str(response["distribution_skipped_reason"]).startswith("Email distribution skipped"))
        self.assertEqual(response["invoice"]["distribution"], "none")
        self.assertIsNone(self.api.session.last_post_json)

    def test_create_and_send_invoice_simple_skips_ehf_when_no_gln(self) -> None:
        self.workflow._partner_workflow = _FakePartnerWorkflowMissingEmailAndGln()  # type: ignore[assignment]
        self.workflow._article_workflow = _FakeArticleWorkflow()  # type: ignore[assignment]

        response = self.workflow.create_and_send_invoice_simple(
            customer_account_number=10010,
            distribution="ehf",
            order_date="15.04.2026",
            lines=[{"article_number": 1020, "quantity": 1, "price_each": 1}],
        )

        self.assertEqual(response["distribution_requested"], "ehf")
        self.assertEqual(response["distribution_effective"], "none")
        self.assertTrue(str(response["distribution_skipped_reason"]).startswith("EHF distribution skipped"))
        self.assertEqual(response["invoice"]["distribution"], "none")
        self.assertIsNone(self.api.last_send_electronic_data)


if __name__ == "__main__":
    unittest.main()
