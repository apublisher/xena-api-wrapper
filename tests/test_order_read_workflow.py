from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.order.order_read import (
    OrderAmbiguousError,
    OrderNotFoundError,
    OrderReadError,
    OrderReadWorkflow,
)


class _FakeOrderApi:
    def __init__(self) -> None:
        self.last_get_kwargs: dict[str, Any] | None = None
        self.last_get_invoice_kwargs: dict[str, Any] | None = None
        self.last_get_by_partner_id: int | None = None
        self.last_get_invoice_by_partner_id: int | None = None

    def api_order__get_get__api__fiscal_fiscal_id__order(self, fiscal_id: str, **kwargs: Any) -> dict[str, Any]:
        self.last_get_kwargs = {"fiscal_id": fiscal_id, **kwargs}
        query = str(kwargs.get("filter_query_string") or "")

        entities: list[dict[str, Any]] = [
            {
                "Id": 11,
                "OrderNumber": 200271,
                "PartnerId": 9001,
                "PartnerAccountNumber": 10008,
                "OrderInvoiceNumbers": "100001",
            },
            {
                "Id": 12,
                "OrderNumber": 200272,
                "PartnerId": 9002,
                "PartnerAccountNumber": 10003,
                "OrderInvoiceNumbers": "100002,100003",
            },
        ]

        if query:
            entities = [
                e
                for e in entities
                if query in str(e.get("OrderNumber"))
                or query in str(e.get("PartnerAccountNumber"))
                or query in str(e.get("OrderInvoiceNumbers"))
            ]

        partner_id = kwargs.get("filter_partner_id")
        if isinstance(partner_id, int):
            entities = [e for e in entities if e.get("PartnerId") == partner_id]

        return {"Count": len(entities), "Entities": entities}

    def api_order__get_get__api__fiscal_fiscal_id__order_id(self, id: int, fiscal_id: str, **kwargs: Any) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        if id == 11:
            return {"Id": 11, "OrderNumber": 200271, "OrderInvoiceNumbers": "100001"}
        if id == 12:
            return {"Id": 12, "OrderNumber": 200272, "OrderInvoiceNumbers": "100002,100003"}
        return {"Id": id, "OrderNumber": 999999, "OrderInvoiceNumbers": ""}

    def api_order__get_by_number_get__api__fiscal_fiscal_id__order__by_number(
        self,
        order_number: int,
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        return {"Id": 11, "OrderNumber": order_number}

    def api_order__get_by_partner_get__api__fiscal_fiscal_id__partner_id__order(
        self,
        id: int,
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_get_by_partner_id = id
        return {"Count": 1, "Entities": [{"Id": 11, "PartnerId": id}]}

    def api_order__get_invoice_get__api__fiscal_fiscal_id__order__invoice(self, fiscal_id: str, **kwargs: Any) -> dict[str, Any]:
        self.last_get_invoice_kwargs = {"fiscal_id": fiscal_id, **kwargs}
        query = str(kwargs.get("filter_query_string") or "")

        entities: list[dict[str, Any]] = [
            {"Id": 801, "OrderId": 11, "OrderNumber": 200271, "VoucherNumber": 100001, "DocumentId": 100001},
            {"Id": 802, "OrderId": 12, "OrderNumber": 200272, "VoucherNumber": 100002, "DocumentId": 100002},
        ]

        if query:
            entities = [e for e in entities if query in str(e.get("VoucherNumber")) or query in str(e.get("OrderNumber"))]

        partner_id = kwargs.get("filter_partner_id")
        if isinstance(partner_id, int):
            entities = [e for e in entities if (e.get("OrderId") == 11 and partner_id == 9001) or (e.get("OrderId") == 12 and partner_id == 9002)]

        return {"Count": len(entities), "Entities": entities}

    def api_order__get_invoice_by_partner_get__api__fiscal_fiscal_id__partner_id__invoice(
        self,
        id: int,
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_get_invoice_by_partner_id = id
        if id == 9001:
            entities = [{"Id": 801, "OrderId": 11, "VoucherNumber": 100001}]
        else:
            entities = [{"Id": 802, "OrderId": 12, "VoucherNumber": 100002}]
        return {"Count": len(entities), "Entities": entities}


class OrderReadWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = _FakeOrderApi()
        self.workflow = OrderReadWorkflow(SimpleNamespace(order=self.api), "104779")

    def test_get_all_and_entities(self) -> None:
        result = self.workflow.get_all(context_type="ContextType_Customer", query_string="200271")
        self.assertEqual(result["Count"], 1)
        entities = self.workflow.get_entities(query_string="")
        self.assertEqual(len(entities), 2)

    def test_get_by_id_and_order_number(self) -> None:
        one = self.workflow.get_by_id(11)
        self.assertEqual(one["OrderNumber"], 200271)
        by_no = self.workflow.get_by_order_number(200271)
        self.assertEqual(by_no["OrderNumber"], 200271)

    def test_get_by_partner_and_invoice_by_partner(self) -> None:
        rows = self.workflow.get_by_partner(9001)
        self.assertEqual(rows["Count"], 1)
        self.assertEqual(self.api.last_get_by_partner_id, 9001)

        inv = self.workflow.get_invoices_by_partner(9001)
        self.assertEqual(inv["Count"], 1)
        self.assertEqual(self.api.last_get_invoice_by_partner_id, 9001)

    def test_get_by_invoice_number(self) -> None:
        order = self.workflow.get_by_invoice_number(100001)
        self.assertEqual(order["Id"], 11)

    def test_get_by_invoice_number_not_found(self) -> None:
        with self.assertRaises(OrderNotFoundError):
            self.workflow.get_by_invoice_number(999999)

    def test_get_by_invoice_number_ambiguous(self) -> None:
        original = self.api.api_order__get_invoice_get__api__fiscal_fiscal_id__order__invoice

        def dupes(fiscal_id: str, **kwargs: Any) -> dict[str, Any]:
            _ = (fiscal_id, kwargs)
            return {
                "Count": 2,
                "Entities": [
                    {"OrderId": 11, "VoucherNumber": 100001},
                    {"OrderId": 12, "VoucherNumber": 100001},
                ],
            }

        self.api.api_order__get_invoice_get__api__fiscal_fiscal_id__order__invoice = dupes  # type: ignore[method-assign]
        with self.assertRaises(OrderAmbiguousError):
            self.workflow.get_by_invoice_number(100001)
        self.api.api_order__get_invoice_get__api__fiscal_fiscal_id__order__invoice = original  # type: ignore[method-assign]

    def test_resolve_one(self) -> None:
        self.assertEqual(self.workflow.resolve_one(id=11)["Id"], 11)
        self.assertEqual(self.workflow.resolve_one(order_number=200271)["OrderNumber"], 200271)
        self.assertEqual(self.workflow.resolve_one(invoice_number=100001)["Id"], 11)

        with self.assertRaises(OrderReadError):
            self.workflow.resolve_one(id=11, order_number=200271)

    def test_missing_generated_method_raises(self) -> None:
        workflow = OrderReadWorkflow(SimpleNamespace(order=SimpleNamespace()), "104779")
        with self.assertRaises(AttributeError):
            workflow.get_all()


if __name__ == "__main__":
    unittest.main()
