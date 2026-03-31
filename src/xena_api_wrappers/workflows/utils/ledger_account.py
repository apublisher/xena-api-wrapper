from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class LedgerAccountError(ValueError):
    """Base error for ledger account workflow operations."""


class LedgerAccountNotFoundError(LedgerAccountError):
    """Raised when no ledger account can be matched."""


class LedgerAccountAmbiguousError(LedgerAccountError):
    """Raised when more than one ledger account matches a selector."""


@dataclass
class LedgerAccountWorkflow:
    """Workflow helper for /LedgerAccount endpoint operations."""

    _client: Any
    _fiscal_id: str

    def get_all(
        self,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = True,
        query_string: str | None = None,
        ledger_account: str | None = None,
        include_default: bool | None = None,
        exclude_vats: bool | None = None,
        exclude_article_groups: bool | None = None,
        exclude_ledger_tags: bool | None = None,
        exclude_system_accounts: bool | None = None,
    ) -> Any:
        return self._client.finance.api_ledger_account__get_list_get__api__fiscal_fiscal_id__ledger_account(
            fiscal_id=self._fiscal_id,
            ledger_account=ledger_account,
            query_string=query_string,
            include_default=include_default,
            exclude_vats=exclude_vats,
            exclude_article_groups=exclude_article_groups,
            exclude_ledger_tags=exclude_ledger_tags,
            exclude_system_accounts=exclude_system_accounts,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        raw = self.get_all(**kwargs)
        if isinstance(raw, dict):
            entities = raw.get("Entities")
            if isinstance(entities, list):
                return [e for e in entities if isinstance(e, dict)]
        if hasattr(raw, "to_dict"):
            converted = raw.to_dict()
            if isinstance(converted, dict):
                entities = converted.get("Entities")
                if isinstance(entities, list):
                    return [e for e in entities if isinstance(e, dict)]
        raise LedgerAccountError("Unexpected LedgerAccount response shape: could not read Entities list")

    def get_accounts(
        self,
        *,
        account_number_from: int,
        account_number_to: int,
        show_deactivated: bool = True,
    ) -> list[dict[str, Any]]:
        if account_number_from > account_number_to:
            raise LedgerAccountError("account_number_from cannot be greater than account_number_to")

        entities = self.get_entities(show_deactivated=show_deactivated)
        filtered: list[dict[str, Any]] = []
        for row in entities:
            number = row.get("AccountNumber")
            if isinstance(number, int) and account_number_from <= number <= account_number_to:
                filtered.append(row)

        return sorted(filtered, key=lambda r: int(r.get("AccountNumber", 0)))

    def get_all_accounts(self, *, show_deactivated: bool = True) -> list[dict[str, Any]]:
        return self.get_accounts(
            account_number_from=1000,
            account_number_to=9999,
            show_deactivated=show_deactivated,
        )

    def get_balance_accounts(self, *, show_deactivated: bool = True) -> list[dict[str, Any]]:
        return self.get_accounts(
            account_number_from=1000,
            account_number_to=2999,
            show_deactivated=show_deactivated,
        )

    def get_result_accounts(self, *, show_deactivated: bool = True) -> list[dict[str, Any]]:
        return self.get_accounts(
            account_number_from=3000,
            account_number_to=9999,
            show_deactivated=show_deactivated,
        )

    def get_by_account_number(self, account_number: int, *, show_deactivated: bool = True) -> dict[str, Any]:
        if account_number < 0:
            raise LedgerAccountError("account_number must be a positive integer")

        matches = [
            row
            for row in self.get_entities(show_deactivated=show_deactivated)
            if row.get("AccountNumber") == account_number
        ]
        if not matches:
            raise LedgerAccountNotFoundError(f"No ledger account found for account number {account_number}")
        if len(matches) > 1:
            raise LedgerAccountAmbiguousError(
                f"More than one ledger account matched account number {account_number}"
            )
        return matches[0]

    def get_id_by_account_number(self, account_number: int, *, show_deactivated: bool = True) -> str:
        row = self.get_by_account_number(account_number, show_deactivated=show_deactivated)
        account_id = row.get("Id")
        if not isinstance(account_id, str) or not account_id:
            raise LedgerAccountError("Ledger account response missing string Id field")
        return account_id