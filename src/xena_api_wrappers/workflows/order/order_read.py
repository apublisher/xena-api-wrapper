from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from ...core import DateInput, to_fiscal_date_int


class OrderReadError(ValueError):
    """Base error for order read workflow operations."""


class OrderNotFoundError(OrderReadError):
    """Raised when an order lookup returns no result."""


class OrderAmbiguousError(OrderReadError):
    """Raised when an order lookup returns more than one result."""


@dataclass
class OrderReadWorkflow:
    """Read-only workflow helper for order, invoice, and task retrieval endpoints."""

    _client: Any
    _fiscal_id: str

    def get_all(
        self,
        *,
        query_string: str | None = None,
        context_type: str | None = "ContextType_Customer",
        deliver_filter: str | None = None,
        partner_id: int | None = None,
        order_status_id: int | None = None,
        responsible_id: int | None = None,
        limit_to_responsible: bool | None = None,
        department_id: int | None = None,
        limit_to_department: bool | None = None,
        bearer_id: int | None = None,
        limit_to_bearer: bool | None = None,
        purpose_id: int | None = None,
        limit_to_purpose: bool | None = None,
        date_from: DateInput | None = None,
        date_to: DateInput | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = False,
    ) -> Any:
        return self._client.order.api_order__get_get__api__fiscal_fiscal_id__order(
            fiscal_id=self._fiscal_id,
            filter_query_string=query_string,
            filter_context_type=context_type,
            filter_deliver_filter=deliver_filter,
            filter_partner_id=partner_id,
            filter_order_status_id=order_status_id,
            filter_responsible_id=responsible_id,
            filter_limit_to_responsible=limit_to_responsible,
            filter_department_id=department_id,
            filter_limit_to_department=limit_to_department,
            filter_bearer_id=bearer_id,
            filter_limit_to_bearer=limit_to_bearer,
            filter_purpose_id=purpose_id,
            filter_limit_to_purpose=limit_to_purpose,
            filter_date_from=to_fiscal_date_int(date_from) if date_from is not None else None,
            filter_date_to=to_fiscal_date_int(date_to) if date_to is not None else None,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self._extract_entities(self.get_all(**kwargs), label="Order")

    def get_by_id(self, order_id: int) -> Any:
        return self._client.order.api_order__get_get__api__fiscal_fiscal_id__order_id(
            id=order_id,
            fiscal_id=self._fiscal_id,
        )

    def get_by_order_number(self, order_number: int) -> Any:
        return self._client.order.api_order__get_by_number_get__api__fiscal_fiscal_id__order__by_number(
            order_number=order_number,
            fiscal_id=self._fiscal_id,
        )

    def get_by_partner(
        self,
        partner_id: int,
        *,
        context_type: str | None = "ContextType_Customer",
        query_string: str | None = None,
        date_from: DateInput | None = None,
        date_to: DateInput | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = False,
    ) -> Any:
        return self._client.order.api_order__get_by_partner_get__api__fiscal_fiscal_id__partner_id__order(
            id=partner_id,
            fiscal_id=self._fiscal_id,
            context_type=context_type,
            query_string=query_string,
            date_from=to_fiscal_date_int(date_from) if date_from is not None else None,
            date_to=to_fiscal_date_int(date_to) if date_to is not None else None,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_invoices(
        self,
        *,
        query_string: str | None = None,
        context_type: str | None = "ContextType_Customer",
        deliver_filter: str | None = None,
        is_settled: bool | None = None,
        partner_id: int | None = None,
        order_status_id: int | None = None,
        responsible_id: int | None = None,
        limit_to_responsible: bool | None = None,
        date_from: DateInput | None = None,
        date_to: DateInput | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = False,
    ) -> Any:
        return self._client.order.api_order__get_invoice_get__api__fiscal_fiscal_id__order__invoice(
            fiscal_id=self._fiscal_id,
            filter_query_string=query_string,
            filter_context_type=context_type,
            filter_deliver_filter=deliver_filter,
            filter_is_settled=is_settled,
            filter_partner_id=partner_id,
            filter_order_status_id=order_status_id,
            filter_responsible_id=responsible_id,
            filter_limit_to_responsible=limit_to_responsible,
            filter_date_from=to_fiscal_date_int(date_from) if date_from is not None else None,
            filter_date_to=to_fiscal_date_int(date_to) if date_to is not None else None,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_invoice_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self._extract_entities(self.get_invoices(**kwargs), label="Order invoice")

    def get_invoices_by_partner(
        self,
        partner_id: int,
        *,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = False,
    ) -> Any:
        return self._client.order.api_order__get_invoice_by_partner_get__api__fiscal_fiscal_id__partner_id__invoice(
            id=partner_id,
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_by_invoice_number(
        self,
        invoice_number: int | str,
        *,
        context_type: str | None = "ContextType_Customer",
        partner_id: int | None = None,
        show_deactivated: bool = False,
        page_size: int = 100,
    ) -> dict[str, Any]:
        lookup = str(invoice_number).strip()
        if not lookup:
            raise OrderReadError("invoice_number must not be empty")

        invoices_payload = self.get_invoices(
            query_string=lookup,
            context_type=context_type,
            partner_id=partner_id,
            show_deactivated=show_deactivated,
            page=0,
            page_size=page_size,
            force_no_paging=False,
        )
        invoice_entities = self._extract_entities(invoices_payload, label="Order invoice")

        matches = [entity for entity in invoice_entities if self._matches_invoice_number(entity, lookup)]
        match = self._single_match(matches, label=f"invoice number '{lookup}'")

        order_id = match.get("OrderId")
        if not isinstance(order_id, int):
            raise OrderReadError("Invoice payload missing integer OrderId field")

        raw_order = self.get_by_id(order_id)
        order_dict = self._as_dict(raw_order, label="Order")

        # Enforce semantics: invoice selector only resolves invoiced orders.
        order_invoice_numbers = order_dict.get("OrderInvoiceNumbers")
        if isinstance(order_invoice_numbers, str) and lookup not in order_invoice_numbers:
            raise OrderNotFoundError(f"No invoiced order found for invoice number '{lookup}'")

        return order_dict

    def get_tasks_by_order(self, order_id: int) -> list[dict[str, Any]]:
        """Return task entities for one order id."""
        payload = self._client.order.api_order_task__get_by_order_get__api__fiscal_fiscal_id__order_id__order_task(
            id=order_id,
            fiscal_id=self._fiscal_id,
            list_options_force_no_paging=True,
        )
        return self._extract_entities(payload, label="Order task")

    def get_task_by_id(self, task_id: int) -> dict[str, Any]:
        """Return a single order task by id using generated API naming fallbacks."""
        candidates = [
            "api_order_task__get_get__api__fiscal_fiscal_id__order_task_id",
            "api_order_task__get_get__api__fiscal_fiscal_id__order_task__id",
        ]
        for candidate in candidates:
            method = getattr(self._client.order, candidate, None)
            if callable(method):
                return self._as_dict(
                    method(
                        id=task_id,
                        fiscal_id=self._fiscal_id,
                    ),
                    label="Order task",
                )

        raise OrderReadError(
            "Order-task get-by-id endpoint is not available on the configured client"
        )

    def resolve_primary_task(
        self,
        order_id: int,
        *,
        on_multiple: str = "raise",
    ) -> dict[str, Any]:
        """Resolve primary task for an order with explicit multi-task behavior.

        on_multiple:
        - "raise": raise OrderAmbiguousError when more than one task exists.
        - "first": return the first task entity.
        """
        tasks = self.get_tasks_by_order(order_id)
        if not tasks:
            raise OrderNotFoundError(f"No order task found for order id {order_id}")

        if len(tasks) > 1:
            if on_multiple == "first":
                return tasks[0]
            if on_multiple != "raise":
                raise OrderReadError("on_multiple must be one of: raise, first")
            raise OrderAmbiguousError(
                f"More than one order task matched order id {order_id}"
            )

        return tasks[0]

    def resolve_one(
        self,
        *,
        id: int | None = None,
        order_number: int | None = None,
        invoice_number: int | str | None = None,
        context_type: str | None = "ContextType_Customer",
        partner_id: int | None = None,
    ) -> dict[str, Any]:
        provided = sum(
            [
                1 if id is not None else 0,
                1 if order_number is not None else 0,
                1 if invoice_number is not None else 0,
            ]
        )
        if provided != 1:
            raise OrderReadError("Provide exactly one selector: id, order_number, or invoice_number")

        if id is not None:
            return self._as_dict(self.get_by_id(id), label="Order")
        if order_number is not None:
            return self._as_dict(self.get_by_order_number(order_number), label="Order")
        return self.get_by_invoice_number(
            cast(int | str, invoice_number),
            context_type=context_type,
            partner_id=partner_id,
        )

    @staticmethod
    def _extract_entities(payload: Any, *, label: str) -> list[dict[str, Any]]:
        payload_dict = OrderReadWorkflow._as_dict(payload, label=label)
        entities_obj = payload_dict.get("Entities")
        if not isinstance(entities_obj, list):
            raise OrderReadError(f"Unexpected {label} response shape: could not read Entities list")

        entities = cast(list[Any], entities_obj)
        return [cast(dict[str, Any], entity) for entity in entities if isinstance(entity, dict)]

    @staticmethod
    def _as_dict(payload: Any, *, label: str) -> dict[str, Any]:
        if isinstance(payload, dict):
            return cast(dict[str, Any], payload)
        to_dict = getattr(cast(object, payload), "to_dict", None)
        if callable(to_dict):
            converted = to_dict()
            if isinstance(converted, dict):
                return cast(dict[str, Any], converted)
        raise OrderReadError(f"Unexpected {label} response shape: expected dict-like payload")

    @staticmethod
    def _single_match(matches: list[dict[str, Any]], *, label: str) -> dict[str, Any]:
        if not matches:
            raise OrderNotFoundError(f"No order found for {label}")
        if len(matches) > 1:
            raise OrderAmbiguousError(f"More than one order matched {label}")
        return matches[0]

    @staticmethod
    def _matches_invoice_number(entity: dict[str, Any], lookup: str) -> bool:
        for key in ("InvoiceNumber", "DocumentId", "VoucherNumber"):
            value = entity.get(key)
            if value is not None and str(value).strip() == lookup:
                return True

        order_invoice_numbers = entity.get("OrderInvoiceNumbers")
        if isinstance(order_invoice_numbers, str):
            parts = [part.strip() for part in order_invoice_numbers.split(",") if part.strip()]
            if lookup in parts:
                return True

        return False
