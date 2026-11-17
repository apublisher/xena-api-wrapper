from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

import requests

from ..core.authentication import require_bearer
from ..core.dates import DateInput, to_fiscal_date_int
from ..core.payloads import (
    as_dict,
    boolean_param,
    extract_entities,
    non_empty_string,
    non_negative_int,
    positive_int,
)


class ReconciliationError(ValueError):
    """Invalid reconciliation input or an unexpected API response."""


_BANK_IMPORT_URL = "https://xena-services-bankimport-api-v1-production.codezoo.io"


@dataclass
class ReconciliationWorkflow:
    """Bank import and stored bank transactions, without bank-token management."""

    _client: Any
    _fiscal_id: str

    def sync_bank_transactions(self, *, timeout: float = 60) -> Any:
        """Ask Xena's bank import service to update all mappings in this fiscal.

        This is an explicit write, never retried or triggered by the read methods.
        Authentication failures propagate as requests.HTTPError. API-key support
        is not assumed; the browser uses bearer authentication.
        """
        if isinstance(timeout, bool) or not isfinite(timeout) or timeout <= 0:
            raise ReconciliationError("timeout must be a positive finite number")
        fiscal_id = non_empty_string(self._fiscal_id, "fiscal_id")
        prepared = self._client.session.prepare_request(
            requests.Request("GET", "https://my.xena.biz/")
        )
        headers = {"Accept": "application/json", "x-fiscal-id": fiscal_id}
        api_key = prepared.headers.get("XenaAPIKey")
        if api_key:
            if prepared.headers.get("Authorization"):
                raise ReconciliationError("Provide either API-key or bearer authentication, not both")
            headers["XenaAPIKey"] = api_key
        else:
            headers["Authorization"] = f"Bearer {require_bearer(self._client)}"

        # Do not forward the Xena session's cookies or unrelated headers to this host.
        with requests.Session() as session:
            session.trust_env = False
            with session.post(
                f"{_BANK_IMPORT_URL}/mappings/actions/update",
                headers=headers,
                timeout=timeout,
                allow_redirects=False,
            ) as response:
                response.raise_for_status()
                if 300 <= response.status_code < 400:
                    raise ReconciliationError("Unexpected redirect from the bank import API")
                if not response.content:
                    return None
                return response.json()

    def get_bank_contexts(
        self,
        *,
        include_defaults: bool = False,
        show_deactivated: bool = False,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Return the Count/Entities envelope of bank contexts for this fiscal."""
        self._validate_paging(show_deactivated, force_no_paging, page, page_size)
        boolean_param(include_defaults, "include_defaults")
        payload = self._client.bank.api_ledger_tag_bank_context__get_get__api__fiscal_fiscal_id__ledger_tag_bank_context(
            fiscal_id=self._fiscal_id,
            include_defaults=include_defaults,
            list_options_show_deactivated=show_deactivated,
            list_options_force_no_paging=force_no_paging,
            list_options_page=page,
            list_options_page_size=page_size,
            timeout=30,
            allow_redirects=False,
        )
        return self._page_response(payload, "bank contexts")

    def get_bank_transactions(
        self,
        bank_context_id: int,
        *,
        date_from: DateInput | None = None,
        date_to: DateInput | None = None,
        show_reconciled: bool = True,
        reverse_date_sort: bool = False,
        show_deactivated: bool = False,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Read stored postings, independently of when they were imported.

        No date limit is imposed by the wrapper. Reconciled postings are included
        by default rather than copying the UI's unreconciled-only view.
        """
        positive_int(bank_context_id, "bank_context_id")
        self._validate_paging(show_deactivated, force_no_paging, page, page_size)
        boolean_param(show_reconciled, "show_reconciled")
        boolean_param(reverse_date_sort, "reverse_date_sort")
        if isinstance(date_from, bool) or isinstance(date_to, bool):
            raise ReconciliationError("Date filters cannot be booleans")
        start = to_fiscal_date_int(date_from) if date_from is not None else None
        end = to_fiscal_date_int(date_to) if date_to is not None else None
        if start is not None and end is not None and start > end:
            raise ReconciliationError("date_from must not be later than date_to")
        payload = self._client.bank.api_bank_posting__get_by_bank_context_get__api__fiscal_fiscal_id__ledger_tag_bank_context_id__posting(
            id=bank_context_id,
            fiscal_id=self._fiscal_id,
            fiscal_date_from=start,
            fiscal_date_to=end,
            show_reconciled=show_reconciled,
            reverse_date_sort=reverse_date_sort,
            list_options_show_deactivated=show_deactivated,
            list_options_force_no_paging=force_no_paging,
            list_options_page=page,
            list_options_page_size=page_size,
            timeout=30,
            allow_redirects=False,
        )
        return self._page_response(payload, "bank transactions")

    @staticmethod
    def _validate_paging(
        show_deactivated: bool, force_no_paging: bool, page: int, page_size: int,
    ) -> None:
        boolean_param(show_deactivated, "show_deactivated")
        boolean_param(force_no_paging, "force_no_paging")
        non_negative_int(page, "page")
        positive_int(page_size, "page_size")

    @staticmethod
    def _page_response(payload: Any, label: str) -> dict[str, Any]:
        result = as_dict(payload, ReconciliationError, label)
        extract_entities(result, ReconciliationError, label)
        count = result.get("Count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ReconciliationError(f"Unexpected {label} response: expected a non-negative Count")
        return result
