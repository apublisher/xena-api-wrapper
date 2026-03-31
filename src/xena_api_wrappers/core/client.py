from __future__ import annotations

import importlib
from typing import Any, Callable


ClientFactory = Callable[[str, str], Any]


def default_client_factory(api_key: str, fiscal_id: str) -> Any:
    """Create the underlying xena-client instance lazily."""
    module = importlib.import_module("xena_client")
    client_cls = getattr(module, "XenaClient")
    return client_cls(api_key=api_key, fiscal_id=fiscal_id)
