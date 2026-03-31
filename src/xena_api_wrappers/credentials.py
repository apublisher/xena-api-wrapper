from __future__ import annotations

from dataclasses import dataclass
import os


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
