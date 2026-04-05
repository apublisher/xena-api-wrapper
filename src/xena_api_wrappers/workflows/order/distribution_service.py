from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from .distribution_policy import DEFAULT_EHF_RECIPIENT_ADDRESS_TYPE, SUPPORTED_DISTRIBUTION_MODES
from .order_errors import OrderDistributionError, OrderWriteHydrationError


@dataclass
class OrderDistributionService:
    _client: Any
    _fiscal_id: str

    def bookkeep_and_distribute(
        self,
        *,
        order_id: int,
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
        mode = (distribution or "none").strip().lower()
        if mode not in SUPPORTED_DISTRIBUTION_MODES:
            raise OrderDistributionError("distribution must be one of: none, email, ehf")

        bookkeep_result = self._client.order.api_order__put_bookkeep_put__api__fiscal_fiscal_id__order_id__bookkeep(
            id=order_id,
            bookkeep_data=bookkeep_data,
            fiscal_id=self._fiscal_id,
        )
        response: dict[str, Any] = {
            "bookkeep": self._as_dict(bookkeep_result),
            "distribution": mode,
            "distribution_result": None,
            "distribution_payload": None,
        }

        if mode == "none":
            return response

        if mode == "email":
            payload = self.build_email_send_payload(
                order_id=order_id,
                to_addresses=email_to_addresses,
                subject=email_subject,
                body_text=email_body_text,
                include_signature=email_include_signature,
                document_ids=email_document_ids,
            )
            result = self.send_email_payload(payload)
            response["distribution_payload"] = payload
            response["distribution_result"] = result
            return response

        payload = self.build_ehf_send_payload(
            order_id=order_id,
            recipient_address=ehf_recipient_address,
            recipient_address_type=ehf_recipient_address_type,
            party_identifications=ehf_party_identifications,
        )
        result = self._client.order.api_order__put_send_electronic_invoices_put__api__fiscal_fiscal_id__order__invoice__send_electronic_invoice(
            invoice_data=payload,
            fiscal_id=self._fiscal_id,
        )
        response["distribution_payload"] = payload
        response["distribution_result"] = self._as_dict(result)
        return response

    def get_order_journal_entries(self, order_id: int) -> list[dict[str, Any]]:
        payload = self._client.order.api_order__get_order_journal_get__api__fiscal_fiscal_id__order_id__journal(
            id=order_id,
            fiscal_id=self._fiscal_id,
            list_options_force_no_paging=True,
        )
        payload_dict = self._as_dict(payload)
        entities_obj = payload_dict.get("Entities")
        if not isinstance(entities_obj, list):
            raise OrderDistributionError("Unexpected order journal response shape")

        entities = cast(list[Any], entities_obj)
        return [cast(dict[str, Any], item) for item in entities if isinstance(item, dict)]

    def build_email_send_payload(
        self,
        *,
        order_id: int,
        to_addresses: str | None,
        subject: str | None,
        body_text: str | None,
        include_signature: bool,
        document_ids: list[int] | None,
    ) -> dict[str, Any]:
        if self._is_missing(to_addresses):
            raise OrderDistributionError("email_to_addresses is required for email distribution")

        journals = self.get_order_journal_entries(order_id)

        resolved_document_ids: list[int]
        if document_ids:
            resolved_document_ids = [int(doc_id) for doc_id in document_ids]
        else:
            ids: list[int] = []
            for entry in journals:
                document_id = entry.get("DocumentId")
                if isinstance(document_id, int):
                    ids.append(document_id)
            resolved_document_ids = ids

        if not resolved_document_ids:
            raise OrderDistributionError("Could not resolve invoice DocumentIds for email distribution")

        invoice_number: int | None = None
        for entry in journals:
            voucher = entry.get("VoucherNumber")
            if isinstance(voucher, int):
                invoice_number = voucher
                break

        resolved_subject = subject
        if self._is_missing(resolved_subject):
            resolved_subject = f"Faktura {invoice_number}" if invoice_number is not None else "Faktura"

        resolved_body = body_text
        if self._is_missing(resolved_body):
            resolved_body = "Vedlagt finner du faktura som avtalt.\n\nMed vennlig hilsen"

        return {
            "ToAddresses": str(to_addresses),
            "Subject": str(resolved_subject),
            "BodyText": str(resolved_body),
            "DocumentIds": resolved_document_ids,
            "IncludeSignature": bool(include_signature),
        }

    def send_email_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        order_api = self._client.order
        base_url = getattr(order_api, "base_url", None)
        session = getattr(order_api, "session", None)

        if not isinstance(base_url, str) or session is None:
            raise OrderDistributionError("Underlying client does not expose HTTP session for Email/Send")

        url = f"{base_url}/Api/Fiscal/{self._fiscal_id}/Email/Send"
        response = session.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, dict):
            return cast(dict[str, Any], result)
        return {"result": result}

    def build_ehf_send_payload(
        self,
        *,
        order_id: int,
        recipient_address: str | None,
        recipient_address_type: str,
        party_identifications: Any,
    ) -> dict[str, Any]:
        journals = self.get_order_journal_entries(order_id)
        journal_ids = [entry.get("Id") for entry in journals if isinstance(entry.get("Id"), int)]
        if not journal_ids:
            raise OrderDistributionError("Could not resolve journal ids for EHF distribution")

        defaults_payload = self._client.order.api_order__get_default_electronic_invoice_data_get__api__fiscal_fiscal_id__order__default_electronic_invoice_data(
            journal_ids=journal_ids,
            fiscal_id=self._fiscal_id,
        )
        defaults_dict = self._as_dict(defaults_payload)
        entities_obj = defaults_dict.get("Entities")
        if not isinstance(entities_obj, list) or not entities_obj or not isinstance(entities_obj[0], dict):
            raise OrderDistributionError("Could not resolve default electronic invoice data")

        defaults = cast(dict[str, Any], entities_obj[0])

        transaction_id = defaults.get("OrderInvoiceTransactionId")
        if not isinstance(transaction_id, int):
            raise OrderDistributionError("Missing OrderInvoiceTransactionId in electronic invoice defaults")

        invoice_number = defaults.get("InvoiceNumber")
        if not isinstance(invoice_number, int):
            raise OrderDistributionError("Missing InvoiceNumber in electronic invoice defaults")

        partner_name = defaults.get("PartnerName")
        if not isinstance(partner_name, str) or not partner_name.strip():
            raise OrderDistributionError("Missing PartnerName in electronic invoice defaults")

        partner_account_number = defaults.get("PartnerAccountNumber")
        if not isinstance(partner_account_number, int):
            raise OrderDistributionError("Missing PartnerAccountNumber in electronic invoice defaults")

        resolved_recipient = recipient_address
        if self._is_missing(resolved_recipient):
            base_recipient = defaults.get("GLNNumber") or defaults.get("RecipientAddress") or defaults.get("OrgNumber")
            if self._is_missing(base_recipient):
                raise OrderDistributionError(
                    "ehf_recipient_address is required when no GLN/recipient default is available"
                )
            normalized_base = str(base_recipient).strip()
            resolved_recipient = (
                normalized_base
                if normalized_base.upper().startswith("NO")
                else f"NO{normalized_base}"
            )

        return {
            "OrderInvoiceTransactionId": transaction_id,
            "PartnerName": partner_name,
            "PartnerAccountNumber": partner_account_number,
            "InvoiceNumber": invoice_number,
            "Endpoint": {
                "RecipientAddressType": recipient_address_type,
                "RecipientAddress": str(resolved_recipient),
            },
            "PartyIdentifications": party_identifications,
        }

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