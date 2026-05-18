from __future__ import annotations

from datetime import date
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, cast

from ...core import DateInput, to_fiscal_date_int
from .distribution_policy import (
    DEFAULT_EHF_RECIPIENT_ADDRESS_TYPE,
    SUPPORTED_DISTRIBUTION_MODES,
)
from .order_errors import (
    OrderDistributionError,
    OrderWriteError,
    OrderWriteHydrationError,
)
from .distribution_service import OrderDistributionService
from .dto_hydrator import OrderDtoHydrator
from ..article.article import ArticleWorkflow
from ..partner.partner import PartnerWorkflow


@dataclass
class OrderWriteWorkflow:
    """Write workflow helper for explicit order and order-task mutations.

    Mapping note for Xena order details UI:
    - Visible description maps to OrderTask.Description.
    - Visible note maps to OrderTask.Details.
    - Order header Description/DeliveryNote/InternalNote/PartnerNote are preserved for
      backward compatibility and other flows/views.
    """

    _client: Any
    _fiscal_id: str
    _partner_workflow: PartnerWorkflow | None = None
    _article_workflow: ArticleWorkflow | None = None
    _distribution_service: OrderDistributionService | None = None

    def assist_hydrate(
        self,
        hydrator: OrderDtoHydrator,
        *,
        hydrate_partner: bool = False,
        hydrate_articles: bool = False,
    ) -> dict[str, Any]:
        """Fill missing partner/article fields from lookup workflows without overriding explicit input."""

        metadata: dict[str, Any] = {
            "hydrate_partner": hydrate_partner,
            "hydrate_articles": hydrate_articles,
            "partner_fields_filled": [],
            "article_fields_filled": [],
        }

        if hydrate_partner:
            partner_data = self._resolve_partner_for_hydration(hydrator)
            if partner_data is not None:
                filled = self._hydrate_partner_defaults(hydrator, partner_data)
                metadata["partner_fields_filled"] = filled

        if hydrate_articles:
            filled_article_fields = self._hydrate_article_defaults(hydrator)
            metadata["article_fields_filled"] = filled_article_fields

        return metadata

    def new_hydrator(
        self,
        data: dict[str, Any] | None = None,
        *,
        article_collection_key: str = "OrderTaskLines",
    ) -> OrderDtoHydrator:
        return OrderDtoHydrator.create(
            data,
            article_collection_key=article_collection_key,
        )

    def create_hydrated(self, hydrator: OrderDtoHydrator) -> Any:
        return self.create(hydrator.to_dict())

    def create_hydrated_assisted(
        self,
        hydrator: OrderDtoHydrator,
        *,
        hydrate_partner: bool = False,
        hydrate_articles: bool = False,
    ) -> dict[str, Any]:
        metadata = self.assist_hydrate(
            hydrator,
            hydrate_partner=hydrate_partner,
            hydrate_articles=hydrate_articles,
        )
        created = self.create_hydrated(hydrator)
        return {
            "result": created,
            "assist": metadata,
        }

    def update_hydrated(self, order_id: int, hydrator: OrderDtoHydrator) -> Any:
        return self.update(order_id, hydrator.to_dict())

    def update_hydrated_assisted(
        self,
        order_id: int,
        hydrator: OrderDtoHydrator,
        *,
        hydrate_partner: bool = False,
        hydrate_articles: bool = False,
    ) -> dict[str, Any]:
        metadata = self.assist_hydrate(
            hydrator,
            hydrate_partner=hydrate_partner,
            hydrate_articles=hydrate_articles,
        )
        updated = self.update_hydrated(order_id, hydrator)
        return {
            "result": updated,
            "assist": metadata,
        }

    def create(self, create_data: dict[str, Any]) -> Any:
        return self._client.order.api_order__post_post__api__fiscal_fiscal_id__order(
            create_data=create_data,
            fiscal_id=self._fiscal_id,
        )

    def update(self, order_id: int, order_dto: dict[str, Any]) -> Any:
        return self._client.order.api_order__put_put__api__fiscal_fiscal_id__order_id(
            order_dto=order_dto,
            fiscal_id=self._fiscal_id,
            id=str(order_id),
        )

    def update_task(self, task_id: int, task_dto: dict[str, Any]) -> Any:
        """Update one order task using generated API naming/signature fallbacks."""
        if not isinstance(task_dto, dict):
            raise OrderWriteError("task_dto must be a dict")
        if not task_dto:
            raise OrderWriteError("task_dto must not be empty")

        candidates = [
            "api_order_task__put_put__api__fiscal_fiscal_id__order_task_id",
            "api_order_task__put_put__api__fiscal_fiscal_id__order_task__id",
        ]
        payload_keys = ["order_task_dto", "task_dto", "order_dto", "create_data"]

        for candidate in candidates:
            method = getattr(self._client.order, candidate, None)
            if not callable(method):
                continue

            for payload_key in payload_keys:
                for typed_task_id in (task_id, str(task_id)):
                    try:
                        return method(
                            fiscal_id=self._fiscal_id,
                            id=typed_task_id,
                            **{payload_key: task_dto},
                        )
                    except TypeError:
                        continue

        raise OrderWriteError(
            "Order-task update endpoint is not available on the configured client"
        )

    def update_task_fields(
        self,
        task_id: int,
        *,
        description: str | None = None,
        details: str | None = None,
        internal_note: str | None = None,
        merge_with_existing: bool = True,
        **extra_fields: Any,
    ) -> dict[str, Any]:
        """Update task-level fields with explicit mapping semantics.

        Mapping note:
        - Xena order-details UI description -> OrderTask.Description
        - Xena order-details UI note -> OrderTask.Details
        """
        task_patch: dict[str, Any] = {}
        if description is not None:
            task_patch["Description"] = description
        if details is not None:
            task_patch["Details"] = details
        if internal_note is not None:
            task_patch["InternalNote"] = internal_note

        task_patch.update(extra_fields)
        if not task_patch:
            raise OrderWriteError("At least one task field must be provided")

        task_dto = dict(task_patch)
        if merge_with_existing:
            existing_task = self._get_order_task_by_id(task_id)
            if existing_task is not None:
                task_dto = {**existing_task, **task_patch}

        updated = self.update_task(task_id, task_dto)
        return self._as_dict(updated)

    def update_primary_task_for_order(
        self,
        order_id: int,
        *,
        description: str | None = None,
        details: str | None = None,
        internal_note: str | None = None,
        on_multiple: str = "raise",
        **extra_fields: Any,
    ) -> dict[str, Any]:
        """Update primary task fields for an order with explicit multi-task behavior."""
        task = self._resolve_primary_task_entity(order_id, on_multiple=on_multiple)
        task_id_obj = task.get("Id")
        if not isinstance(task_id_obj, int):
            raise OrderWriteError("Unexpected order task response shape: missing integer Id")

        return self.update_task_fields(
            task_id_obj,
            description=description,
            details=details,
            internal_note=internal_note,
            **extra_fields,
        )

    # Explicit transition method: moves order into offer flow.
    def offer(self, order_id: int, create_data: dict[str, Any]) -> Any:
        return self._client.order.api_order__put_offer_put__api__fiscal_fiscal_id__order_id__offer(
            id=order_id,
            create_data=create_data,
            fiscal_id=self._fiscal_id,
        )

    # Explicit transition method: confirms order from offer/draft state.
    def confirm(self, order_id: int, create_data: dict[str, Any]) -> Any:
        return self._client.order.api_order__put_confirmation_put__api__fiscal_fiscal_id__order_id__confirmation(
            id=order_id,
            create_data=create_data,
            fiscal_id=self._fiscal_id,
        )

    # Explicit transition method: marks delivery with provided payload.
    def deliver(self, order_id: int, deliver_data: dict[str, Any]) -> Any:
        return self._client.order.api_order__put_deliver_put__api__fiscal_fiscal_id__order_id__deliver(
            id=order_id,
            deliver_data=deliver_data,
            fiscal_id=self._fiscal_id,
        )

    # Explicit transition method: books/invoices order with provided payload.
    def bookkeep(self, order_id: int, bookkeep_data: dict[str, Any]) -> Any:
        return self._client.order.api_order__put_bookkeep_put__api__fiscal_fiscal_id__order_id__bookkeep(
            id=order_id,
            bookkeep_data=bookkeep_data,
            fiscal_id=self._fiscal_id,
        )

    def delete(self, order_id: int) -> Any:
        return self._client.order.api_order__delete_delete__api__fiscal_fiscal_id__order_id(
            id=order_id,
            fiscal_id=self._fiscal_id,
        )

    def bookkeep_and_distribute(
        self,
        order_id: int,
        *,
        bookkeep_data: dict[str, Any],
        distribution: str | None = None,
        email_to_addresses: str | None = None,
        email_subject: str | None = None,
        email_body_text: str | None = None,
        email_include_signature: bool = True,
        email_document_ids: list[int] | None = None,
        ehf_recipient_address: str | None = None,
        ehf_recipient_address_type: str = DEFAULT_EHF_RECIPIENT_ADDRESS_TYPE,
        ehf_party_identifications: Any = None,
    ) -> dict[str, Any]:
        """Bookkeep order and optionally distribute invoice via email or EHF."""
        return self._get_distribution_service().bookkeep_and_distribute(
            order_id=order_id,
            bookkeep_data=bookkeep_data,
            distribution=distribution,
            email_to_addresses=email_to_addresses,
            email_subject=email_subject,
            email_body_text=email_body_text,
            email_include_signature=email_include_signature,
            email_document_ids=email_document_ids,
            ehf_recipient_address=ehf_recipient_address,
            ehf_recipient_address_type=ehf_recipient_address_type,
            ehf_party_identifications=ehf_party_identifications,
        )

    def create_simple_order(
        self,
        *,
        customer_account_number: int,
        our_reference: str | None = None,
        your_reference: str | None = None,
        order_date: DateInput | None = None,
        gln_number: str | None = None,
        task_description: str | None = None,
        task_details: str | None = None,
        task_internal_note: str | None = None,
        lines: list[dict[str, Any]] | None = None,
        hydrate_partner: bool = True,
        hydrate_articles: bool = True,
    ) -> dict[str, Any]:
        """Create a sales order in one call with simple business-friendly inputs.

        The implementation mirrors observed API behavior where reliable creation may require:
        1) create order header payload
        2) update final header fields on the created order
        3) create order lines on the resolved order task
        """

        partner_data = self._as_dict(self._get_partner_workflow().get_by_account_number(customer_account_number))
        partner_id_obj = partner_data.get("Id")
        if not isinstance(partner_id_obj, int):
            raise OrderWriteError("Could not resolve PartnerId from customer_account_number")

        hydrator = self.new_hydrator()
        hydrator.set_customer(partner_id_obj)
        if order_date is not None:
            # DateDays is what persisted in observed live behavior.
            hydrator.set_order_date(order_date)
        hydrator.set_customer_fields(
            account_number=customer_account_number,
            our_reference=our_reference,
            your_reference=your_reference,
            gln_number=gln_number,
        )

        if lines:
            for line in lines:
                hydrator.add_order_line(line)

        assist = self.assist_hydrate(
            hydrator,
            hydrate_partner=hydrate_partner,
            hydrate_articles=hydrate_articles,
        )

        created_order = self.create_hydrated(hydrator)
        created_order_dict = self._as_dict(created_order)
        order_id_obj = created_order_dict.get("Id")
        if not isinstance(order_id_obj, int):
            raise OrderWriteError("Unexpected create response shape: missing integer Id")

        # Ensure explicit caller fields persist on header in all environments.
        # Some tenants reject sparse update payloads; start from full DTO baseline.
        update_hydrator = self.new_hydrator(created_order_dict)
        if order_date is not None:
            update_hydrator.set_order_date(order_date)
        update_hydrator.set_customer_fields(
            account_number=customer_account_number,
            our_reference=our_reference,
            your_reference=your_reference,
            gln_number=gln_number,
        )

        updated_order = self.update_hydrated(order_id_obj, update_hydrator)

        updated_primary_task: dict[str, Any] | None = None
        if any(value is not None for value in (task_description, task_details, task_internal_note)):
            updated_primary_task = self.update_primary_task_for_order(
                order_id_obj,
                description=task_description,
                details=task_details,
                internal_note=task_internal_note,
                on_multiple="raise",
            )

        created_lines: list[dict[str, Any]] = []
        normalized_lines = hydrator.get_order_lines()
        if normalized_lines:
            task_id = self._get_primary_order_task_id(order_id_obj)
            for line in normalized_lines:
                created_lines.append(self._create_order_line(task_id=task_id, line=line))

        return {
            "order": self._as_dict(updated_order),
            "task": updated_primary_task,
            "lines": created_lines,
            "assist": assist,
        }

    def create_and_send_invoice_simple(
        self,
        *,
        customer_account_number: int,
        lines: list[dict[str, Any]],
        distribution: str | None = None,
        our_reference: str | None = None,
        your_reference: str | None = None,
        order_date: DateInput | None = None,
        gln_number: str | None = None,
        task_description: str | None = None,
        task_details: str | None = None,
        task_internal_note: str | None = None,
        email_to_addresses: str | None = None,
        email_subject: str | None = None,
        email_body_text: str | None = None,
        email_include_signature: bool = True,
        email_document_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Create order and invoice it with optional distribution.

        Distribution fallback rules:
        - email: requires resolved recipient email (explicit or order InvoiceEmail)
        - ehf: requires GLN on order (or explicit gln_number)
        If validation fails, invoice is still created via bookkeep but distribution is skipped.
        """

        created = self.create_simple_order(
            customer_account_number=customer_account_number,
            our_reference=our_reference,
            your_reference=your_reference,
            order_date=order_date,
            gln_number=gln_number,
            task_description=task_description,
            task_details=task_details,
            task_internal_note=task_internal_note,
            lines=lines,
        )

        order = self._as_dict(created.get("order"))
        order_id_obj = order.get("Id")
        if not isinstance(order_id_obj, int):
            raise OrderWriteError("Unexpected create_simple_order response: missing order Id")

        requested_distribution = (distribution or "none").strip().lower()
        if requested_distribution not in SUPPORTED_DISTRIBUTION_MODES:
            raise OrderDistributionError("distribution must be one of: none, email, ehf")

        effective_distribution = requested_distribution
        skipped_reason: str | None = None

        resolved_email = email_to_addresses
        if self._is_missing(resolved_email):
            invoice_email = order.get("InvoiceEmail")
            if isinstance(invoice_email, str) and invoice_email.strip():
                resolved_email = invoice_email.strip()

        resolved_gln = gln_number
        if self._is_missing(resolved_gln):
            gln_from_order = order.get("GLNNumber")
            if isinstance(gln_from_order, str) and gln_from_order.strip():
                resolved_gln = gln_from_order.strip()

        if requested_distribution == "email" and self._is_missing(resolved_email):
            effective_distribution = "none"
            skipped_reason = "Email distribution skipped: missing recipient email"

        if requested_distribution == "ehf" and self._is_missing(resolved_gln):
            effective_distribution = "none"
            skipped_reason = "EHF distribution skipped: missing GLN"

        invoicing_date_obj = order.get("DateDays")
        invoicing_date = int(invoicing_date_obj) if isinstance(invoicing_date_obj, int) else to_fiscal_date_int(date.today())
        version_obj = order.get("Version")
        version = int(version_obj) if isinstance(version_obj, int) else 1

        distribution_result = self.bookkeep_and_distribute(
            order_id_obj,
            bookkeep_data={
                "version": version,
                "invoicingDate": invoicing_date,
                "invoiceReportLayoutId": None,
                "doDeliver": False,
                "deliveryReportLayoutId": None,
                "supplierInvoiceNumber": None,
                "orderStatusId": None,
            },
            distribution=effective_distribution,
            email_to_addresses=resolved_email,
            email_subject=email_subject,
            email_body_text=email_body_text,
            email_include_signature=email_include_signature,
            email_document_ids=email_document_ids,
            ehf_recipient_address=(
                None
                if self._is_missing(resolved_gln)
                else f"NO{str(cast(str, resolved_gln)).removeprefix('NO')}"
            ),
        )

        return {
            "create": created,
            "invoice": distribution_result,
            "distribution_requested": requested_distribution,
            "distribution_effective": effective_distribution,
            "distribution_skipped_reason": skipped_reason,
            "resolved": {
                "email_to_addresses": resolved_email,
                "gln_number": resolved_gln,
            },
        }

    def create_invoice_by_number(
        self,
        invoice_number: int | str,
        date: DateInput | None = None,
        distribution: str | None = None,
        *,
        email_to_addresses: str | None = None,
        email_subject: str | None = None,
        email_body_text: str | None = None,
        email_include_signature: bool = True,
        email_document_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Create a reversing invoice from an existing invoice number.

        Behavior:
        - Resolves the source invoice and related order/task lines.
        - Builds mirrored lines with negated quantities.
        - Uses source invoice date by default; override with date=...
        - Creates and invoices the reversal order, with optional distribution.
        """

        requested_distribution = (distribution or "none").strip().lower()
        if requested_distribution not in SUPPORTED_DISTRIBUTION_MODES:
            raise OrderDistributionError("distribution must be one of: none, email, ehf")

        source_invoice = self._get_invoice_entity_by_number(invoice_number)
        source_order_id = source_invoice.get("OrderId")
        if not isinstance(source_order_id, int):
            raise OrderWriteError("Could not resolve source OrderId from invoice")

        source_order = self._get_order_by_id(source_order_id)
        source_task_id = self._get_order_task_id_for_voucher(source_order_id, int(source_invoice["VoucherNumber"]))
        source_lines = self._get_order_lines_by_task(source_task_id)
        mirrored_lines = self._build_mirrored_lines(source_lines)
        if not mirrored_lines:
            raise OrderWriteError("Could not build reversal lines from source invoice")

        source_invoice_date_days = self._resolve_source_invoice_date_days(source_invoice)
        selected_date: DateInput = date if date is not None else source_invoice_date_days

        partner_account_number = source_order.get("PartnerAccountNumber")
        if not isinstance(partner_account_number, int):
            raise OrderWriteError("Could not resolve PartnerAccountNumber from source order")

        result = self.create_and_send_invoice_simple(
            customer_account_number=partner_account_number,
            lines=mirrored_lines,
            distribution=requested_distribution,
            our_reference=cast(str | None, source_order.get("OurReference")),
            your_reference=cast(str | None, source_order.get("YourReference")),
            order_date=selected_date,
            gln_number=cast(str | None, source_order.get("GLNNumber")),
            email_to_addresses=email_to_addresses,
            email_subject=email_subject,
            email_body_text=email_body_text,
            email_include_signature=email_include_signature,
            email_document_ids=email_document_ids,
        )

        reverse_order = self._as_dict(cast(dict[str, Any], result.get("create", {})).get("order"))
        reverse_order_id = reverse_order.get("Id")
        if not isinstance(reverse_order_id, int):
            raise OrderWriteError("Could not resolve reverse order id after creating reversal invoice")

        reverse_invoice = self._get_latest_invoice_entity_by_order_id(reverse_order_id)

        settlement = self._settle_reverse_invoice_if_possible(
            source_invoice=source_invoice,
            reverse_invoice=reverse_invoice,
            pay_date=selected_date,
        )

        return {
            "source": {
                "invoice_number": source_invoice.get("VoucherNumber"),
                "order_id": source_order_id,
                "task_id": source_task_id,
                "invoice_date_days": source_invoice_date_days,
                "line_count": len(source_lines),
                "invoice_post_id": source_invoice.get("Id"),
            },
            "settlement": settlement,
            "reverse": result,
        }

    def _get_invoice_entity_by_number(self, invoice_number: int | str) -> dict[str, Any]:
        lookup = str(invoice_number).strip()
        if not lookup:
            raise OrderWriteError("invoice_number must not be empty")

        payload = self._client.order.api_order__get_invoice_get__api__fiscal_fiscal_id__order__invoice(
            fiscal_id=self._fiscal_id,
            filter_query_string=lookup,
            filter_context_type="ContextType_Customer",
            filter_deliver_filter=None,
            filter_is_settled=None,
            filter_partner_id=None,
            filter_order_status_id=None,
            filter_responsible_id=None,
            filter_limit_to_responsible=None,
            filter_date_from=None,
            filter_date_to=None,
            list_options_show_deactivated=False,
            list_options_page=0,
            list_options_page_size=100,
            list_options_force_no_paging=True,
        )
        payload_dict = self._as_dict(payload)
        entities_obj = payload_dict.get("Entities")
        if not isinstance(entities_obj, list):
            raise OrderWriteError("Unexpected invoice lookup response shape")

        target = int(lookup) if lookup.isdigit() else None
        matches = [
            cast(dict[str, Any], entity)
            for entity in entities_obj
            if isinstance(entity, dict)
            and (
                (target is not None and entity.get("VoucherNumber") == target)
                or str(entity.get("VoucherNumber", "")).strip() == lookup
            )
        ]
        if not matches:
            # Some tenants do not return older invoices reliably through filter_query_string.
            # Fall back to a full no-paging fetch and match by voucher number locally.
            all_payload = self._client.order.api_order__get_invoice_get__api__fiscal_fiscal_id__order__invoice(
                fiscal_id=self._fiscal_id,
                filter_query_string=None,
                filter_context_type="ContextType_Customer",
                filter_deliver_filter=None,
                filter_is_settled=None,
                filter_partner_id=None,
                filter_order_status_id=None,
                filter_responsible_id=None,
                filter_limit_to_responsible=None,
                filter_date_from=None,
                filter_date_to=None,
                list_options_show_deactivated=False,
                list_options_page=0,
                list_options_page_size=100,
                list_options_force_no_paging=True,
            )
            all_dict = self._as_dict(all_payload)
            all_entities_obj = all_dict.get("Entities")
            all_entities = all_entities_obj if isinstance(all_entities_obj, list) else []
            matches = [
                cast(dict[str, Any], entity)
                for entity in all_entities
                if isinstance(entity, dict)
                and (
                    (target is not None and entity.get("VoucherNumber") == target)
                    or str(entity.get("VoucherNumber", "")).strip() == lookup
                )
            ]
        if not matches:
            raise OrderWriteError(f"No invoice found for invoice_number '{lookup}'")
        if len(matches) > 1:
            raise OrderWriteError(f"More than one invoice matched invoice_number '{lookup}'")

        voucher = matches[0].get("VoucherNumber")
        if not isinstance(voucher, int):
            raise OrderWriteError("Matched invoice did not contain an integer VoucherNumber")
        return matches[0]

    def _get_order_by_id(self, order_id: int) -> dict[str, Any]:
        payload = self._client.order.api_order__get_get__api__fiscal_fiscal_id__order_id(
            id=order_id,
            fiscal_id=self._fiscal_id,
        )
        return self._as_dict(payload)

    def _get_order_task_id_for_voucher(self, order_id: int, voucher_number: int) -> int:
        tasks_payload = self._client.order.api_order_task__get_by_order_get__api__fiscal_fiscal_id__order_id__order_task(
            id=order_id,
            fiscal_id=self._fiscal_id,
            list_options_force_no_paging=True,
        )
        tasks_dict = self._as_dict(tasks_payload)
        entities_obj = tasks_dict.get("Entities")
        if not isinstance(entities_obj, list) or not entities_obj:
            raise OrderWriteError("Could not resolve source order tasks for invoice lookup")

        matching_task_ids: list[int] = []
        for task in entities_obj:
            if not isinstance(task, dict):
                continue
            task_id = task.get("Id")
            if not isinstance(task_id, int):
                continue

            journals_payload = self._client.order.api_order_task__get_journal_get__api__fiscal_fiscal_id__order_task_id__journal(
                id=task_id,
                fiscal_id=self._fiscal_id,
                list_options_force_no_paging=True,
            )
            journals_dict = self._as_dict(journals_payload)
            journals_obj = journals_dict.get("Entities")
            journals = journals_obj if isinstance(journals_obj, list) else []
            has_voucher = any(
                isinstance(journal, dict) and journal.get("VoucherNumber") == voucher_number
                for journal in journals
            )
            if has_voucher:
                matching_task_ids.append(task_id)

        if not matching_task_ids:
            raise OrderWriteError(
                f"Could not resolve source order task for voucher {voucher_number}"
            )
        if len(matching_task_ids) > 1:
            raise OrderWriteError(
                f"Voucher {voucher_number} matched multiple order tasks: {matching_task_ids}"
            )
        return matching_task_ids[0]

    def _get_order_lines_by_task(self, task_id: int) -> list[dict[str, Any]]:
        payload = self._client.order.api_order_line__get_by_order_task_get__api__fiscal_fiscal_id__order_task_id__order_line(
            id=task_id,
            fiscal_id=self._fiscal_id,
            list_options_force_no_paging=True,
        )
        payload_dict = self._as_dict(payload)
        entities_obj = payload_dict.get("Entities")
        if not isinstance(entities_obj, list):
            raise OrderWriteError("Unexpected order line response shape for source task")
        return [cast(dict[str, Any], line) for line in entities_obj if isinstance(line, dict)]

    def _build_mirrored_lines(self, source_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        mirrored: list[dict[str, Any]] = []
        for source in source_lines:
            quantity_obj = source.get("Quantity")
            if not isinstance(quantity_obj, (int, float)):
                continue
            quantity = float(quantity_obj)
            if quantity == 0:
                continue

            line: dict[str, Any] = {
                "quantity": -quantity,
            }

            article_number = source.get("ArticleNumber")
            article_id = source.get("ArticleId")
            if isinstance(article_number, (str, int)) and str(article_number).strip():
                line["article_number"] = str(article_number)
            elif isinstance(article_id, int):
                line["article_id"] = article_id
            else:
                continue

            price_each = source.get("PriceEach")
            if not isinstance(price_each, (int, float)):
                price_each = source.get("UnitNetPrice")
            if isinstance(price_each, (int, float)):
                line["price_each"] = float(price_each)

            description = source.get("Description")
            if isinstance(description, str) and description.strip():
                line["description"] = description

            vat_id = source.get("VatId")
            if isinstance(vat_id, int):
                line["vat_id"] = vat_id

            unit_id = source.get("UnitId")
            if isinstance(unit_id, int):
                line["unit_id"] = unit_id

            discount_percent = source.get("DiscountPercent")
            if isinstance(discount_percent, (int, float)):
                line["discount_percent"] = float(discount_percent)

            delivery_date_days = source.get("DeliveryDateDays")
            if isinstance(delivery_date_days, int):
                line["delivery_date"] = delivery_date_days

            mirrored.append(line)

        return mirrored

    def _resolve_source_invoice_date_days(self, invoice_entity: dict[str, Any]) -> int:
        journal_obj = invoice_entity.get("Journal")
        if isinstance(journal_obj, dict):
            invoicing_date_days = journal_obj.get("InvoicingDateDays")
            if isinstance(invoicing_date_days, int):
                return invoicing_date_days

        fiscal_date_days = invoice_entity.get("FiscalDateDays")
        if isinstance(fiscal_date_days, int):
            return fiscal_date_days

        raise OrderWriteError("Could not resolve source invoice date for reversal")

    def _get_latest_invoice_entity_by_order_id(self, order_id: int) -> dict[str, Any]:
        payload = self._client.order.api_order__get_invoice_get__api__fiscal_fiscal_id__order__invoice(
            fiscal_id=self._fiscal_id,
            filter_query_string="",
            filter_context_type="ContextType_Customer",
            filter_deliver_filter=None,
            filter_is_settled=None,
            filter_partner_id=None,
            filter_order_status_id=None,
            filter_responsible_id=None,
            filter_limit_to_responsible=None,
            filter_date_from=None,
            filter_date_to=None,
            list_options_show_deactivated=False,
            list_options_page=0,
            list_options_page_size=100,
            list_options_force_no_paging=True,
        )
        payload_dict = self._as_dict(payload)
        entities_obj = payload_dict.get("Entities")
        if not isinstance(entities_obj, list):
            raise OrderWriteError("Unexpected invoice list response shape while resolving reverse invoice")

        matches = [
            cast(dict[str, Any], entity)
            for entity in entities_obj
            if isinstance(entity, dict) and entity.get("OrderId") == order_id
        ]
        if not matches:
            raise OrderWriteError(f"Could not resolve reverse invoice for order id {order_id}")

        # If more than one invoice exists for the order, pick the newest by voucher number.
        return sorted(
            matches,
            key=lambda entity: int(cast(int, entity.get("VoucherNumber")))
            if isinstance(entity.get("VoucherNumber"), int)
            else -1,
        )[-1]

    def _settle_reverse_invoice_if_possible(
        self,
        *,
        source_invoice: dict[str, Any],
        reverse_invoice: dict[str, Any],
        pay_date: DateInput,
    ) -> dict[str, Any]:
        source_post_id = source_invoice.get("Id")
        reverse_post_id = reverse_invoice.get("Id")
        source_voucher = source_invoice.get("VoucherNumber")
        reverse_voucher = reverse_invoice.get("VoucherNumber")
        partner_id = source_invoice.get("PartnerId")

        if not isinstance(source_voucher, int) or not isinstance(reverse_voucher, int):
            return {
                "attempted": False,
                "settled": False,
                "reason": "Could not resolve voucher numbers for settlement",
                "invoice_post_ids": [source_post_id, reverse_post_id],
                "invoice_voucher_numbers": [source_voucher, reverse_voucher],
            }
        if not isinstance(partner_id, int):
            return {
                "attempted": False,
                "settled": False,
                "reason": "Could not resolve partner id for settlement",
                "invoice_post_ids": [source_post_id, reverse_post_id],
                "invoice_voucher_numbers": [source_voucher, reverse_voucher],
            }

        unsettled_payload = self._client.finance.api_payment__get_unsettled_partner_post_get__api__fiscal_fiscal_id__partner_id__unsettled_post(
            id=partner_id,
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=False,
            list_options_page=0,
            list_options_page_size=100,
            list_options_force_no_paging=True,
        )
        unsettled_dict = self._as_dict(unsettled_payload)
        unsettled_obj = unsettled_dict.get("Entities")
        unsettled_entities = unsettled_obj if isinstance(unsettled_obj, list) else []

        selected_rows = [
            cast(dict[str, Any], row)
            for row in unsettled_entities
            if isinstance(row, dict) and row.get("VoucherNumber") in (source_voucher, reverse_voucher)
        ]
        selected_ids = [
            cast(int, row.get("Id"))
            for row in selected_rows
            if isinstance(row.get("Id"), int)
        ]
        selected_vouchers = {
            cast(int, row.get("VoucherNumber"))
            for row in selected_rows
            if isinstance(row.get("VoucherNumber"), int)
        }
        missing_vouchers = [
            voucher for voucher in (source_voucher, reverse_voucher) if voucher not in selected_vouchers
        ]
        if len(selected_ids) != 2 or missing_vouchers:
            return {
                "attempted": False,
                "settled": False,
                "reason": f"Could not resolve unsettled partner posts for vouchers: {missing_vouchers or [source_voucher, reverse_voucher]}",
                "invoice_post_ids": [source_post_id, reverse_post_id],
                "invoice_voucher_numbers": [source_voucher, reverse_voucher],
                "partner_post_ids": selected_ids,
            }
        currency_values = {
            str(row.get("CurrencyAbbreviation")).strip()
            for row in selected_rows
            if row.get("CurrencyAbbreviation") is not None and str(row.get("CurrencyAbbreviation")).strip()
        }
        if len(currency_values) > 1:
            return {
                "attempted": False,
                "settled": False,
                "reason": f"Mixed currencies in selected posts: {sorted(currency_values)}",
                "partner_post_ids": selected_ids,
            }

        total = Decimal("0")
        for row in selected_rows:
            remaining_amount = row.get("RemainingAmount")
            amount = row.get("Amount")
            numeric = remaining_amount if remaining_amount is not None else amount
            total += self._as_decimal(numeric)

        if total != Decimal("0"):
            return {
                "attempted": False,
                "settled": False,
                "reason": f"Selected posts are not balanced (sum={total})",
                "partner_post_ids": selected_ids,
            }

        tag_payload = self._client.finance.api_ledger_tag__get_currency_difference_tag_get__api__fiscal_fiscal_id__ledger_tag__currency_difference_tag(
            fiscal_id=self._fiscal_id,
            list_options_force_no_paging=True,
        )
        tag_dict = self._as_dict(tag_payload)
        tag_entities_obj = tag_dict.get("Entities")
        tag_entities = tag_entities_obj if isinstance(tag_entities_obj, list) else []
        if not tag_entities or not isinstance(tag_entities[0], dict):
            return {
                "attempted": False,
                "settled": False,
                "reason": "Currency difference tag not found",
                "partner_post_ids": selected_ids,
            }

        tag = cast(dict[str, Any], tag_entities[0])
        tag_id = tag.get("Id")
        if not isinstance(tag_id, int):
            return {
                "attempted": False,
                "settled": False,
                "reason": "Currency difference tag missing integer Id",
                "partner_post_ids": selected_ids,
            }

        currency_abbreviation = next(iter(currency_values), "NOK")
        ledger_tag_number = tag.get("LedgerTagNumber")
        if ledger_tag_number is None:
            ledger_tag_number = tag.get("Number")

        pay_payload = {
            "ledgerPosts": [
                {
                    "LedgerTagId": tag_id,
                    "LedgerTagNumber": ledger_tag_number,
                    "LedgerTagDescription": tag.get("Description"),
                    "Amount": 0,
                }
            ],
            "currencyAbbreviation": currency_abbreviation,
            "partnerPostIds": selected_ids,
            "payDate": to_fiscal_date_int(pay_date),
            "partialSettleId": selected_ids[0],
        }

        pay_result = self._client.order.api_order__put_pay_put__api__fiscal_fiscal_id__order__pay(
            pay_data=pay_payload,
            fiscal_id=self._fiscal_id,
        )

        return {
            "attempted": True,
            "settled": True,
            "invoice_post_ids": [source_post_id, reverse_post_id],
            "invoice_voucher_numbers": [source_voucher, reverse_voucher],
            "partner_post_ids": selected_ids,
            "payload": pay_payload,
            "result": self._as_dict(pay_result) if not isinstance(pay_result, dict) else pay_result,
        }

    @staticmethod
    def _as_decimal(value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float, str)):
            return Decimal(str(value))
        raise OrderWriteError(f"Unsupported numeric settlement value: {value!r}")

    def _resolve_partner_for_hydration(self, hydrator: OrderDtoHydrator) -> dict[str, Any] | None:
        partner_id = hydrator.get_field("PartnerId")
        partner_account_number = hydrator.get_field("PartnerAccountNumber")

        partner_raw: Any | None = None
        partner_workflow = self._get_partner_workflow()

        if isinstance(partner_id, int):
            partner_raw = partner_workflow.get_by_id(partner_id)
        elif isinstance(partner_account_number, int):
            partner_raw = partner_workflow.get_by_account_number(partner_account_number)
        elif isinstance(partner_account_number, str) and partner_account_number.strip().isdigit():
            partner_raw = partner_workflow.get_by_account_number(int(partner_account_number.strip()))
        else:
            return None

        return self._as_dict(partner_raw)

    def _get_primary_order_task_id(self, order_id: int) -> int:
        primary_task = self._resolve_primary_task_entity(order_id, on_multiple="first")
        task_id_obj = primary_task.get("Id")
        if not isinstance(task_id_obj, int):
            raise OrderWriteError("Unexpected order task response shape: missing integer Id")
        return task_id_obj

    def _get_order_tasks_by_order(self, order_id: int) -> list[dict[str, Any]]:
        tasks_payload = self._client.order.api_order_task__get_by_order_get__api__fiscal_fiscal_id__order_id__order_task(
            id=order_id,
            fiscal_id=self._fiscal_id,
            list_options_force_no_paging=True,
        )
        tasks_dict = self._as_dict(tasks_payload)
        entities_obj = tasks_dict.get("Entities")
        if not isinstance(entities_obj, list):
            raise OrderWriteError("Unexpected order task response shape")
        return [cast(dict[str, Any], entity) for entity in entities_obj if isinstance(entity, dict)]

    def _get_order_task_by_id(self, task_id: int) -> dict[str, Any] | None:
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
                    )
                )
        return None

    def _resolve_primary_task_entity(
        self,
        order_id: int,
        *,
        on_multiple: str,
    ) -> dict[str, Any]:
        tasks = self._get_order_tasks_by_order(order_id)
        if not tasks:
            raise OrderWriteError(f"Could not resolve order task for order id {order_id}")
        if len(tasks) > 1:
            if on_multiple == "first":
                return tasks[0]
            if on_multiple != "raise":
                raise OrderWriteError("on_multiple must be one of: raise, first")
            raise OrderWriteError(
                f"More than one order task matched order id {order_id}; set on_multiple='first' to pick first task"
            )
        return tasks[0]

    def _create_order_line(self, *, task_id: int, line: dict[str, Any]) -> dict[str, Any]:
        line_dto = dict(line)
        line_dto["OrderTaskId"] = task_id

        if self._is_missing(line_dto.get("ArticleId")) and not self._is_missing(line_dto.get("ArticleNumber")):
            article_data = self._as_dict(self._get_article_workflow().get_by_number(str(line_dto["ArticleNumber"])))
            article_id_obj = article_data.get("Id")
            if isinstance(article_id_obj, int):
                line_dto["ArticleId"] = article_id_obj

        if self._is_missing(line_dto.get("UnitNetPrice")) and not self._is_missing(line_dto.get("PriceEach")):
            line_dto["UnitNetPrice"] = line_dto["PriceEach"]

        if self._is_missing(line_dto.get("Quantity")):
            line_dto["Quantity"] = 1

        created_line = self._client.order.api_order_line__post_post__api__fiscal_fiscal_id__order_line(
            line_dto=line_dto,
            fiscal_id=self._fiscal_id,
        )
        return self._as_dict(created_line)

    def _hydrate_partner_defaults(
        self,
        hydrator: OrderDtoHydrator,
        partner_data: dict[str, Any],
    ) -> list[str]:
        filled: list[str] = []
        address_obj = partner_data.get("Address")
        address = cast(dict[str, Any], address_obj) if isinstance(address_obj, dict) else None

        partner_name = None
        if address is not None and isinstance(address.get("Name"), str) and address.get("Name", "").strip():
            partner_name = str(address["Name"])
        elif isinstance(partner_data.get("LongDescription"), str):
            long_desc = str(partner_data.get("LongDescription"))
            parts = [part.strip() for part in long_desc.split(" - ", 1)]
            partner_name = parts[-1] if parts else long_desc
        elif isinstance(partner_data.get("ShortDescription"), str):
            partner_name = str(partner_data.get("ShortDescription"))

        partner_defaults: dict[str, Any] = {
            "PartnerId": partner_data.get("Id"),
            "PartnerAccountNumber": partner_data.get("AccountNumber"),
            "PartnerName": partner_name,
            "InvoiceEmail": partner_data.get("PartnerCustomerContextInvoiceMail"),
            "PartnerPhoneNumber": partner_data.get("PhoneNumber"),
            "PartnerAttention": partner_data.get("Attention"),
            "PartnerNote": partner_data.get("Note"),
            "GLNNumber": partner_data.get("GLNNumber"),
            "PartnerType": partner_data.get("PartnerType"),
            "PartnerIsVatExcept": partner_data.get("IsVatExcept"),
        }

        for key, value in partner_defaults.items():
            if self._is_missing(hydrator.get_field(key)) and not self._is_missing(value):
                hydrator.set_field(key, value)
                filled.append(key)

        if address is not None:
            current_address_obj = hydrator.get_field("Address")
            if isinstance(current_address_obj, dict):
                merged_address = dict(cast(dict[str, Any], current_address_obj))
                merged_filled_keys: list[str] = []

                for key, value in address.items():
                    if self._is_missing(merged_address.get(key)) and not self._is_missing(value):
                        merged_address[key] = value
                        merged_filled_keys.append(key)

                if merged_filled_keys:
                    hydrator.set_field("Address", merged_address)
                    filled.append("Address." + ",".join(sorted(merged_filled_keys)))
            elif self._is_missing(current_address_obj):
                hydrator.set_field("Address", dict(address))
                filled.append("Address")

        return filled

    def _hydrate_article_defaults(self, hydrator: OrderDtoHydrator) -> list[dict[str, Any]]:
        lines = hydrator.get_order_lines_ref()
        article_workflow = self._get_article_workflow()
        result: list[dict[str, Any]] = []

        for index, line in enumerate(lines):
            normalized_line = hydrator.normalize_order_line_input(line)
            line.clear()
            line.update(normalized_line)

            article_raw: Any | None = None

            article_id = line.get("ArticleId")
            article_number = line.get("ArticleNumber")

            if isinstance(article_id, int):
                article_raw = article_workflow.get_by_id(article_id)
            elif isinstance(article_number, (str, int)):
                article_raw = article_workflow.get_by_number(str(article_number))
            else:
                continue

            article = self._as_dict(article_raw)
            line_filled: list[str] = []

            mapping: dict[str, Any] = {
                "ArticleId": article.get("Id"),
                "ArticleNumber": article.get("ArticleNumber"),
                "Description": article.get("Description") or article.get("Abbreviation"),
            }

            sales_setup_obj = article.get("SalesSetup")
            sales_setup = cast(dict[str, Any], sales_setup_obj) if isinstance(sales_setup_obj, dict) else {}
            mapping["UnitId"] = sales_setup.get("DefaultUnitId")
            mapping["Quantity"] = sales_setup.get("DefaultQuantity")

            # Price defaults can appear under different key names in generated payloads.
            for price_key in ("PriceEach", "SalesPrice", "SalesPriceEach", "UnitPrice"):
                if not self._is_missing(sales_setup.get(price_key)):
                    mapping["PriceEach"] = sales_setup.get(price_key)
                    break
            if "PriceEach" not in mapping and not self._is_missing(article.get("PriceEach")):
                mapping["PriceEach"] = article.get("PriceEach")

            for key, value in mapping.items():
                if self._is_missing(line.get(key)) and not self._is_missing(value):
                    line[key] = value
                    line_filled.append(key)

            if not self._is_missing(line.get("PriceEach")) and not self._is_missing(line.get("Quantity")):
                totals_obj = line.get("Totals")
                if not isinstance(totals_obj, dict):
                    line["Totals"] = {}
                totals = cast(dict[str, Any], line["Totals"])
                if self._is_missing(totals.get("PriceNettTotal")):
                    computed = OrderDtoHydrator.build_line_totals(
                        quantity=float(cast(float | int, line["Quantity"])),
                        price_each=float(cast(float | int, line["PriceEach"])),
                        discount_pct=0,
                    )
                    if computed is not None:
                        totals.update(computed)
                        line_filled.append("Totals")

            if line_filled:
                result.append({"index": index, "fields": line_filled})

        return result

    def _get_partner_workflow(self) -> PartnerWorkflow:
        if self._partner_workflow is None:
            self._partner_workflow = PartnerWorkflow(self._client, self._fiscal_id)
        return self._partner_workflow

    def _get_article_workflow(self) -> ArticleWorkflow:
        if self._article_workflow is None:
            self._article_workflow = ArticleWorkflow(self._client, self._fiscal_id)
        return self._article_workflow

    def _get_distribution_service(self) -> OrderDistributionService:
        if self._distribution_service is None:
            self._distribution_service = OrderDistributionService(self._client, self._fiscal_id)
        return self._distribution_service

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return cast(dict[str, Any], value)
        to_dict = getattr(value, "to_dict", None)
        if callable(to_dict):
            converted = to_dict()
            if isinstance(converted, dict):
                return cast(dict[str, Any], converted)
        raise OrderWriteHydrationError("Expected dict-like payload during assisted hydration")

    @staticmethod
    def _is_missing(value: Any) -> bool:
        return value is None or value == ""
