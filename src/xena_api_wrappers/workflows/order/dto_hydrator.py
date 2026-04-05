from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, cast

from ...core import DateInput, to_fiscal_date_int
from .order_errors import OrderWriteHydrationError


@dataclass
class OrderDtoHydrator:
    """Mutable DTO helper that builds order payloads from simple setter calls."""

    _dto: dict[str, Any]
    _article_collection_key: str = "OrderTaskLines"

    @classmethod
    def create(
        cls,
        data: dict[str, Any] | None = None,
        *,
        article_collection_key: str = "OrderTaskLines",
    ) -> "OrderDtoHydrator":
        payload = copy.deepcopy(data) if isinstance(data, dict) else {}
        return cls(_dto=payload, _article_collection_key=article_collection_key)

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self._dto)

    def hydrate(self, data: Any, *, replace: bool = False) -> "OrderDtoHydrator":
        if not isinstance(data, dict):
            raise OrderWriteHydrationError("hydrate expects a dict payload")
        data_dict = cast(dict[str, Any], data)
        if replace:
            self._dto = copy.deepcopy(data_dict)
            return self

        self._dto.update(copy.deepcopy(data_dict))
        return self

    def clear(self) -> "OrderDtoHydrator":
        self._dto = {}
        return self

    def set_field(self, key: str, value: Any) -> "OrderDtoHydrator":
        self._dto[key] = value
        return self

    def get_field(self, key: str, default: Any = None) -> Any:
        return self._dto.get(key, default)

    def remove_field(self, key: str) -> "OrderDtoHydrator":
        self._dto.pop(key, None)
        return self

    def set_customer(
        self,
        partner_id: int,
        *,
        context_type: str = "ContextType_Customer",
    ) -> "OrderDtoHydrator":
        self._dto["PartnerId"] = int(partner_id)
        self._dto["ContextType"] = context_type
        return self

    def set_customer_fields(
        self,
        *,
        account_number: int | None = None,
        name: str | None = None,
        invoice_email: str | None = None,
        phone_number: str | None = None,
        attention: str | None = None,
        note: str | None = None,
        gln_number: str | None = None,
        our_reference: str | None = None,
        your_reference: str | None = None,
    ) -> "OrderDtoHydrator":
        mapping: dict[str, Any] = {
            "PartnerAccountNumber": account_number,
            "PartnerName": name,
            "InvoiceEmail": invoice_email,
            "PartnerPhoneNumber": phone_number,
            "PartnerAttention": attention,
            "PartnerNote": note,
            "GLNNumber": gln_number,
            "OurReference": our_reference,
            "YourReference": your_reference,
        }
        for key, value in mapping.items():
            if value is not None:
                self._dto[key] = value
        return self

    def get_customer_fields(self) -> dict[str, Any]:
        keys = [
            "PartnerId",
            "ContextType",
            "PartnerAccountNumber",
            "PartnerName",
            "InvoiceEmail",
            "PartnerPhoneNumber",
            "PartnerAttention",
            "PartnerNote",
            "GLNNumber",
            "OurReference",
            "YourReference",
        ]
        return {key: self._dto.get(key) for key in keys if key in self._dto}

    def set_dates(
        self,
        *,
        order_date: DateInput | None = None,
        due_date: DateInput | None = None,
        delivery_date: DateInput | None = None,
    ) -> "OrderDtoHydrator":
        if order_date is not None:
            self._dto["FiscalDateDays"] = to_fiscal_date_int(order_date)
        if due_date is not None:
            self._dto["DueDateDays"] = to_fiscal_date_int(due_date)
        if delivery_date is not None:
            self._dto["DeliveryDateDays"] = to_fiscal_date_int(delivery_date)
        return self

    def set_order_date(self, value: DateInput) -> "OrderDtoHydrator":
        self._dto["DateDays"] = to_fiscal_date_int(value)
        return self

    def set_order_date_today(self) -> "OrderDtoHydrator":
        self._dto["DateDays"] = to_fiscal_date_int(date.today())
        return self

    def set_due_date(self, value: DateInput) -> "OrderDtoHydrator":
        self._dto["DueDateDays"] = to_fiscal_date_int(value)
        return self

    def set_delivery_date(self, value: DateInput) -> "OrderDtoHydrator":
        self._dto["DeliveryDateDays"] = to_fiscal_date_int(value)
        return self

    def set_notes(
        self,
        *,
        internal_note: str | None = None,
        delivery_note: str | None = None,
    ) -> "OrderDtoHydrator":
        if internal_note is not None:
            self._dto["InternalNote"] = internal_note
        if delivery_note is not None:
            self._dto["DeliveryNote"] = delivery_note
        return self

    def set_description(self, description: str) -> "OrderDtoHydrator":
        self._dto["Description"] = description
        return self

    def set_delivery_contact(
        self,
        *,
        contact_name: str | None = None,
        title: str | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> "OrderDtoHydrator":
        mapping: dict[str, Any] = {
            "DeliveryContactName": contact_name,
            "DeliveryTitle": title,
            "DeliveryPhone": phone,
            "DeliveryEmail": email,
        }
        for key, value in mapping.items():
            if value is not None:
                self._dto[key] = value
        return self

    def set_delivery_address(
        self,
        *,
        name: str | None = None,
        street: str | None = None,
        zip_code: str | None = None,
        city: str | None = None,
        country_name: str = "NO",
        place_name: str = "",
        country_display_name: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> "OrderDtoHydrator":
        delivery_address_obj = self._dto.get("DeliveryAddress")
        if isinstance(delivery_address_obj, dict):
            delivery_address = copy.deepcopy(cast(dict[str, Any], delivery_address_obj))
        else:
            delivery_address = {}

        defaults: dict[str, Any] = {
            "Name": "",
            "Street": "",
            "Zip": "",
            "City": "",
            "CountryName": country_name,
            "PlaceName": place_name,
            "CountryDisplayName": country_display_name,
        }
        for key, value in defaults.items():
            if key not in delivery_address and value is not None:
                delivery_address[key] = value

        updates = {
            "Name": name,
            "Street": street,
            "Zip": zip_code,
            "City": city,
        }
        for key, value in updates.items():
            if value is not None:
                delivery_address[key] = value

        if country_display_name is not None:
            delivery_address["CountryDisplayName"] = country_display_name
        if extra:
            delivery_address.update(copy.deepcopy(extra))

        self._dto["DeliveryAddress"] = delivery_address
        return self

    def clear_delivery_address(self) -> "OrderDtoHydrator":
        self._dto["DeliveryAddress"] = None
        return self

    def set_header(self, data: Any) -> "OrderDtoHydrator":
        if not isinstance(data, dict):
            raise OrderWriteHydrationError("set_header expects a dict payload")
        data_dict = cast(dict[str, Any], data)
        self._dto.update(copy.deepcopy(data_dict))
        return self

    def get_header(self) -> dict[str, Any]:
        header = self.to_dict()
        header.pop(self._article_collection_key, None)
        return header

    def set_article(
        self,
        *,
        article_id: int | None = None,
        article_number: str | int | None = None,
        quantity: float | int = 1,
        unit_net_price: float | int | None = None,
        description: str | None = None,
        vat_id: int | None = None,
        unit_id: int | None = None,
        discount_percent: float | int | None = None,
        delivery_date: DateInput | None = None,
        extra: dict[str, Any] | None = None,
    ) -> "OrderDtoHydrator":
        if article_id is None and article_number is None:
            raise OrderWriteHydrationError("set_article requires article_id or article_number")

        line: dict[str, Any] = {
            "Quantity": quantity,
        }
        if article_id is not None:
            line["ArticleId"] = int(article_id)
        if article_number is not None:
            line["ArticleNumber"] = str(article_number)
        if unit_net_price is not None:
            line["UnitNetPrice"] = unit_net_price
        if description is not None:
            line["Description"] = description
        if vat_id is not None:
            line["VatId"] = int(vat_id)
        if unit_id is not None:
            line["UnitId"] = int(unit_id)
        if discount_percent is not None:
            line["DiscountPercent"] = discount_percent
        if delivery_date is not None:
            line["DeliveryDateDays"] = to_fiscal_date_int(delivery_date)
        if extra:
            line.update(copy.deepcopy(extra))

        return self.add_article_line(line)

    def add_order_line(self, line: dict[str, Any]) -> "OrderDtoHydrator":
        normalized = self._normalize_order_line_input(line)
        return self.add_article_line(normalized)

    def set_order_lines(
        self,
        lines: list[dict[str, Any]],
        *,
        clear_existing: bool = True,
    ) -> "OrderDtoHydrator":
        if clear_existing:
            self.clear_order_lines()
        for line in lines:
            self.add_order_line(line)
        return self

    def add_order_lines(self, lines: list[dict[str, Any]]) -> "OrderDtoHydrator":
        return self.set_order_lines(lines, clear_existing=False)

    def add_article_line(self, line: Any) -> "OrderDtoHydrator":
        if not isinstance(line, dict):
            raise OrderWriteHydrationError("add_article_line expects dict payload")
        line_dict = cast(dict[str, Any], line)

        lines_obj = self._dto.setdefault(self._article_collection_key, [])
        if not isinstance(lines_obj, list):
            raise OrderWriteHydrationError(
                f"Expected list in '{self._article_collection_key}' when adding article line"
            )

        lines = cast(list[Any], lines_obj)
        lines.append(copy.deepcopy(line_dict))
        return self

    def get_articles(self) -> list[dict[str, Any]]:
        lines_obj = self._dto.get(self._article_collection_key)
        if not isinstance(lines_obj, list):
            return []

        lines = cast(list[Any], lines_obj)
        return [copy.deepcopy(cast(dict[str, Any], line)) for line in lines if isinstance(line, dict)]

    def get_order_lines(self) -> list[dict[str, Any]]:
        return self.get_articles()

    def set_article_line(self, index: int, line: Any) -> "OrderDtoHydrator":
        if not isinstance(line, dict):
            raise OrderWriteHydrationError("set_article_line expects dict payload")

        lines = self._get_article_lines_ref()
        if index < 0 or index >= len(lines):
            raise OrderWriteHydrationError(f"article line index out of range: {index}")

        lines[index] = copy.deepcopy(cast(dict[str, Any], line))
        return self

    def patch_article_line(self, index: int, **fields: Any) -> "OrderDtoHydrator":
        lines = self._get_article_lines_ref()
        if index < 0 or index >= len(lines):
            raise OrderWriteHydrationError(f"article line index out of range: {index}")

        line = lines[index]
        line.update(copy.deepcopy(fields))
        return self

    def set_order_line_pricing(
        self,
        index: int,
        *,
        price_each: float | int,
        quantity: float | int | None = None,
        discount_pct: float | int | None = None,
        net_total: float | int | None = None,
    ) -> "OrderDtoHydrator":
        lines = self._get_article_lines_ref()
        if index < 0 or index >= len(lines):
            raise OrderWriteHydrationError(f"article line index out of range: {index}")

        line = lines[index]
        line["PriceEach"] = float(price_each)

        if quantity is not None:
            line["Quantity"] = float(quantity)

        qty_value = line.get("Quantity", 1)
        qty = float(qty_value) if qty_value is not None else 1.0

        totals_obj = line.get("Totals")
        if isinstance(totals_obj, dict):
            totals = cast(dict[str, Any], totals_obj)
        else:
            totals = {}
            line["Totals"] = totals

        computed = self._build_line_totals(
            quantity=qty,
            price_each=float(price_each),
            discount_pct=discount_pct,
            net_total=net_total,
        )
        if computed is not None:
            totals.update(computed)

        return self

    def set_order_line_price(
        self,
        index: int,
        *,
        price_each: float | int,
        quantity: float | int | None = None,
    ) -> "OrderDtoHydrator":
        return self.set_order_line_pricing(
            index,
            price_each=price_each,
            quantity=quantity,
        )

    def remove_article_line(self, index: int) -> dict[str, Any]:
        lines = self._get_article_lines_ref()
        if index < 0 or index >= len(lines):
            raise OrderWriteHydrationError(f"article line index out of range: {index}")

        removed = lines.pop(index)
        return copy.deepcopy(removed)

    def set_order_line(self, index: int, line: Any) -> "OrderDtoHydrator":
        return self.set_article_line(index, line)

    def edit_order_line(self, index: int, **fields: Any) -> "OrderDtoHydrator":
        return self.patch_article_line(index, **fields)

    def remove_order_line(self, index: int) -> dict[str, Any]:
        return self.remove_article_line(index)

    def clear_articles(self) -> "OrderDtoHydrator":
        self._dto[self._article_collection_key] = []
        return self

    def clear_order_lines(self) -> "OrderDtoHydrator":
        return self.clear_articles()

    def _get_article_lines_ref(self) -> list[dict[str, Any]]:
        lines_obj = self._dto.setdefault(self._article_collection_key, [])
        if not isinstance(lines_obj, list):
            raise OrderWriteHydrationError(
                f"Expected list in '{self._article_collection_key}' when manipulating article lines"
            )

        lines = cast(list[Any], lines_obj)
        normalized: list[dict[str, Any]] = []
        for line in lines:
            if not isinstance(line, dict):
                raise OrderWriteHydrationError("Article line collection contains non-dict element")
            normalized.append(cast(dict[str, Any], line))
        self._dto[self._article_collection_key] = normalized
        return normalized

    def get_order_lines_ref(self) -> list[dict[str, Any]]:
        return self._get_article_lines_ref()

    @staticmethod
    def _normalize_order_line_input(line: dict[str, Any]) -> dict[str, Any]:
        normalized = copy.deepcopy(line)

        # Convenience aliases -> API DTO key names.
        aliases: dict[str, str] = {
            "article_id": "ArticleId",
            "article_number": "ArticleNumber",
            "description": "Description",
            "quantity": "Quantity",
            "price_each": "PriceEach",
            "unit_price": "PriceEach",
            "unit_net_price": "PriceEach",
            "cost_each": "CostEach",
            "unit_id": "UnitId",
            "project_id": "ProjectId",
            "location_id": "LocationId",
            "payer_id": "PayerId",
            "partner_article_number": "PartnerArticleNumber",
        }

        for alias, canonical in aliases.items():
            if alias in normalized and canonical not in normalized:
                normalized[canonical] = normalized.pop(alias)

        if "ArticleId" in normalized and normalized["ArticleId"] is not None:
            normalized["ArticleId"] = int(normalized["ArticleId"])
        if "ArticleNumber" in normalized and normalized["ArticleNumber"] is not None:
            normalized["ArticleNumber"] = str(normalized["ArticleNumber"])

        if "Quantity" not in normalized:
            normalized["Quantity"] = 1

        # Optional pricing helpers for convenient dicts.
        discount_pct = normalized.pop("discount_pct", None)
        if discount_pct is None:
            discount_pct = normalized.pop("discount_percent", None)
        net_total = normalized.pop("net_total", None)
        price_each_obj = normalized.get("PriceEach")
        qty_obj = normalized.get("Quantity")
        if price_each_obj is not None and qty_obj is not None:
            price_each = float(price_each_obj)
            qty = float(qty_obj)

            totals_obj = normalized.get("Totals")
            if isinstance(totals_obj, dict):
                totals = cast(dict[str, Any], totals_obj)
            else:
                totals = {}
                normalized["Totals"] = totals

            computed = OrderDtoHydrator._build_line_totals(
                quantity=qty,
                price_each=price_each,
                discount_pct=discount_pct,
                net_total=net_total,
            )
            if computed is not None:
                totals.update(computed)

        return normalized

    @staticmethod
    def normalize_order_line_input(line: dict[str, Any]) -> dict[str, Any]:
        return OrderDtoHydrator._normalize_order_line_input(line)

    @staticmethod
    def _build_line_totals(
        *,
        quantity: float,
        price_each: float,
        discount_pct: float | int | None = None,
        net_total: float | int | None = None,
    ) -> dict[str, float] | None:
        if discount_pct is None and net_total is None:
            return None
        if discount_pct is not None and net_total is not None:
            raise OrderWriteHydrationError(
                "Provide either discount_pct or net_total, not both"
            )

        qty_dec = Decimal(str(quantity))
        price_dec = Decimal(str(price_each))
        gross = qty_dec * price_dec

        if discount_pct is not None:
            pct = Decimal(str(discount_pct))
            ratio = pct / Decimal("100")
            discount_total = gross * ratio
            net = gross - discount_total
            return {
                "PriceNettTotal": float(net),
                "DiscountTotal": float(discount_total),
                "DiscountTotalRatio": float(ratio),
                "DiscountTotalPct": float(pct),
            }

        net = Decimal(str(cast(float | int, net_total)))
        discount_total = gross - net
        ratio = Decimal("0") if gross == 0 else (discount_total / gross)
        pct = ratio * Decimal("100")
        return {
            "PriceNettTotal": float(net),
            "DiscountTotal": float(discount_total),
            "DiscountTotalRatio": float(ratio),
            "DiscountTotalPct": float(pct),
        }

    @staticmethod
    def build_line_totals(
        *,
        quantity: float,
        price_each: float,
        discount_pct: float | int | None = None,
        net_total: float | int | None = None,
    ) -> dict[str, float] | None:
        return OrderDtoHydrator._build_line_totals(
            quantity=quantity,
            price_each=price_each,
            discount_pct=discount_pct,
            net_total=net_total,
        )

    @classmethod
    def get_dto_help(cls) -> dict[str, Any]:
        return {
            "header_keys_common": [
                "PartnerId",
                "ContextType",
                "DateDays",
                "FiscalDateDays",
                "DueDateDays",
                "DeliveryDateDays",
                "Description",
                "InternalNote",
                "DeliveryNote",
                "OurReference",
                "YourReference",
                "DeliveryAddress",
                "DeliveryContactName",
                "DeliveryTitle",
                "DeliveryPhone",
                "DeliveryEmail",
            ],
            "article_collection_key_default": "OrderTaskLines",
            "article_line_keys_common": [
                "ArticleId",
                "ArticleNumber",
                "Quantity",
                "UnitNetPrice",
                "Description",
                "VatId",
                "UnitId",
                "DiscountPercent",
                "DeliveryDateDays",
            ],
            "notes": [
                "Use hydrate(...) for full raw payload compatibility.",
                "Use set_customer(...) and set_article(...) for simplified hydration.",
                "Use set_order_date_today() when caller does not provide explicit order date.",
                "Use set_customer_fields(...) and set_delivery_address(...) for common customer/delivery edits.",
                "Use set_order_line/edit_order_line/remove_order_line to fully manage line state.",
                "Use set_order_line_pricing(...) with explicit discount_pct/net_total when discount/total control is needed.",
                "Field names follow observed/generated API patterns and may require additional keys per fiscal setup.",
            ],
        }

    # Backward-compatible aliases for callers preferring mixedCase methods.
    def setCustomer(self, partner_id: int, *, context_type: str = "ContextType_Customer") -> "OrderDtoHydrator":  # noqa: N802
        return self.set_customer(partner_id, context_type=context_type)

    def setArticle(self, **kwargs: Any) -> "OrderDtoHydrator":  # noqa: N802
        return self.set_article(**kwargs)

    def getDto(self) -> dict[str, Any]:  # noqa: N802
        return self.to_dict()
