from __future__ import annotations

from datetime import date
from dataclasses import dataclass
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
    """Write workflow helper for explicit order mutations and transitions."""

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

        created_lines: list[dict[str, Any]] = []
        normalized_lines = hydrator.get_order_lines()
        if normalized_lines:
            task_id = self._get_primary_order_task_id(order_id_obj)
            for line in normalized_lines:
                created_lines.append(self._create_order_line(task_id=task_id, line=line))

        return {
            "order": self._as_dict(updated_order),
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
        tasks_payload = self._client.order.api_order_task__get_by_order_get__api__fiscal_fiscal_id__order_id__order_task(
            id=order_id,
            fiscal_id=self._fiscal_id,
            list_options_force_no_paging=True,
        )
        tasks_dict = self._as_dict(tasks_payload)
        entities_obj = tasks_dict.get("Entities")
        if not isinstance(entities_obj, list) or not entities_obj:
            raise OrderWriteError("Could not resolve order task for created order")

        entities = cast(list[Any], entities_obj)
        first_obj = entities[0]
        if not isinstance(first_obj, dict):
            raise OrderWriteError("Unexpected order task response shape")
        first = cast(dict[str, Any], first_obj)

        task_id_obj = first.get("Id")
        if not isinstance(task_id_obj, int):
            raise OrderWriteError("Unexpected order task response shape: missing integer Id")
        return task_id_obj

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
