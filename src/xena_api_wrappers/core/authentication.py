from __future__ import annotations

from typing import Any

import requests


class OAuthRequiredError(PermissionError):
    """The operation requires an OAuth bearer session, not an API key."""

    code = "oauth_required"
    requires_oauth = True


def validate_access_token(access_token: object) -> None:
    if (
        not isinstance(access_token, str)
        or not access_token
        or not access_token.isascii()
        or any(c.isspace() for c in access_token)
    ):
        raise ValueError("Provide a non-empty access token without the Bearer prefix")


def require_bearer(client: Any) -> str:
    """Inspect effective request authentication without making a network call."""
    session = getattr(client, "session", None)
    prepare_request = getattr(session, "prepare_request", None)
    if not callable(prepare_request):
        raise OAuthRequiredError("This operation requires an OAuth-authenticated client session")
    request = prepare_request(requests.Request("GET", "https://my.xena.biz/"))
    if not isinstance(request, requests.PreparedRequest):
        raise OAuthRequiredError("The configured session cannot prepare bearer-authenticated requests")
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token or "XenaAPIKey" in request.headers:
        raise OAuthRequiredError("OAuth login is required; API-key access is not sufficient")
    try:
        validate_access_token(token)
    except ValueError:
        raise OAuthRequiredError("The configured bearer token is invalid; OAuth login is required") from None
    return token
