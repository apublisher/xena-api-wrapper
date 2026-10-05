from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlencode

from ...core.authentication import require_bearer
from ...core.payloads import as_dict, positive_int


class DocumentError(ValueError):
    """Invalid document input or an unexpected API response."""


@dataclass
class DocumentWorkflow:
    """Bearer-only document metadata and preview URL helpers."""

    _client: Any
    _fiscal_id: str

    def get_by_id(self, document_id: int) -> dict[str, Any]:
        require_bearer(self._client)
        positive_int(document_id, "document_id")
        return as_dict(
            self._client.document.api_document__get_get__api__fiscal_fiscal_id__document_id(
                id=document_id, fiscal_id=self._fiscal_id, timeout=30,
            ),
            DocumentError, "Document",
        )

    def get_last_version(self, document_id: int) -> dict[str, Any]:
        require_bearer(self._client)
        positive_int(document_id, "document_id")
        return as_dict(
            self._client.document.api_document__get_last_version_get__api__fiscal_fiscal_id__document__document_id__last_version(
                id=document_id, fiscal_id=self._fiscal_id, timeout=30,
            ),
            DocumentError, "Document version",
        )

    def get_preview_url(
        self, document_version_id: int, *, width: int = 1000, page: int = 1,
    ) -> str:
        """Return a sensitive, short-lived URL. Never log or persist it.

        Page numbering starts at one, matching captured Xena preview requests.
        The token is read from current session authentication on every call.
        """
        token = require_bearer(self._client)
        positive_int(document_version_id, "document_version_id")
        positive_int(width, "width")
        positive_int(page, "page")
        fiscal_id = quote(self._fiscal_id, safe="")
        query = urlencode({"width": width, "page": page, "access_token": token})
        return (
            f"{self._client.BASE_URL.rstrip('/')}/Api/Blob/Fiscal/{fiscal_id}"
            f"/ScaledImage/{document_version_id}?{query}"
        )

    def get_preview_url_for_document(
        self, document_id: int, *, width: int = 1000, page: int = 1,
    ) -> str:
        version = self.get_last_version(document_id)
        version_id = version.get("Id")
        if not isinstance(version_id, int) or isinstance(version_id, bool) or version_id <= 0:
            raise DocumentError("Document version response is missing a positive integer Id")
        return self.get_preview_url(version_id, width=width, page=page)
