from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, ClassVar, cast

from ...core import DateInput, to_fiscal_date_int
from ..utils import LedgerListWorkflow
from ..utils.ledger_account import LedgerAccountNotFoundError, LedgerAccountWorkflow
from ..utils.ledger_tag import LedgerTagWorkflow
from ..utils.ledger_tag import LedgerTagNotFoundError
from ..utils.vat import VatWorkflow


class VoucherDraftError(ValueError):
    """Base error for voucher draft workflow operations."""


class VoucherDraftLedgerNotFoundError(VoucherDraftError):
    """Raised when no draft ledger is found for the given selector."""


class VoucherDraftValidationError(VoucherDraftError):
    """Raised when convenience-line input cannot be validated."""


@dataclass
class VoucherDraftWorkflow:
    """Workflow helper for bookkeeping draft-voucher (Kassekladd) operations."""

    _client: Any
    _fiscal_id: str
    _ledger_list_workflow: LedgerListWorkflow | None = None
    _ledger_tag_workflow: LedgerTagWorkflow | None = None
    _ledger_account_workflow: LedgerAccountWorkflow | None = None
    _vat_workflow: VatWorkflow | None = None
    _selected_ledger_id: int | None = None
    _ensure_xena_ui_is_happy: bool = True

    _CONVENIENCE_ALLOWED_KEYS = {
        "date",
        "type",
        "amount",
        "description",
        "account",
        "contra_account",
        "vatnumber",
        "partner_number",
        "settled_partner_post_ids",
        "partial_settle_id",
    }

    _CONVENIENCE_REQUIRED_KEYS = {"date", "amount"}

    _CONTEXT_TYPE_ALIASES: ClassVar[dict[str, str]] = {
        "customer": "ContextType_Customer",
        "supplier": "ContextType_Supplier",
    }

    def get_modified_history(
        self,
        *,
        force_no_paging: bool = True,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
    ) -> Any:
        return self._client.finance.api_bookkeeping__get_voucher_modified_history_get__api__fiscal_fiscal_id__bookkeeping__voucher_modified_history(
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def list_ledgers(self, **kwargs: Any) -> Any:
        return self._get_ledger_list_workflow().get_all(**kwargs)

    def list_ledger_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self._get_ledger_list_workflow().get_entities(**kwargs)

    def get_ledger_by_id(self, ledger_id: int) -> Any:
        return self._client.finance.api_ledger__get_get__api__fiscal_fiscal_id__ledger_id(
            fiscal_id=self._fiscal_id,
            id=ledger_id,
        )

    def get_ledger_id_by_description(self, description: str, **kwargs: Any) -> int:
        return self._get_ledger_list_workflow().get_id_by_description(description, **kwargs)

    def set_ledger_by_name(self, description: str, **kwargs: Any) -> int:
        ledger_id = self.get_ledger_id_by_description(description, **kwargs)
        self._selected_ledger_id = ledger_id
        return ledger_id

    def set_ledger_by_id(self, ledger_id: int, **kwargs: Any) -> int:
        # Validate the selected id by resolving it through the shared list utility.
        self._get_ledger_list_workflow().get_by_id(ledger_id, **kwargs)
        self._selected_ledger_id = ledger_id
        return ledger_id

    def get_selected_ledger_id(self) -> int | None:
        return self._selected_ledger_id

    # Backward-compatible aliases requested for convenience.
    def setVoucherByName(self, description: str, **kwargs: Any) -> int:  # noqa: N802
        return self.set_ledger_by_name(description, **kwargs)

    def setVoucherById(self, ledger_id: int, **kwargs: Any) -> int:  # noqa: N802
        return self.set_ledger_by_id(ledger_id, **kwargs)

    def get_lines(
        self,
        ledger_id: int,
        *,
        query_string: str | None = None,
        force_no_paging: bool = True,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
    ) -> Any:
        base_kwargs: dict[str, Any] = {
            "id": ledger_id,
            "fiscal_id": self._fiscal_id,
            "list_options_show_deactivated": show_deactivated,
            "list_options_page": page,
            "list_options_page_size": page_size,
            "list_options_force_no_paging": force_no_paging,
        }

        if query_string is None:
            return self._client.finance.api_ledger_line__get_get__api__fiscal_fiscal_id__ledger_id__line(
                **base_kwargs,
            )

        try:
            return self._client.finance.api_ledger_line__get_get__api__fiscal_fiscal_id__ledger_id__line(
                querystring=query_string,
                **base_kwargs,
            )
        except TypeError:
            return self._client.finance.api_ledger_line__get_get__api__fiscal_fiscal_id__ledger_id__line(
                query_string=query_string,
                **base_kwargs,
            )

    def get_partner_payment_suggestions(
        self,
        query_string: str,
        *,
        per_date: DateInput | None = None,
        include_manual_payment: bool = True,
        context_type: str | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 30,
        force_no_paging: bool = False,
    ) -> Any:
        payload = self._client.finance.api_payment__get_payment_suggestion_get__api__fiscal_fiscal_id__payment__unsettled_post(
            query_string=query_string,
            fiscal_id=self._fiscal_id,
            per_date=to_fiscal_date_int(per_date) if per_date is not None else None,
            include_manual_payment=include_manual_payment,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

        normalized_context = self._normalize_context_type(context_type)
        if normalized_context is None:
            return payload

        payload_dict = self._as_dict(payload)
        entities_obj = payload_dict.get("Entities")
        entities = entities_obj if isinstance(entities_obj, list) else []

        if normalized_context == "ContextType_Customer":
            filtered = [
                row
                for row in entities
                if isinstance(row, dict)
                and str(row.get("PostType", "")).startswith("PartnerPostType_Customer")
            ]
        else:
            filtered = [
                row
                for row in entities
                if isinstance(row, dict)
                and str(row.get("PostType", "")).startswith("PartnerPostType_Supplier")
            ]

        output = dict(payload_dict)
        output["Entities"] = filtered
        output["Count"] = len(filtered)
        return output

    def apply_settled_partner_posts(
        self,
        dto: dict[str, Any],
        *,
        settled_partner_post_ids: list[int],
        partial_settle_id: int | None = None,
    ) -> dict[str, Any]:
        if not settled_partner_post_ids:
            raise VoucherDraftValidationError("settled_partner_post_ids cannot be empty")

        normalized_ids: list[int] = []
        for post_id in settled_partner_post_ids:
            if not isinstance(post_id, int):
                raise VoucherDraftValidationError("settled_partner_post_ids must contain only integers")
            normalized_ids.append(post_id)

        updated = dict(dto)
        updated["SettledPartnerPosts"] = [{"Id": post_id} for post_id in normalized_ids]

        if partial_settle_id is not None:
            if not isinstance(partial_settle_id, int):
                raise VoucherDraftValidationError("partial_settle_id must be an integer when provided")
            updated["PartiallySettledPostId"] = partial_settle_id

        return updated

    def create_line(self, dto: dict[str, Any], *, ensure_xena_ui_is_happy: bool | None = None) -> Any:
        created_raw = self._create_line_raw(dto)

        ensure_ui = self._ensure_xena_ui_is_happy
        if ensure_xena_ui_is_happy is not None:
            ensure_ui = bool(ensure_xena_ui_is_happy)

        if not ensure_ui:
            return created_raw

        created = self._as_dict(created_raw)
        created_id = created.get("Id")
        if not isinstance(created_id, int):
            return created_raw

        # Round-trip through update to align draft-row state with what Xena UI expects.
        return self.update_line(created_id, created)

    def _create_line_raw(self, dto: dict[str, Any]) -> Any:
        request_body = self._hydrate_create_line_dto(dto)
        return self._client.finance.api_ledger_line__post_post__api__fiscal_fiscal_id__ledger_line(
            dto=request_body,
            fiscal_id=self._fiscal_id,
        )

    # This toggle controls an intentional create->update roundtrip used only to match
    # Xena draft-UI expectations (start empty, then hydrate). It does not add business
    # value in backend terms, but improves frontend visibility/state consistency.
    def set_ensure_xena_ui_is_happy(self, enabled: bool) -> bool:
        self._ensure_xena_ui_is_happy = bool(enabled)
        return self._ensure_xena_ui_is_happy

    # Explicit opt-out helper for callers that prefer strict backend efficiency over
    # UI-state smoothing in draft workflows.
    def dont_care_about_what_ui_feels(self) -> bool:
        return self.set_ensure_xena_ui_is_happy(False)

    def update_line(self, ledger_line_id: int, dto: dict[str, Any]) -> Any:
        return self._client.finance.api_ledger_line__put_put__api__fiscal_fiscal_id__ledger_line_id(
            dto=dto,
            fiscal_id=self._fiscal_id,
            id=str(ledger_line_id),
        )

    def delete_line(self, ledger_line_id: int) -> Any:
        return self._client.finance.api_ledger_line__delete_delete__api__fiscal_fiscal_id__ledger_line_id(
            fiscal_id=self._fiscal_id,
            id=ledger_line_id,
        )

    def update_ledger(self, ledger_id: int, dto: dict[str, Any]) -> Any:
        return self._client.finance.api_ledger__put_put__api__fiscal_fiscal_id__ledger_id(
            ledger=dto,
            fiscal_id=self._fiscal_id,
            id=str(ledger_id),
        )

    def preview_summary(
        self,
        ledger_id: int,
        *,
        bookkeep_all: bool = False,
        ledger_line_ids: list[int] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {"bookkeepAll": bool(bookkeep_all)}
        if ledger_line_ids is not None:
            payload["ledgerLineIds"] = ledger_line_ids

        return self._client.finance.api_ledger__post_summary_post__api__fiscal_fiscal_id__ledger_id__summary(
            id=ledger_id,
            data=payload,
            fiscal_id=self._fiscal_id,
        )

    def resolve_ledger_id(
        self,
        *,
        ledger_id: int | None = None,
        ledger_description: str | None = None,
        **kwargs: Any,
    ) -> int:
        if ledger_id is not None:
            return ledger_id
        if ledger_description:
            return self.get_ledger_id_by_description(ledger_description, **kwargs)
        raise VoucherDraftLedgerNotFoundError(
            "Provide either ledger_id or ledger_description to resolve draft ledger"
        )

    def create_lines_convenience(
        self,
        rows: dict[str, Any] | list[dict[str, Any]],
        *,
        ledger_id: int | None = None,
        ledger_description: str | None = None,
        voucher_number: int | None = None,
        strict_settlement_contra: bool = True,
    ) -> dict[str, Any]:
        entries = self._normalize_entry_rows(rows)
        resolved_ledger_id = ledger_id
        if resolved_ledger_id is None and ledger_description:
            resolved_ledger_id = self.get_ledger_id_by_description(ledger_description)
        if resolved_ledger_id is None:
            resolved_ledger_id = self._selected_ledger_id
        if not isinstance(resolved_ledger_id, int):
            raise VoucherDraftLedgerNotFoundError(
                "Provide ledger_id/ledger_description, or set class default with set_ledger_by_name/set_ledger_by_id"
            )

        shared_voucher_number = voucher_number
        line_results: list[dict[str, Any]] = []

        for index, entry in enumerate(entries):
            fiscal_date_days = to_fiscal_date_int(cast(DateInput, entry.get("date")))

            create_payload: dict[str, Any] = {
                "LedgerId": resolved_ledger_id,
                "FiscalDateDays": fiscal_date_days,
            }
            if isinstance(shared_voucher_number, int):
                create_payload["VoucherNumber"] = shared_voucher_number

            created_raw = self._create_line_raw(create_payload)
            created = self._as_dict(created_raw)

            created_id = created.get("Id")
            if not isinstance(created_id, int):
                raise VoucherDraftValidationError(
                    f"Line {index}: create_line did not return integer Id"
                )

            if shared_voucher_number is None:
                vn = created.get("VoucherNumber")
                if isinstance(vn, int):
                    shared_voucher_number = vn

            updated_payload = self._build_updated_line_payload(
                base_dto=created,
                entry=entry,
                shared_voucher_number=shared_voucher_number,
                strict_settlement_contra=strict_settlement_contra,
            )
            updated_raw = self.update_line(created_id, updated_payload)
            updated = self._as_dict(updated_raw)

            line_results.append(
                {
                    "Index": index,
                    "Created": created,
                    "Updated": updated,
                }
            )

        return {
            "LedgerId": resolved_ledger_id,
            "VoucherNumber": shared_voucher_number,
            "LineCount": len(line_results),
            "Lines": line_results,
        }

    @classmethod
    def get_convenience_dto_help(cls) -> dict[str, Any]:
        return {
            "method": "create_lines_convenience",
            "accepted_keys": sorted(cls._CONVENIENCE_ALLOWED_KEYS),
            "required_keys": {
                "all_types": sorted(cls._CONVENIENCE_REQUIRED_KEYS),
                "type_partnerpayment": ["partner_number", "account"],
            },
            "notes": [
                "Use exact key names only; aliases are intentionally unsupported.",
                "type accepts: finance, partnerpayment.",
                "For partnerpayment, use account for the posting account (not contra_account).",
                "contra_account is only applied for finance lines.",
            ],
            "example_finance": {
                "date": "2026-04-01",
                "type": "finance",
                "amount": "200,00",
                "account": 1530,
                "contra_account": 1920,
                "description": "Revenue accrual",
                "vatnumber": "3",
            },
            "example_partnerpayment": {
                "date": "2026-04-01",
                "type": "partnerpayment",
                "amount": 2000,
                "partner_number": 10140,
                "account": 1920,
                "description": "Partner payment",
            },
        }

    def _get_ledger_list_workflow(self) -> LedgerListWorkflow:
        if self._ledger_list_workflow is None:
            self._ledger_list_workflow = LedgerListWorkflow(self._client, self._fiscal_id)
        return self._ledger_list_workflow

    def _get_ledger_tag_workflow(self) -> LedgerTagWorkflow:
        if self._ledger_tag_workflow is None:
            self._ledger_tag_workflow = LedgerTagWorkflow(self._client, self._fiscal_id)
        return self._ledger_tag_workflow

    def _get_vat_workflow(self) -> VatWorkflow:
        if self._vat_workflow is None:
            self._vat_workflow = VatWorkflow(self._client, self._fiscal_id)
        return self._vat_workflow

    def _get_ledger_account_workflow(self) -> LedgerAccountWorkflow:
        if self._ledger_account_workflow is None:
            self._ledger_account_workflow = LedgerAccountWorkflow(self._client, self._fiscal_id)
        return self._ledger_account_workflow

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return cast(dict[str, Any], value)
        if hasattr(value, "to_dict"):
            converted = value.to_dict()
            if isinstance(converted, dict):
                return cast(dict[str, Any], converted)
        raise VoucherDraftValidationError("Expected dict-like response from API")

    @staticmethod
    def _normalize_entry_rows(rows: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        if isinstance(rows, dict):
            return [dict(rows)]

        normalized: list[dict[str, Any]] = []
        for row in rows:
            normalized.append(dict(row))

        if not normalized:
            raise VoucherDraftValidationError("rows cannot be empty")

        return normalized

    def _build_updated_line_payload(
        self,
        *,
        base_dto: dict[str, Any],
        entry: dict[str, Any],
        shared_voucher_number: int | None,
        strict_settlement_contra: bool,
    ) -> dict[str, Any]:
        self._validate_convenience_entry_keys(entry)

        payload = dict(base_dto)

        if "description" in entry and entry["description"] is not None:
            payload["Description"] = str(entry["description"])

        payload["Amount"] = self._normalize_amount(entry.get("amount"))

        entry_type = str(entry.get("type", "finance")).strip().lower()
        if entry_type in {"finance", "finanse", "default"}:
            payload["LedgerLineType"] = "LedgerLineType_Default"
        elif entry_type in {"partnerpayment", "partner_payment", "partner"}:
            payload["LedgerLineType"] = "LedgerLineType_PartnerPayment"
        else:
            raise VoucherDraftValidationError(f"Unsupported line type: {entry.get('type')!r}")

        if isinstance(shared_voucher_number, int):
            payload["VoucherNumber"] = shared_voucher_number

        account_number = entry.get("account")
        contra_account_number = entry.get("contra_account")

        if entry_type in {"partnerpayment", "partner_payment", "partner"}:
            if contra_account_number is not None:
                raise VoucherDraftValidationError(
                    "partnerpayment does not support contra_account; use account instead"
                )
            if entry.get("partner_number") is None:
                raise VoucherDraftValidationError("partnerpayment requires partner_number")
            if account_number is None:
                raise VoucherDraftValidationError("partnerpayment requires account")

        if account_number is not None:
            account_tag = self._resolve_account_tag(account_number)
            tag_id = account_tag.get("Id")
            if not isinstance(tag_id, int):
                raise VoucherDraftValidationError("Resolved account tag is missing integer Id")
            payload["LedgerTagId"] = tag_id
            payload["AccountNumber"] = self._read_number(account_tag)
            payload["LedgerTagNumber"] = self._read_number(account_tag)
            payload["LedgerTagDescription"] = account_tag.get("Description")

        if contra_account_number is not None and entry_type not in {
            "partnerpayment",
            "partner_payment",
            "partner",
        }:
            contra_tag = self._get_ledger_tag_workflow().get_by_number(
                contra_account_number,
                force_no_paging=True,
            )
            if strict_settlement_contra:
                if contra_tag.get("LedgerTagType") != "LedgerTagType_Settlement":
                    raise VoucherDraftValidationError(
                        f"contra_account {contra_account_number} is not a settlement tag"
                    )

            contra_tag_id = contra_tag.get("Id")
            if not isinstance(contra_tag_id, int):
                raise VoucherDraftValidationError("Resolved contra tag is missing integer Id")
            payload["ContraTagId"] = contra_tag_id
            payload["ContraTagNumber"] = self._read_number(contra_tag)
            payload["ContraTagDescription"] = contra_tag.get("Description")

        vat_abbreviation = entry.get("vatnumber")
        if vat_abbreviation is not None:
            vat_row = self._get_vat_workflow().get_by_abbreviation(
                str(vat_abbreviation),
                force_no_paging=True,
                include_defaults=True,
            )
            vat_id = vat_row.get("Id")
            if not isinstance(vat_id, int):
                raise VoucherDraftValidationError("Resolved VAT row is missing integer Id")
            payload["VatId"] = vat_id
            payload["VatAbbreviation"] = vat_row.get("Abbreviation")
            payload["VatDescription"] = vat_row.get("Description")

        partner_number = entry.get("partner_number")
        if partner_number is not None:
            partner_id = self._resolve_partner_id(partner_number)
            payload["PartnerId"] = partner_id
            payload["PartnerAccountNumber"] = str(partner_number)

        settled_partner_post_ids = entry.get("settled_partner_post_ids")
        if settled_partner_post_ids is not None:
            if not isinstance(settled_partner_post_ids, list):
                raise VoucherDraftValidationError("settled_partner_post_ids must be a list of integers")

            partial_settle_id = entry.get("partial_settle_id")
            if partial_settle_id is not None and not isinstance(partial_settle_id, int):
                raise VoucherDraftValidationError("partial_settle_id must be an integer when provided")

            payload = self.apply_settled_partner_posts(
                payload,
                settled_partner_post_ids=cast(list[int], settled_partner_post_ids),
                partial_settle_id=cast(int | None, partial_settle_id),
            )

        return payload

    @staticmethod
    def _normalize_amount(value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            cleaned = value.strip().replace(" ", "")
            if not cleaned:
                raise VoucherDraftValidationError("amount cannot be empty")

            if "," in cleaned and "." in cleaned:
                if cleaned.rfind(",") > cleaned.rfind("."):
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                else:
                    cleaned = cleaned.replace(",", "")
            elif "," in cleaned:
                cleaned = cleaned.replace(",", ".")

            try:
                return float(Decimal(cleaned))
            except (InvalidOperation, ValueError) as exc:
                raise VoucherDraftValidationError(f"Unsupported amount format: {value!r}") from exc

        raise VoucherDraftValidationError(f"Unsupported amount type: {type(value).__name__}")

    def _validate_convenience_entry_keys(self, entry: dict[str, Any]) -> None:
        unknown_keys = sorted(k for k in entry.keys() if k not in self._CONVENIENCE_ALLOWED_KEYS)
        if unknown_keys:
            raise VoucherDraftValidationError(
                f"Unsupported key(s) in convenience row: {', '.join(unknown_keys)}"
            )

        missing_required = sorted(k for k in self._CONVENIENCE_REQUIRED_KEYS if entry.get(k) is None)
        if missing_required:
            raise VoucherDraftValidationError(
                f"Missing required key(s): {', '.join(missing_required)}"
            )

    def _resolve_account_tag(self, account_number: Any) -> dict[str, Any]:
        try:
            return self._get_ledger_tag_workflow().get_by_number(
                account_number,
                force_no_paging=True,
            )
        except LedgerTagNotFoundError as exc:
            parsed = self._to_int(account_number)
            if parsed is None:
                raise VoucherDraftValidationError(
                    f"account must be numeric. Got: {account_number!r}"
                ) from exc

            try:
                account_row = self._get_ledger_account_workflow().get_by_account_number(parsed)
            except LedgerAccountNotFoundError:
                raise VoucherDraftValidationError(
                    f"No ledger tag found for account {parsed}. "
                    "This fiscal setup may not have that account configured for draft posting."
                ) from exc

            ledger_tag_id = account_row.get("LedgerTagId")
            if not isinstance(ledger_tag_id, int):
                raise VoucherDraftValidationError(
                    f"Account {parsed} exists, but it is not linked to a ledger tag and cannot be used "
                    "as a draft posting account in this flow."
                ) from exc

            try:
                return self._get_ledger_tag_workflow().get_by_id(ledger_tag_id)
            except Exception as resolve_exc:  # pragma: no cover - defensive guard
                raise VoucherDraftValidationError(
                    f"Account {parsed} references ledger tag id {ledger_tag_id}, "
                    "but the ledger tag could not be resolved."
                ) from resolve_exc

    @staticmethod
    def _to_int(value: Any) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.isdigit():
                return int(stripped)
        return None

    @staticmethod
    def _read_number(row: dict[str, Any]) -> int | None:
        for key in ("Number", "TagNumber", "LedgerTagNumber", "AccountNumber"):
            value = row.get(key)
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)
        return None

    @classmethod
    def _normalize_context_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if cleaned.startswith("ContextType_"):
            return cleaned
        return cls._CONTEXT_TYPE_ALIASES.get(cleaned.lower(), cleaned)

    def _resolve_partner_id(self, partner_number: Any) -> int:
        partner_number_str = str(partner_number).strip()
        if not partner_number_str.isdigit():
            raise VoucherDraftValidationError(
                f"partner_number must be numeric. Got: {partner_number!r}"
            )

        raw = self._client.partner.api_partner__get_by_account_number_get__api__fiscal_fiscal_id__partner__by_account_number_account_number(
            account_number=int(partner_number_str),
            fiscal_id=self._fiscal_id,
        )

        partner = self._as_dict(raw)
        partner_id = partner.get("Id")
        if not isinstance(partner_id, int):
            raise VoucherDraftValidationError(
                f"Could not resolve partner id for account number {partner_number_str}"
            )
        return partner_id

    def _hydrate_create_line_dto(self, dto: dict[str, Any]) -> dict[str, Any]:
        payload = dict(dto)

        ledger_id = payload.get("LedgerId")
        if ledger_id is None:
            ledger_id = payload.get("ledger_id")

        if ledger_id is None:
            ledger_description = payload.get("LedgerDescription")
            if ledger_description is None:
                ledger_description = payload.get("ledger_description")
            if isinstance(ledger_description, str) and ledger_description.strip():
                ledger_id = self.get_ledger_id_by_description(ledger_description.strip())

        if ledger_id is None:
            ledger_id = self._selected_ledger_id

        if not isinstance(ledger_id, int):
            raise VoucherDraftLedgerNotFoundError(
                "create_line requires LedgerId (or ledger_id / LedgerDescription), "
                "or a class default set via set_ledger_by_name / set_ledger_by_id"
            )

        payload["LedgerId"] = ledger_id
        payload.pop("ledger_id", None)
        payload.pop("LedgerDescription", None)
        payload.pop("ledger_description", None)
        return payload
