from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class TransactionError(ValueError):
    """Base error for transaction workflow operations."""


class VoucherNotFoundError(TransactionError):
    """Raised when no voucher can be matched by voucher number."""


class VoucherAmbiguousError(TransactionError):
    """Raised when more than one voucher matches voucher number selector."""


@dataclass
class TransactionWorkflow:
    """Workflow helper for transaction-centric voucher/detail endpoints."""

    _client: Any
    _fiscal_id: str

    def get_vouchers(
        self,
        *,
        voucher_number_from: int | None = None,
        voucher_number_to: int | None = None,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self._client.finance.api_voucher__get_get__api__fiscal_fiscal_id__voucher(
            fiscal_id=self._fiscal_id,
            options_voucher_number_from=voucher_number_from,
            options_voucher_number_to=voucher_number_to,
            options_show_deactivated=show_deactivated,
            options_page=page,
            options_page_size=page_size,
            options_force_no_paging=force_no_paging,
        )

    def get_voucher_by_number(self, voucher_number: int, *, show_deactivated: bool = False) -> dict[str, Any]:
        payload = self.get_vouchers(
            voucher_number_from=voucher_number,
            voucher_number_to=voucher_number,
            force_no_paging=True,
            page=0,
            page_size=100,
            show_deactivated=show_deactivated,
        )
        entities = self._extract_entities(payload)

        if not entities:
            raise VoucherNotFoundError(f"No voucher found for voucher number {voucher_number}")
        if len(entities) > 1:
            raise VoucherAmbiguousError(
                f"More than one voucher matched voucher number {voucher_number}"
            )

        return entities[0]

    def get_voucher_id_by_number(self, voucher_number: int, *, show_deactivated: bool = False) -> int:
        voucher = self.get_voucher_by_number(voucher_number, show_deactivated=show_deactivated)
        voucher_id = voucher.get("Id")
        if not isinstance(voucher_id, int):
            raise TransactionError("Voucher response missing integer Id field")
        return voucher_id

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

    def get_transactions_by_voucher_number(
        self,
        voucher_number: int,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        voucher_id = self.get_voucher_id_by_number(voucher_number, show_deactivated=show_deactivated)
        return self.get_transactions_by_voucher(
            voucher_id,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
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

    def get_posting_details_by_voucher_number(
        self,
        voucher_number: int,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> list[dict[str, Any]]:
        voucher_id = self.get_voucher_id_by_number(voucher_number, show_deactivated=show_deactivated)
        return self.get_posting_details_by_voucher(
            voucher_id,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

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