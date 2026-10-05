from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from ...core.authentication import require_bearer
from ...core.payloads import as_dict, boolean_param, extract_entities, non_negative_int, positive_int
from .registration_errors import RegistrationInboxError


@dataclass
class RegistrationInboxWorkflow:
    """Resource-scoped registration inbox reads with a conservative bearer requirement."""

    _client: Any
    _fiscal_id: str

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
        require_bearer(self._client)
        positive_int(resource_id, "resource_id")
        positive_int(page_size, "page_size")
        non_negative_int(page, "page")
        params: dict[str, Any] = {
            "resourceId": resource_id,
            "ShowDeactivated": boolean_param(show_deactivated, "show_deactivated"),
            "Page": page,
            "PageSize": page_size,
            "ForceNoPaging": boolean_param(force_no_paging, "force_no_paging"),
        }
        for key, value in (
            ("isNew", is_new),
            ("isParked", is_parked),
            ("isAllApproved", is_all_approved),
        ):
            if value is not None:
                params[key] = boolean_param(value, key)
        return self._get_json("ResourceInboxDocumentRelation/ByResource", params)

    def get_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        return extract_entities(self.get_all(**kwargs), RegistrationInboxError, "registration inbox")

    def get_by_id(self, inbox_id: int) -> dict[str, Any]:
        require_bearer(self._client)
        positive_int(inbox_id, "inbox_id")
        return self._get_json(f"ResourceInboxDocumentRelation/{inbox_id}")

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        fiscal_id = quote(self._fiscal_id, safe="")
        base_url = self._client.BASE_URL.rstrip("/")
        with self._client.session.get(
            f"{base_url}/Api/Fiscal/{fiscal_id}/{path}",
            params=params, timeout=30, allow_redirects=False,
        ) as response:
            response.raise_for_status()
            if 300 <= response.status_code < 400:
                raise RegistrationInboxError("Unexpected redirect from the registration inbox API")
            return as_dict(response.json(), RegistrationInboxError, "registration inbox")
