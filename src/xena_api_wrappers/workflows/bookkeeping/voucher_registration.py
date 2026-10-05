from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, cast

from ...core import DateInput, to_fiscal_date_int
from ...core.authentication import require_bearer
from ...core.payloads import as_dict, boolean_param, extract_entities, non_negative_int, positive_int
from .registration_errors import VoucherRegistrationError
from .registration_inbox import RegistrationInboxWorkflow


@dataclass
class VoucherRegistrationWorkflow:
    """Document-based draft registration. Does not bookkeep or modify supplier defaults."""

    _client: Any
    _fiscal_id: str
    _registration_inbox_workflow: RegistrationInboxWorkflow | None = None

    def get_all(
        self,
        *,
        resource_id: int,
        is_new: bool | None = None,
        is_parked: bool | None = False,
        is_all_approved: bool | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 10,
        force_no_paging: bool = False,
    ) -> dict[str, Any]:
        """Compatibility shortcut; inbox operations live in RegistrationInboxWorkflow."""
        return self._get_registration_inbox().get_all(
            resource_id=resource_id, is_new=is_new, is_parked=is_parked,
            is_all_approved=is_all_approved, show_deactivated=show_deactivated,
            page=page, page_size=page_size, force_no_paging=force_no_paging,
        )

    def get_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Compatibility shortcut for registration_inbox.get_entities."""
        return self._get_registration_inbox().get_entities(**kwargs)

    def get_inbox_item(self, inbox_id: int) -> dict[str, Any]:
        """Compatibility shortcut for registration_inbox.get_by_id."""
        return self._get_registration_inbox().get_by_id(inbox_id)

    def get_for_inbox(self, inbox_id: int) -> dict[str, Any]:
        require_bearer(self._client)
        positive_int(inbox_id, "inbox_id")
        return as_dict(
            self._client.finance.api_voucher_preview__get_voucher_preview_for_resource_inbox_get__api__fiscal_fiscal_id__resource_inbox_id__voucher_preview(
                id=inbox_id, fiscal_id=self._fiscal_id, timeout=30,
            ),
            VoucherRegistrationError, "VoucherPreview",
        )

    def get_by_id(self, voucher_preview_id: int) -> dict[str, Any]:
        require_bearer(self._client)
        positive_int(voucher_preview_id, "voucher_preview_id")
        return as_dict(
            self._client.finance.api_voucher_preview__get_get__api__fiscal_fiscal_id__voucher_preview_id(
                id=voucher_preview_id, fiscal_id=self._fiscal_id, timeout=30,
            ),
            VoucherRegistrationError, "VoucherPreview",
        )

    def update(self, voucher_preview_id: int, dto: dict[str, Any]) -> dict[str, Any]:
        require_bearer(self._client)
        payload = self._update_payload(voucher_preview_id, dto)
        return as_dict(
            self._client.finance.api_voucher_preview__put_put__api__fiscal_fiscal_id__voucher_preview_id(
                id=str(voucher_preview_id), dto=payload, fiscal_id=self._fiscal_id, timeout=30,
            ),
            VoucherRegistrationError, "VoucherPreview",
        )

    def update_fields(
        self,
        voucher_preview_id: int,
        *,
        fiscal_date: DateInput | None = None,
        pay_date: DateInput | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        """Merge explicit fields into a fresh DTO, preserving Version and unrelated data.

        Pass API field names in fields. Explicit None clears a field; omitted fields
        are preserved. Raw fiscal-day fields may be supplied through fields.
        """
        require_bearer(self._client)
        patch = deepcopy(fields)
        self._validate_patch(patch)
        for name, value in (("FiscalDateDays", fiscal_date), ("PayDateDays", pay_date)):
            if value is not None:
                if name in patch:
                    raise VoucherRegistrationError(f"Provide either the date helper or {name}, not both")
                patch[name] = to_fiscal_date_int(value)
        if not patch:
            raise VoucherRegistrationError("At least one header field must be provided")
        dto = self.get_by_id(voucher_preview_id)
        dto = {**deepcopy(dto), **patch}
        return self.update(voucher_preview_id, dto)

    def get_lines(
        self,
        voucher_preview_id: int,
        *,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
    ) -> dict[str, Any]:
        require_bearer(self._client)
        positive_int(voucher_preview_id, "voucher_preview_id")
        positive_int(page_size, "page_size")
        non_negative_int(page, "page")
        boolean_param(show_deactivated, "show_deactivated")
        boolean_param(force_no_paging, "force_no_paging")
        return as_dict(
            self._client.finance.api_ledger_post_preview__get_ledger_post_preview_get__api__fiscal_fiscal_id__voucher_preview_id__ledger_post_preview(
                id=voucher_preview_id, fiscal_id=self._fiscal_id,
                list_options_show_deactivated=show_deactivated,
                list_options_page=page, list_options_page_size=page_size,
                list_options_force_no_paging=force_no_paging, timeout=30,
            ),
            VoucherRegistrationError, "LedgerPostPreview list",
        )

    def get_line_entities(self, voucher_preview_id: int, **kwargs: Any) -> list[dict[str, Any]]:
        return extract_entities(
            self.get_lines(voucher_preview_id, **kwargs),
            VoucherRegistrationError, "LedgerPostPreview list",
        )

    def get_line(self, line_id: int) -> dict[str, Any]:
        require_bearer(self._client)
        positive_int(line_id, "line_id")
        return as_dict(
            self._client.finance.api_ledger_post_preview__get_get__api__fiscal_fiscal_id__ledger_post_preview_id(
                id=line_id, fiscal_id=self._fiscal_id, timeout=30,
            ),
            VoucherRegistrationError, "LedgerPostPreview",
        )

    def create_line(
        self, voucher_preview_id: int, dto: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        require_bearer(self._client)
        positive_int(voucher_preview_id, "voucher_preview_id")
        payload = self._copy_dto(dto) if dto is not None else {}
        if "VoucherPreviewId" in payload:
            positive_int(payload["VoucherPreviewId"], "DTO VoucherPreviewId")
            if payload["VoucherPreviewId"] != voucher_preview_id:
                raise VoucherRegistrationError("VoucherPreviewId must match voucher_preview_id")
        if payload.get("Id") is not None:
            raise VoucherRegistrationError("A new line must not have an Id")
        payload["VoucherPreviewId"] = voucher_preview_id
        return as_dict(
            self._client.finance.api_ledger_post_preview__post_post__api__fiscal_fiscal_id__ledger_post_preview(
                ledger_post_preview=payload, fiscal_id=self._fiscal_id, timeout=30,
            ),
            VoucherRegistrationError, "LedgerPostPreview",
        )

    def update_line(self, line_id: int, dto: dict[str, Any]) -> dict[str, Any]:
        require_bearer(self._client)
        payload = self._update_payload(line_id, dto)
        return as_dict(
            self._client.finance.api_ledger_post_preview__put_put__api__fiscal_fiscal_id__ledger_post_preview_id(
                id=str(line_id), ledger_post_preview=payload, fiscal_id=self._fiscal_id, timeout=30,
            ),
            VoucherRegistrationError, "LedgerPostPreview",
        )

    def update_line_fields(self, line_id: int, **fields: Any) -> dict[str, Any]:
        require_bearer(self._client)
        if not fields:
            raise VoucherRegistrationError("At least one line field must be provided")
        self._validate_patch(fields)
        dto = {**deepcopy(self.get_line(line_id)), **deepcopy(fields)}
        return self.update_line(line_id, dto)

    def delete_line(self, line_id: int) -> Any:
        require_bearer(self._client)
        positive_int(line_id, "line_id")
        return self._client.finance.api_ledger_post_preview__delete_delete__api__fiscal_fiscal_id__ledger_post_preview_id(
            id=line_id, fiscal_id=self._fiscal_id, timeout=30,
        )

    def get_summary(self, voucher_preview_id: int) -> dict[str, Any]:
        require_bearer(self._client)
        positive_int(voucher_preview_id, "voucher_preview_id")
        return as_dict(
            self._client.finance.api_voucher_preview__get_summary_get__api__fiscal_fiscal_id__voucher_preview_id__summary(
                id=voucher_preview_id, fiscal_id=self._fiscal_id, timeout=30,
            ),
            VoucherRegistrationError, "VoucherPreview summary",
        )

    def _get_registration_inbox(self) -> RegistrationInboxWorkflow:
        if self._registration_inbox_workflow is None:
            self._registration_inbox_workflow = RegistrationInboxWorkflow(self._client, self._fiscal_id)
        return self._registration_inbox_workflow

    @staticmethod
    def _update_payload(entity_id: int, dto: object) -> dict[str, Any]:
        positive_int(entity_id, "entity_id")
        payload = VoucherRegistrationWorkflow._copy_dto(dto)
        if not payload:
            raise VoucherRegistrationError("dto must be a non-empty dictionary")
        dto_id = positive_int(payload.get("Id"), "DTO Id")
        if dto_id != entity_id:
            raise VoucherRegistrationError("DTO Id must match the requested entity")
        version = payload.get("Version")
        if not isinstance(version, int) or isinstance(version, bool) or version < 0:
            raise VoucherRegistrationError("Update DTO must contain a non-negative integer Version")
        return payload

    @staticmethod
    def _copy_dto(dto: object) -> dict[str, Any]:
        if not isinstance(dto, dict):
            raise VoucherRegistrationError("dto must be a dictionary")
        return deepcopy(cast(dict[str, Any], dto))

    @staticmethod
    def _validate_patch(fields: dict[str, Any]) -> None:
        protected = {
            "Id", "Version", "FiscalSetupId", "CreatedAt",
            "VoucherPreviewId", "ResourceInboxDocumentRelationId",
        }
        if protected.intersection(fields):
            raise VoucherRegistrationError("Field updates cannot replace identity, version or relation fields")
