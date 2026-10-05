from __future__ import annotations

from dataclasses import dataclass, field
import os

from .core.authentication import validate_access_token
from .core.payloads import non_empty_string


@dataclass(frozen=True)
class XenaCredentials:
    """Immutable credentials container for Xena API access."""

    api_key: str
    fiscal_id: str

    @classmethod
    def from_env(cls, prefix: str = "") -> "XenaCredentials":
        api_key = (os.getenv(f"{prefix}API_KEY") or "").strip()
        fiscal_id = (os.getenv(f"{prefix}FISCAL_ID") or "").strip()

        if not api_key:
            raise ValueError(f"Missing environment variable: {prefix}API_KEY")
        if not fiscal_id:
            raise ValueError(f"Missing environment variable: {prefix}FISCAL_ID")

        return cls(api_key=api_key, fiscal_id=fiscal_id)


@dataclass(frozen=True)
class XenaBearerCredentials:
    """An existing access token; login and refresh remain the caller's responsibility."""

    access_token: str = field(repr=False)
    fiscal_id: str

    def __post_init__(self) -> None:
        validate_access_token(self.access_token)
        non_empty_string(self.fiscal_id, "fiscal_id")

    @classmethod
    def from_env(cls, prefix: str = "") -> "XenaBearerCredentials":
        token = (os.getenv(f"{prefix}ACCESS_TOKEN") or "").strip()
        fiscal_id = (os.getenv(f"{prefix}FISCAL_ID") or "").strip()
        if not token:
            raise ValueError(f"Missing environment variable: {prefix}ACCESS_TOKEN")
        if not fiscal_id:
            raise ValueError(f"Missing environment variable: {prefix}FISCAL_ID")
        return cls(access_token=token, fiscal_id=fiscal_id)
