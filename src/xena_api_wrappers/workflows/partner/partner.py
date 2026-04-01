from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, cast


class PartnerError(ValueError):
    """Base error for partner workflow operations."""


class PartnerNotFoundError(PartnerError):
    """Raised when a partner lookup returns no result."""


@dataclass
class PartnerAddressDTO:
    name: str | None = None
    street: str | None = None
    place_name: str | None = None
    zip: str | None = None
    city: str | None = None
    country_name: str | None = None

    def to_api_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.name is not None:
            payload["Name"] = self.name
        if self.street is not None:
            payload["Street"] = self.street
        if self.place_name is not None:
            payload["PlaceName"] = self.place_name
        if self.zip is not None:
            payload["Zip"] = self.zip
        if self.city is not None:
            payload["City"] = self.city
        if self.country_name is not None:
            payload["CountryName"] = self.country_name
        return payload


@dataclass
class PartnerDTO:
    short_description: str | None = None
    long_description: str | None = None
    attention: str | None = None
    phone_number: str | None = None
    note: str | None = None
    url: str | None = None
    gln_number: str | None = None
    org_number: str | None = None
    partner_type: str | None = None
    is_vat_except: bool | None = None
    address: PartnerAddressDTO | dict[str, Any] | None = None
    partner_customer_context_invoice_mail: str | None = None
    partner_supplier_context_invoice_mail: str | None = None
    partner_resource_context_sender_mail: str | None = None
    extra_fields: dict[str, Any] | None = None

    def to_api_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.short_description is not None:
            payload["ShortDescription"] = self.short_description
        if self.long_description is not None:
            payload["LongDescription"] = self.long_description
        if self.attention is not None:
            payload["Attention"] = self.attention
        if self.phone_number is not None:
            payload["PhoneNumber"] = self.phone_number
        if self.note is not None:
            payload["Note"] = self.note
        if self.url is not None:
            payload["URL"] = self.url
        if self.gln_number is not None:
            payload["GLNNumber"] = self.gln_number
        if self.org_number is not None:
            payload["OrgNumber"] = self.org_number
        if self.partner_type is not None:
            payload["PartnerType"] = self.partner_type
        if self.is_vat_except is not None:
            payload["IsVatExcept"] = self.is_vat_except
        if self.address is not None:
            if isinstance(self.address, PartnerAddressDTO):
                payload["Address"] = self.address.to_api_dict()
            else:
                payload["Address"] = dict(self.address)
        if self.partner_customer_context_invoice_mail is not None:
            payload["PartnerCustomerContextInvoiceMail"] = self.partner_customer_context_invoice_mail
        if self.partner_supplier_context_invoice_mail is not None:
            payload["PartnerSupplierContextInvoiceMail"] = self.partner_supplier_context_invoice_mail
        if self.partner_resource_context_sender_mail is not None:
            payload["PartnerResourceContextSenderMail"] = self.partner_resource_context_sender_mail
        if self.extra_fields:
            payload.update(self.extra_fields)
        return payload


_EMAIL_REGEX = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")


def _normalize_optional_email(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    if not _EMAIL_REGEX.match(trimmed):
        raise PartnerError(f"Invalid email format: {value}")
    return trimmed


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    return trimmed


def _normalize_partner_email_fields(dto: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(dto)
    for field in (
        "PartnerCustomerContextInvoiceMail",
        "PartnerSupplierContextInvoiceMail",
        "PartnerResourceContextSenderMail",
    ):
        if field in normalized:
            normalized[field] = _normalize_optional_email(normalized[field])
    return normalized


def _coerce_partner_payload(dto: PartnerDTO | dict[str, Any]) -> dict[str, Any]:
    if isinstance(dto, PartnerDTO):
        return dto.to_api_dict()
    return dict(dto)


def _extract_entities(payload: dict[str, Any]) -> list[dict[str, Any]] | None:
    entities_any = payload.get("Entities")
    if isinstance(entities_any, list):
        entities = cast(list[object], entities_any)
        return [cast(dict[str, Any], e) for e in entities if isinstance(e, dict)]
    return None


@dataclass
class PartnerWorkflow:
    """Workflow helper for partner list and detail operations."""

    _client: Any
    _fiscal_id: str

    def get_all(
        self,
        *,
        query_string: str | None = None,
        partner_context_type: str | None = "Customer",
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = False,
        excluded_id: int | None = None,
        include_default: bool | None = None,
    ) -> Any:
        return self._client.partner.api_partner__get_get__api__fiscal_fiscal_id__partner(
            fiscal_id=self._fiscal_id,
            query_string=query_string,
            excluded_id=excluded_id,
            include_default=include_default,
            partner_context_type=partner_context_type,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        raw: object = self.get_all(**kwargs)
        if isinstance(raw, dict):
            entities = _extract_entities(cast(dict[str, Any], raw))
            if entities is not None:
                return entities
        else:
            to_dict = getattr(raw, "to_dict", None)
            if callable(to_dict):
                converted = to_dict()
                if isinstance(converted, dict):
                    entities = _extract_entities(cast(dict[str, Any], converted))
                    if entities is not None:
                        return entities

        raise PartnerError("Unexpected Partner response shape: could not read Entities list")

    def get_by_id(self, partner_id: int) -> Any:
        return self._client.partner.api_partner__get_get__api__fiscal_fiscal_id__partner_id(
            id=partner_id,
            fiscal_id=self._fiscal_id,
        )

    def get_by_account_number(self, account_number: int) -> Any:
        return self._client.partner.api_partner__get_by_account_number_get__api__fiscal_fiscal_id__partner__by_account_number_account_number(
            account_number=account_number,
            fiscal_id=self._fiscal_id,
        )

    def get_context_types(self) -> Any:
        return self._client.partner.api_partner__get_context_types_get__api__fiscal_fiscal_id__partner__context_types(
            fiscal_id=self._fiscal_id,
        )

    def create(self, dto: PartnerDTO | dict[str, Any]) -> Any:
        payload = _normalize_partner_email_fields(_coerce_partner_payload(dto))
        return self._client.partner.api_partner__post_post__api__fiscal_fiscal_id__partner(
            dto=payload,
            fiscal_id=self._fiscal_id,
        )

    def update(self, partner_id: int, dto: PartnerDTO | dict[str, Any]) -> Any:
        payload = _normalize_partner_email_fields(_coerce_partner_payload(dto))
        return self._client.partner.api_partner__put_put__api__fiscal_fiscal_id__partner_id(
            dto=payload,
            fiscal_id=self._fiscal_id,
            id=str(partner_id),
        )

    def get_contexts(
        self,
        partner_id: int,
        *,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
    ) -> Any:
        return self._client.partner.api_partner_context__get_by_partner_get__api__fiscal_fiscal_id__partner_id__context(
            id=partner_id,
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_gln_numbers(
        self,
        partner_id: int,
        *,
        query_string: str | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
    ) -> Any:
        return self._client.partner.api_partner_gln_number__get_by_partner_list_get__api__fiscal_fiscal_id__partner_id_gln_number(
            id=partner_id,
            fiscal_id=self._fiscal_id,
            query_string=query_string,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_gln_number(self, gln_id: int) -> Any:
        return self._client.partner.api_partner_gln_number__get_get__api__fiscal_fiscal_id__partner_gln_number_id(
            id=gln_id,
            fiscal_id=self._fiscal_id,
        )

    def add_gln_number(
        self,
        partner_id: int,
        *,
        gln: str | None = None,
        description: str | None = None,
        attention: str | None = None,
    ) -> Any:
        partner = self.get_by_id(partner_id)
        org_number = None
        if isinstance(partner, dict):
            partner_dict = cast(dict[str, Any], partner)
            org_number = _normalize_optional_text(cast(str | None, partner_dict.get("OrgNumber")))

        gln_value = _normalize_optional_text(gln) or org_number
        if gln_value is None:
            raise PartnerError("GLN is required. No GLN provided and partner OrgNumber is empty.")

        payload: dict[str, Any] = {
            "PartnerId": partner_id,
            "GLN": gln_value,
            "Description": _normalize_optional_text(description) or "EHF",
            "Attention": _normalize_optional_text(attention) or "EHF",
        }

        return self._client.partner.api_partner_gln_number__post_post__api__fiscal_fiscal_id__partner_gln_number(
            article=payload,
            fiscal_id=self._fiscal_id,
        )

    def update_gln_number(
        self,
        gln_id: int,
        *,
        gln: str,
        description: str | None = None,
        attention: str | None = None,
        partner_id: int | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "GLN": _normalize_optional_text(gln),
            "Description": _normalize_optional_text(description) or "EHF",
            "Attention": _normalize_optional_text(attention) or "EHF",
        }
        if payload["GLN"] is None:
            raise PartnerError("GLN is required for update_gln_number")
        if partner_id is not None:
            payload["PartnerId"] = partner_id

        return self._client.partner.api_partner_gln_number__put_put__api__fiscal_fiscal_id__partner_gln_number_id(
            article=payload,
            fiscal_id=self._fiscal_id,
            id=str(gln_id),
        )

    def delete_gln_number(self, gln_id: int) -> Any:
        return self._client.partner.api_partner_gln_number__delete_delete__api__fiscal_fiscal_id__partner_gln_number_id(
            id=gln_id,
            fiscal_id=self._fiscal_id,
        )

    def get_delivery_addresses(
        self,
        partner_id: int,
        *,
        query_string: str | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
    ) -> Any:
        return self._client.partner.api_partner_delivery_address__get_by_partner_list_get__api__fiscal_fiscal_id__partner_id__delivery_address(
            id=partner_id,
            fiscal_id=self._fiscal_id,
            query_string=query_string,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_delivery_address(self, delivery_address_id: int) -> Any:
        return self._client.partner.api_partner_delivery_address__get_get__api__fiscal_fiscal_id__partner_delivery_address_id(
            id=delivery_address_id,
            fiscal_id=self._fiscal_id,
        )

    def add_delivery_address(self, dto: dict[str, Any]) -> Any:
        payload = dict(dto)
        if "Email" in payload:
            payload["Email"] = _normalize_optional_email(cast(str | None, payload.get("Email")))
        return self._client.partner.api_partner_delivery_address__post_post__api__fiscal_fiscal_id__partner_delivery_address(
            address=payload,
            fiscal_id=self._fiscal_id,
        )

    def update_delivery_address(self, delivery_address_id: int, dto: dict[str, Any]) -> Any:
        payload = dict(dto)
        if "Email" in payload:
            payload["Email"] = _normalize_optional_email(cast(str | None, payload.get("Email")))
        return self._client.partner.api_partner_delivery_address__put_put__api__fiscal_fiscal_id__partner_delivery_address_id(
            address=payload,
            fiscal_id=self._fiscal_id,
            id=str(delivery_address_id),
        )

    def delete_delivery_address(self, delivery_address_id: int) -> Any:
        return self._client.partner.api_partner_delivery_address__delete_delete__api__fiscal_fiscal_id__partner_delivery_address_id(
            id=delivery_address_id,
            fiscal_id=self._fiscal_id,
        )

    def add_supplier_address(
        self,
        partner_id: int,
        *,
        name: str,
        street: str,
        postal_number: str,
        city: str,
        country_name: str = "NO",
        note: str | None = None,
        contact_name: str | None = None,
        title: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_default: bool = False,
    ) -> Any:
        payload: dict[str, Any] = {
            "PartnerId": partner_id,
            "IsDefault": is_default,
            "Address": {
                "Name": name,
                "Street": street,
                "Zip": postal_number,
                "City": city,
                "CountryName": country_name,
            },
        }
        if note is not None:
            payload["Note"] = note
        if contact_name is not None:
            payload["ContactName"] = contact_name
        if title is not None:
            payload["Title"] = title
        if phone is not None:
            payload["Phone"] = phone
        normalized_email = _normalize_optional_email(email)
        if normalized_email is not None:
            payload["Email"] = normalized_email

        return self.add_delivery_address(payload)

    def add_context(
        self,
        partner_id: int,
        context_type: str,
        *,
        invoice_email: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        normalized_email = _normalize_optional_email(invoice_email)
        create_data: dict[str, Any] = {
            "PartnerId": partner_id,
            "ContextType": context_type,
        }
        if normalized_email is not None:
            create_data["InvoiceEmail"] = normalized_email
        if data:
            create_data.update(data)

        return self._client.partner.api_partner_context__post_post__api__fiscal_fiscal_id__partner_context(
            create_data=create_data,
            fiscal_id=self._fiscal_id,
        )

    def create_customer(
        self,
        *,
        name: str,
        postal_number: str,
        email: str,
        street: str | None = None,
        country_name: str = "NO",
        partner_type: str = "xena_partnertype_company",
    ) -> dict[str, Any]:
        return self._create_partner_with_context(
            name=name,
            postal_number=postal_number,
            email=email,
            street=street,
            context_type="ContextType_Customer",
            country_name=country_name,
            partner_type=partner_type,
        )

    def create_supplier(
        self,
        *,
        name: str,
        postal_number: str,
        email: str,
        street: str | None = None,
        country_name: str = "NO",
        partner_type: str = "xena_partnertype_company",
    ) -> dict[str, Any]:
        return self._create_partner_with_context(
            name=name,
            postal_number=postal_number,
            email=email,
            street=street,
            context_type="ContextType_Supplier",
            country_name=country_name,
            partner_type=partner_type,
        )

    def _create_partner_with_context(
        self,
        *,
        name: str,
        postal_number: str,
        email: str,
        street: str | None,
        context_type: str,
        country_name: str,
        partner_type: str,
    ) -> dict[str, Any]:
        address: dict[str, Any] = {
            "Name": name,
            "Zip": postal_number,
            "CountryName": country_name,
        }
        if street is not None:
            address["Street"] = street

        partner = self.create(
            {
                "ShortDescription": name,
                "Address": address,
                "PartnerType": partner_type,
            }
        )

        partner_dict = cast(dict[str, Any], partner) if isinstance(partner, dict) else None
        partner_id = partner_dict.get("Id") if partner_dict is not None else None
        if not isinstance(partner_id, int):
            raise PartnerError("Create partner did not return an integer Id")

        context = self.add_context(
            partner_id,
            context_type,
            invoice_email=email,
        )
        return {"partner": partner, "context": context}

    def get_customers(self, **kwargs: Any) -> Any:
        return self.get_all(partner_context_type="Customer", **kwargs)

    def get_suppliers(self, **kwargs: Any) -> Any:
        return self.get_all(partner_context_type="Supplier", **kwargs)

    def get_employees(self, **kwargs: Any) -> Any:
        return self.get_all(partner_context_type="Employee", **kwargs)

    def get_all_contexts(self, **kwargs: Any) -> Any:
        return self.get_all(partner_context_type="All", **kwargs)