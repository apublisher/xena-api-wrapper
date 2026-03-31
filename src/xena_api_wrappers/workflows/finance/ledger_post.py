from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...core import DateInput, to_fiscal_date_int
from ..utils import LedgerAccountWorkflow


class LedgerPostError(ValueError):
    """Base error for ledger post workflow operations."""


@dataclass
class LedgerPostWorkflow:
    """Workflow helper for /LedgerTag/{id}/LedgerPost endpoint operations."""

    _client: Any
    _fiscal_id: str
    _ledger_account_workflow: LedgerAccountWorkflow | None = None

    def get_entries_by_account(
        self,
        account: int | str,
        date_from: DateInput,
        date_to: DateInput,
        *,
        include_running_totals: bool = True,
        force_no_paging: bool = False,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
        show_reconciled: bool | None = None,
        reverse_date_sort: bool | None = None,
    ) -> Any:
        ledger_tag_id = self._resolve_ledger_tag_id(account)
        fiscal_date_from = to_fiscal_date_int(date_from)
        fiscal_date_to = to_fiscal_date_int(date_to)

        return self._client.finance.api_ledger_post__get_by_ledger_tag_get__api__fiscal_fiscal_id__ledger_tag_id__ledger_post(
            id=ledger_tag_id,
            fiscal_id=self._fiscal_id,
            include_running_totals=include_running_totals,
            fiscal_date_from=fiscal_date_from,
            fiscal_date_to=fiscal_date_to,
            show_reconciled=show_reconciled,
            reverse_date_sort=reverse_date_sort,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def _resolve_ledger_tag_id(self, account: int | str) -> int:
        # If caller passes account number (int or numeric string), resolve via ledger account map.
        if isinstance(account, int):
            row = self._get_ledger_account_workflow().get_by_account_number(account)
            return self._extract_ledger_tag_id(row, account_hint=str(account))

        candidate = account.strip()
        if not candidate:
            raise LedgerPostError("account cannot be empty")

        if candidate.isdigit():
            row = self._get_ledger_account_workflow().get_by_account_number(int(candidate))
            return self._extract_ledger_tag_id(row, account_hint=candidate)

        # Fallback: treat input as ledger account Id and match directly.
        rows = self._get_ledger_account_workflow().get_entities(show_deactivated=True)
        matches = [r for r in rows if r.get("Id") == candidate]
        if not matches:
            raise LedgerPostError(
                f"No ledger account found for identifier '{candidate}'. "
                "Pass account number (for example 1920) or a valid LedgerAccount Id."
            )
        if len(matches) > 1:
            raise LedgerPostError(f"More than one ledger account matched identifier '{candidate}'")

        return self._extract_ledger_tag_id(matches[0], account_hint=candidate)

    @staticmethod
    def _extract_ledger_tag_id(row: dict[str, Any], *, account_hint: str) -> int:
        ledger_tag_id = row.get("LedgerTagId")
        if not isinstance(ledger_tag_id, int):
            raise LedgerPostError(
                f"LedgerAccount '{account_hint}' is missing integer LedgerTagId; cannot query LedgerPost"
            )
        return ledger_tag_id

    def _get_ledger_account_workflow(self) -> LedgerAccountWorkflow:
        if self._ledger_account_workflow is None:
            self._ledger_account_workflow = LedgerAccountWorkflow(self._client, self._fiscal_id)
        return self._ledger_account_workflow
