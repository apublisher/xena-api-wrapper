from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol, cast

from ...core import DateInput, to_fiscal_date_int


class _FiscalPeriodResolver(Protocol):
    def get_by_year(self, year: int | str) -> dict[str, Any]: ...


class PartnerLedgerError(ValueError):
    """Base error for partner-ledger workflow operations."""


_CONTEXT_TYPE_ALIASES: dict[str, str] = {
    "customer": "ContextType_Customer",
    "supplier": "ContextType_Supplier",
}

_POST_TYPE_ALIASES: dict[str, str] = {
    "invoice": "PartnerPostType_CustomerInvoice",
    "customer_invoice": "PartnerPostType_CustomerInvoice",
    "credit_note": "PartnerPostType_CustomerCreditNote",
    "customer_credit_note": "PartnerPostType_CustomerCreditNote",
    "payment": "PartnerPostType_CustomerPayment",
    "customer_payment": "PartnerPostType_CustomerPayment",
    "supplier_invoice": "PartnerPostType_SupplierInvoice",
    "supplier_credit_note": "PartnerPostType_SupplierCreditNote",
    "supplier_payment": "PartnerPostType_SupplierPayment",
}


def _normalize_context_type(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.startswith("ContextType_"):
        return cleaned
    alias = _CONTEXT_TYPE_ALIASES.get(cleaned.lower())
    return alias or cleaned


def _normalize_post_type(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.startswith("PartnerPostType_"):
        return cleaned
    alias = _POST_TYPE_ALIASES.get(cleaned.lower())
    return alias or cleaned


def _extract_entities(raw_payload: Any) -> list[dict[str, Any]]:
    if isinstance(raw_payload, dict):
        entities = raw_payload.get("Entities")
        if isinstance(entities, list):
            return [e for e in entities if isinstance(e, dict)]
    to_dict = getattr(raw_payload, "to_dict", None)
    if callable(to_dict):
        converted = to_dict()
        if isinstance(converted, dict):
            entities = converted.get("Entities")
            if isinstance(entities, list):
                return [e for e in entities if isinstance(e, dict)]
    return []


def _as_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int | float | str):
        return Decimal(str(value))
    raise PartnerLedgerError(f"Unsupported numeric value: {value!r}")


@dataclass
class PartnerLedgerWorkflow:
    """Workflow helper for partner-ledger read endpoints."""

    _client: Any
    _fiscal_id: str
    _fiscal_period_workflow: _FiscalPeriodResolver

    def get_posts(
        self,
        partner_id: int,
        *,
        context_type: str | None = None,
        fiscal_period_id: int | None = None,
        fiscal_date_from: DateInput | None = None,
        fiscal_date_to: DateInput | None = None,
        is_settled: bool | None = None,
        post_type: str | None = None,
        is_parked: bool | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 30,
        force_no_paging: bool = False,
    ) -> Any:
        if fiscal_period_id is not None:
            raise PartnerLedgerError(
                "fiscal_period_id is not supported by the current generated client method; "
                "use fiscal_date_from/fiscal_date_to or get_posts_for_year(...) instead"
            )

        from_days = to_fiscal_date_int(fiscal_date_from) if fiscal_date_from is not None else None
        to_days = to_fiscal_date_int(fiscal_date_to) if fiscal_date_to is not None else None
        normalized_context_type = _normalize_context_type(context_type)
        normalized_post_type = _normalize_post_type(post_type)

        return self._client.finance.api_transaction__get_partner_posts_by_partner_get__api__fiscal_fiscal_id__transaction__partner_id__partner_post(
            id=partner_id,
            fiscal_id=self._fiscal_id,
            context_type=normalized_context_type,
            fiscal_date_from=from_days,
            fiscal_date_to=to_days,
            is_settled=is_settled,
            post_type=normalized_post_type,
            is_parked=is_parked,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_posts_for_year(
        self,
        partner_id: int,
        year: int | str,
        *,
        context_type: str | None = None,
        is_settled: bool | None = None,
        post_type: str | None = None,
        is_parked: bool | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 30,
        force_no_paging: bool = False,
    ) -> Any:
        period = self._fiscal_period_workflow.get_by_year(year)
        period_id = period.get("Id")
        start_days = period.get("FiscalPeriodStartDays")
        end_days = period.get("FiscalPeriodEndDays")
        if not isinstance(period_id, int):
            raise PartnerLedgerError("Fiscal period response missing integer Id field")
        if not isinstance(start_days, int) or not isinstance(end_days, int):
            raise PartnerLedgerError("Fiscal period response missing integer FiscalPeriodStartDays/FiscalPeriodEndDays")

        return self.get_posts(
            partner_id,
            context_type=context_type,
            fiscal_date_from=start_days,
            fiscal_date_to=end_days,
            is_settled=is_settled,
            post_type=post_type,
            is_parked=is_parked,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
        )

    def get_customer_posts(self, partner_id: int, **kwargs: Any) -> Any:
        return self.get_posts(partner_id, context_type="ContextType_Customer", **kwargs)

    def get_supplier_posts(self, partner_id: int, **kwargs: Any) -> Any:
        return self.get_posts(partner_id, context_type="ContextType_Supplier", **kwargs)

    def get_unsettled_posts(
        self,
        partner_id: int,
        *,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
    ) -> Any:
        return self._client.finance.api_payment__get_unsettled_partner_post_get__api__fiscal_fiscal_id__partner_id__unsettled_post(
            id=partner_id,
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_currency_difference_tag(self, *, force_no_paging: bool = True) -> dict[str, Any]:
        payload = self._client.finance.api_ledger_tag__get_currency_difference_tag_get__api__fiscal_fiscal_id__ledger_tag__currency_difference_tag(
            fiscal_id=self._fiscal_id,
            list_options_force_no_paging=force_no_paging,
        )
        entities = _extract_entities(payload)
        if not entities:
            raise PartnerLedgerError("Currency difference tag not found")
        return entities[0]

    def build_settlement_payload_safe(
        self,
        partner_id: int,
        partner_post_ids: list[int],
        *,
        pay_date: DateInput,
        partial_settle_id: int | None = None,
        currency_abbreviation: str | None = None,
    ) -> dict[str, Any]:
        if not partner_post_ids:
            raise PartnerLedgerError("partner_post_ids must contain at least one id")
        unique_ids = list(dict.fromkeys(partner_post_ids))
        if len(unique_ids) != len(partner_post_ids):
            raise PartnerLedgerError("partner_post_ids contains duplicates")

        unsettled_payload = self.get_unsettled_posts(partner_id, force_no_paging=True)
        unsettled_entities = _extract_entities(unsettled_payload)
        index = {
            cast(int, entity["Id"]): entity
            for entity in unsettled_entities
            if isinstance(entity.get("Id"), int)
        }

        missing_ids = [post_id for post_id in unique_ids if post_id not in index]
        if missing_ids:
            raise PartnerLedgerError(
                f"partner_post_ids not found among unsettled posts for partner {partner_id}: {missing_ids}"
            )

        selected_rows = [index[post_id] for post_id in unique_ids]

        currency_values = {
            str(row.get("CurrencyAbbreviation")).strip()
            for row in selected_rows
            if row.get("CurrencyAbbreviation") is not None and str(row.get("CurrencyAbbreviation")).strip()
        }
        if len(currency_values) > 1:
            raise PartnerLedgerError(
                f"Selected partner posts have mixed currencies: {sorted(currency_values)}"
            )

        inferred_currency = next(iter(currency_values), None)
        if currency_abbreviation is None:
            currency_value = inferred_currency
        else:
            currency_value = currency_abbreviation.strip()

        if not currency_value:
            raise PartnerLedgerError("Could not resolve currency abbreviation for settlement")
        if inferred_currency and currency_value != inferred_currency:
            raise PartnerLedgerError(
                f"currency_abbreviation '{currency_value}' does not match selected posts currency '{inferred_currency}'"
            )

        total = Decimal("0")
        for row in selected_rows:
            remaining_amount = row.get("RemainingAmount")
            amount = row.get("Amount")
            numeric = remaining_amount if remaining_amount is not None else amount
            total += _as_decimal(numeric)

        if total != Decimal("0"):
            raise PartnerLedgerError(
                f"Selected partner posts are not balanced. Expected total RemainingAmount=0, got {total}"
            )

        tag = self.get_currency_difference_tag(force_no_paging=True)
        tag_id = tag.get("Id")
        if not isinstance(tag_id, int):
            raise PartnerLedgerError("Currency difference tag response missing integer Id")

        ledger_tag_number = tag.get("LedgerTagNumber")
        if ledger_tag_number is None:
            ledger_tag_number = tag.get("Number")

        payload: dict[str, Any] = {
            "ledgerPosts": [
                {
                    "LedgerTagId": tag_id,
                    "LedgerTagNumber": ledger_tag_number,
                    "LedgerTagDescription": tag.get("Description"),
                    "Amount": 0,
                }
            ],
            "currencyAbbreviation": currency_value,
            "partnerPostIds": unique_ids,
            "payDate": to_fiscal_date_int(pay_date),
            "partialSettleId": partial_settle_id if partial_settle_id is not None else unique_ids[0],
        }

        for ledger_post in payload["ledgerPosts"]:
            amount = _as_decimal(ledger_post.get("Amount"))
            if amount != Decimal("0"):
                raise PartnerLedgerError("Strict safety rule violated: ledgerPosts Amount must be 0")

        return payload

    def settle_partner_posts_safe(
        self,
        partner_id: int,
        partner_post_ids: list[int],
        *,
        pay_date: DateInput,
        partial_settle_id: int | None = None,
        currency_abbreviation: str | None = None,
    ) -> Any:
        pay_data = self.build_settlement_payload_safe(
            partner_id,
            partner_post_ids,
            pay_date=pay_date,
            partial_settle_id=partial_settle_id,
            currency_abbreviation=currency_abbreviation,
        )
        return self._client.order.api_order__put_pay_put__api__fiscal_fiscal_id__order__pay(
            pay_data=pay_data,
            fiscal_id=self._fiscal_id,
        )
