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

    def get_transactions_by_voucher(
        self,
        voucher_id: int,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self._client.finance.api_voucher__get_transactions_by_voucher_get__api__fiscal_fiscal_id__voucher_id__transaction(
            id=voucher_id,
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

    def get_posting_details(
        self,
        transaction_id: int,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> dict[str, Any]:
        ledger_post = self._client.finance.api_transaction__get_ledger_post_by_transaction_get__api__fiscal_fiscal_id__transaction_id__ledger_post(
            id=transaction_id,
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )
        partner_post = self._client.finance.api_transaction__get_partner_post_by_transaction_get__api__fiscal_fiscal_id__transaction_id__partner_post(
            id=transaction_id,
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )
        article_post = self._client.finance.api_transaction__get_article_post_by_transaction_get__api__fiscal_fiscal_id__transaction_id__article_post(
            id=transaction_id,
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
        )

        return {
            "transaction_id": transaction_id,
            "ledger_post": ledger_post,
            "partner_post": partner_post,
            "article_post": article_post,
        }

    def get_posting_details_by_voucher(
        self,
        voucher_id: int,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> list[dict[str, Any]]:
        transactions = self.get_transactions_by_voucher(
            voucher_id,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )
        entities = self._extract_entities(transactions)

        details: list[dict[str, Any]] = []
        for transaction in entities:
            transaction_id = transaction.get("Id")
            if isinstance(transaction_id, int):
                details.append(
                    self.get_posting_details(
                        transaction_id,
                        force_no_paging=force_no_paging,
                        page=page,
                        page_size=page_size,
                        show_deactivated=show_deactivated,
                    )
                )

        return details

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

    @staticmethod
    def _extract_entities(raw_payload: Any) -> list[dict[str, Any]]:
        if isinstance(raw_payload, dict):
            entities = raw_payload.get("Entities")
            if isinstance(entities, list):
                return [e for e in entities if isinstance(e, dict)]
        if hasattr(raw_payload, "to_dict"):
            converted = raw_payload.to_dict()
            if isinstance(converted, dict):
                entities = converted.get("Entities")
                if isinstance(entities, list):
                    return [e for e in entities if isinstance(e, dict)]
        return []
