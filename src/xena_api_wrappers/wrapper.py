from __future__ import annotations

import importlib
from typing import Any

from .core import ClientFactory, DateInput, default_client_factory
from .credentials import XenaCredentials
from .workflows import (
    ArticleWorkflow,
    ArticleGroupWorkflow,
    OrderReadWorkflow,
    OrderWriteWorkflow,
    FiscalPeriodWorkflow,
    LedgerListWorkflow,
    LedgerAccountWorkflow,
    LedgerTagWorkflow,
    VatWorkflow,
    LedgerGroupDataWorkflow,
    LedgerGroupDataDetailWorkflow,
    LedgerGroupWorkflow,
    PartnerLedgerWorkflow,
    LedgerPostWorkflow,
    PartnerWorkflow,
    VoucherDraftWorkflow,
    TransactionWorkflow,
)



class XenaApiWrapper:
    """High-level, task-oriented wrapper on top of xena-client."""

    def __init__(
        self,
        api_key: str | None = None,
        fiscal_id: str | None = None,
        *,
        credentials: XenaCredentials | None = None,
        client_factory: ClientFactory | None = None,
    ) -> None:
        if credentials is None:
            if not api_key or not fiscal_id:
                raise ValueError("Provide either credentials or both api_key and fiscal_id")
            credentials = XenaCredentials(api_key=api_key, fiscal_id=str(fiscal_id))

        self._credentials = credentials
        factory = client_factory or default_client_factory
        self._client = factory(self._credentials.api_key, self._credentials.fiscal_id)
        self._fiscal_period_workflow: FiscalPeriodWorkflow | None = None
        self._ledger_list_workflow: LedgerListWorkflow | None = None
        self._ledger_account_workflow: LedgerAccountWorkflow | None = None
        self._ledger_tag_workflow: LedgerTagWorkflow | None = None
        self._vat_workflow: VatWorkflow | None = None
        self._ledger_group_workflow: LedgerGroupWorkflow | None = None
        self._ledger_group_data_workflow: LedgerGroupDataWorkflow | None = None
        self._ledger_group_data_detail_workflow: LedgerGroupDataDetailWorkflow | None = None
        self._ledger_post_workflow: LedgerPostWorkflow | None = None
        self._transaction_workflow: TransactionWorkflow | None = None
        self._partner_workflow: PartnerWorkflow | None = None
        self._partner_ledger_workflow: PartnerLedgerWorkflow | None = None
        self._voucher_draft_workflow: VoucherDraftWorkflow | None = None
        self._article_workflow: ArticleWorkflow | None = None
        self._article_group_workflow: ArticleGroupWorkflow | None = None
        self._order_read_workflow: OrderReadWorkflow | None = None
        self._order_write_workflow: OrderWriteWorkflow | None = None

    @classmethod
    def from_env(
        cls,
        *,
        prefix: str = "",
        load_dotenv: bool = False,
        dotenv_path: str | None = None,
        client_factory: ClientFactory | None = None,
    ) -> "XenaApiWrapper":
        if load_dotenv:
            try:
                dotenv_module = importlib.import_module("dotenv")
            except ImportError as exc:
                raise ImportError(
                    "python-dotenv is not installed. Install with: pip install xena-api-wrappers[dotenv]"
                ) from exc

            dotenv_load = getattr(dotenv_module, "load_dotenv")
            dotenv_load(dotenv_path=dotenv_path)

        creds = XenaCredentials.from_env(prefix=prefix)
        return cls(credentials=creds, client_factory=client_factory)

    @property
    def client(self) -> Any:
        """Expose the underlying xena-client for advanced use cases."""
        return self._client

    @property
    def fiscal_id(self) -> str:
        return self._credentials.fiscal_id

    @property
    def fiscal_period(self) -> FiscalPeriodWorkflow:
        if self._fiscal_period_workflow is None:
            self._fiscal_period_workflow = FiscalPeriodWorkflow(self._client, self.fiscal_id)
        return self._fiscal_period_workflow

    def get_fiscal_periods(self) -> Any:
        # Backward-compatible facade method.
        return self.fiscal_period.get_all()

    def get_fiscal_period_id_by_date(self, selected_date: DateInput) -> int:
        # Backward-compatible facade method.
        return self.fiscal_period.get_id_by_date(selected_date)

    @property
    def ledger(self) -> LedgerListWorkflow:
        if self._ledger_list_workflow is None:
            self._ledger_list_workflow = LedgerListWorkflow(self._client, self.fiscal_id)
        return self._ledger_list_workflow

    @property
    def ledger_account(self) -> LedgerAccountWorkflow:
        if self._ledger_account_workflow is None:
            self._ledger_account_workflow = LedgerAccountWorkflow(self._client, self.fiscal_id)
        return self._ledger_account_workflow

    @property
    def ledger_tag(self) -> LedgerTagWorkflow:
        if self._ledger_tag_workflow is None:
            self._ledger_tag_workflow = LedgerTagWorkflow(self._client, self.fiscal_id)
        return self._ledger_tag_workflow

    @property
    def ledger_group(self) -> LedgerGroupWorkflow:
        if self._ledger_group_workflow is None:
            self._ledger_group_workflow = LedgerGroupWorkflow(self._client, self.fiscal_id)
        return self._ledger_group_workflow

    @property
    def vat(self) -> VatWorkflow:
        if self._vat_workflow is None:
            self._vat_workflow = VatWorkflow(self._client, self.fiscal_id)
        return self._vat_workflow

    def get_ledger_groups(self) -> Any:
        return self.ledger_group.get_all()

    def get_ledgers(
        self,
        *,
        force_no_paging: bool = True,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        query_string: str | None = None,
        include_defaults: bool | None = None,
    ) -> Any:
        return self.ledger.get_all(
            force_no_paging=force_no_paging,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
            query_string=query_string,
            include_defaults=include_defaults,
        )

    def get_ledger_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self.ledger.get_entities(**kwargs)

    def get_ledger_by_id(self, ledger_id: int | str, **kwargs: Any) -> dict[str, Any]:
        return self.ledger.get_by_id(ledger_id, **kwargs)

    def get_ledger_by_description(self, description: str, **kwargs: Any) -> dict[str, Any]:
        return self.ledger.get_by_description(description, **kwargs)

    def get_ledger_id_by_description(self, description: str, **kwargs: Any) -> int:
        return self.ledger.get_id_by_description(description, **kwargs)

    @property
    def ledger_group_data(self) -> LedgerGroupDataWorkflow:
        if self._ledger_group_data_workflow is None:
            self._ledger_group_data_workflow = LedgerGroupDataWorkflow(
                self._client,
                self.fiscal_id,
                self.ledger_group,
                self.fiscal_period,
            )
        return self._ledger_group_data_workflow

    @property
    def ledger_group_data_detail(self) -> LedgerGroupDataDetailWorkflow:
        if self._ledger_group_data_detail_workflow is None:
            self._ledger_group_data_detail_workflow = LedgerGroupDataDetailWorkflow(
                self._client,
                self.fiscal_id,
                self.fiscal_period,
                self.ledger_group_data,
            )
        return self._ledger_group_data_detail_workflow

    @property
    def ledger_post(self) -> LedgerPostWorkflow:
        if self._ledger_post_workflow is None:
            self._ledger_post_workflow = LedgerPostWorkflow(
                self._client,
                self.fiscal_id,
                self.ledger_account,
            )
        return self._ledger_post_workflow

    @property
    def transaction(self) -> TransactionWorkflow:
        if self._transaction_workflow is None:
            self._transaction_workflow = TransactionWorkflow(
                self._client,
                self.fiscal_id,
            )
        return self._transaction_workflow

    @property
    def partner(self) -> PartnerWorkflow:
        if self._partner_workflow is None:
            self._partner_workflow = PartnerWorkflow(
                self._client,
                self.fiscal_id,
            )
        return self._partner_workflow

    @property
    def partner_ledger(self) -> PartnerLedgerWorkflow:
        if self._partner_ledger_workflow is None:
            self._partner_ledger_workflow = PartnerLedgerWorkflow(
                self._client,
                self.fiscal_id,
                self.fiscal_period,
            )
        return self._partner_ledger_workflow

    @property
    def voucher_draft(self) -> VoucherDraftWorkflow:
        if self._voucher_draft_workflow is None:
            self._voucher_draft_workflow = VoucherDraftWorkflow(
                self._client,
                self.fiscal_id,
                self.ledger,
            )
        return self._voucher_draft_workflow

    @property
    def article_group(self) -> ArticleGroupWorkflow:
        if self._article_group_workflow is None:
            self._article_group_workflow = ArticleGroupWorkflow(
                self._client,
                self.fiscal_id,
            )
        return self._article_group_workflow

    @property
    def article(self) -> ArticleWorkflow:
        if self._article_workflow is None:
            self._article_workflow = ArticleWorkflow(
                self._client,
                self.fiscal_id,
            )
        return self._article_workflow

    @property
    def order_read(self) -> OrderReadWorkflow:
        if self._order_read_workflow is None:
            self._order_read_workflow = OrderReadWorkflow(
                self._client,
                self.fiscal_id,
            )
        return self._order_read_workflow

    @property
    def order_write(self) -> OrderWriteWorkflow:
        if self._order_write_workflow is None:
            self._order_write_workflow = OrderWriteWorkflow(
                self._client,
                self.fiscal_id,
            )
        return self._order_write_workflow

    def get_all_accounts(self) -> list[dict[str, Any]]:
        return self.ledger_account.get_all_accounts()

    def get_ledger_tags(
        self,
        *,
        ledger_account: str | None = None,
        query_string: str | None = None,
        include_defaults: bool | None = None,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self.ledger_tag.get_all(
            ledger_account=ledger_account,
            query_string=query_string,
            include_defaults=include_defaults,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

    def get_ledger_tag_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self.ledger_tag.get_entities(**kwargs)

    def get_ledger_tag_by_number(self, number: int | str, **kwargs: Any) -> dict[str, Any]:
        return self.ledger_tag.get_by_number(number, **kwargs)

    def get_ledger_tag_id_by_number(self, number: int | str, **kwargs: Any) -> int:
        return self.ledger_tag.get_id_by_number(number, **kwargs)

    def get_settlement_tags(
        self,
        *,
        include_default: bool | None = None,
        query_string: str | None = None,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self.ledger_tag.get_settlement_tags(
            include_default=include_default,
            query_string=query_string,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

    def get_vats(
        self,
        *,
        query_string: str | None = None,
        include_defaults: bool | None = None,
        excluded_vat_id: int | None = None,
        exclude_import_type: bool | None = None,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self.vat.get_all(
            query_string=query_string,
            include_defaults=include_defaults,
            excluded_vat_id=excluded_vat_id,
            exclude_import_type=exclude_import_type,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

    def get_vat_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self.vat.get_entities(**kwargs)

    def get_vat_by_id(self, vat_id: int) -> Any:
        return self.vat.get_by_id(vat_id)

    def get_vat_types(
        self,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self.vat.get_types(
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

    def get_vats_by_type(
        self,
        vat_type: str,
        *,
        query_string: str | None = None,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self.vat.get_by_type(
            vat_type,
            query_string=query_string,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

    def get_vat_by_abbreviation(self, abbreviation: str, **kwargs: Any) -> dict[str, Any]:
        return self.vat.get_by_abbreviation(abbreviation, **kwargs)

    def get_vat_id_by_abbreviation(self, abbreviation: str, **kwargs: Any) -> int:
        return self.vat.get_id_by_abbreviation(abbreviation, **kwargs)

    def get_balance_accounts(self) -> list[dict[str, Any]]:
        return self.ledger_account.get_balance_accounts()

    def get_result_accounts(self) -> list[dict[str, Any]]:
        return self.ledger_account.get_result_accounts()

    def get_all_report_accounts(self, date_from: DateInput, date_to: DateInput) -> list[dict[str, Any]]:
        return self.ledger_group_data_detail.get_all_accounts(
            date_from=date_from,
            date_to=date_to,
        )

    def get_balance_report_accounts(self, date_from: DateInput, date_to: DateInput) -> list[dict[str, Any]]:
        return self.ledger_group_data_detail.get_balance_accounts(
            date_from=date_from,
            date_to=date_to,
        )

    def get_result_report_accounts(self, date_from: DateInput, date_to: DateInput) -> list[dict[str, Any]]:
        return self.ledger_group_data_detail.get_result_accounts(
            date_from=date_from,
            date_to=date_to,
        )

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
        return self.ledger_post.get_entries_by_account(
            account,
            date_from,
            date_to,
            include_running_totals=include_running_totals,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
            show_reconciled=show_reconciled,
            reverse_date_sort=reverse_date_sort,
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
        return self.transaction.get_transactions_by_voucher(
            voucher_id,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

    def get_voucher_by_number(self, voucher_number: int) -> dict[str, Any]:
        return self.transaction.get_voucher_by_number(voucher_number)

    def get_voucher_id_by_number(self, voucher_number: int) -> int:
        return self.transaction.get_voucher_id_by_number(voucher_number)

    def get_transactions_by_voucher_number(
        self,
        voucher_number: int,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> Any:
        return self.transaction.get_transactions_by_voucher_number(
            voucher_number,
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
        return self.transaction.get_posting_details(
            transaction_id,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

    def get_posting_details_by_voucher(
        self,
        voucher_id: int,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> list[dict[str, Any]]:
        return self.transaction.get_posting_details_by_voucher(
            voucher_id,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

    def get_posting_details_by_voucher_number(
        self,
        voucher_number: int,
        *,
        force_no_paging: bool = True,
        page: int = 0,
        page_size: int = 100,
        show_deactivated: bool = False,
    ) -> list[dict[str, Any]]:
        return self.transaction.get_posting_details_by_voucher_number(
            voucher_number,
            force_no_paging=force_no_paging,
            page=page,
            page_size=page_size,
            show_deactivated=show_deactivated,
        )

    def get_partners(
        self,
        *,
        query_string: str | None = None,
        partner_context_type: str | None = "Customer",
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = False,
        excluded_id: int | None = None,
        include_default: bool | None = None,
    ) -> Any:
        return self.partner.get_all(
            query_string=query_string,
            partner_context_type=partner_context_type,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
            excluded_id=excluded_id,
            include_default=include_default,
        )

    def get_partner_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self.partner.get_entities(**kwargs)

    def get_customers(self, **kwargs: Any) -> Any:
        return self.partner.get_customers(**kwargs)

    def get_suppliers(self, **kwargs: Any) -> Any:
        return self.partner.get_suppliers(**kwargs)

    def get_employees(self, **kwargs: Any) -> Any:
        return self.partner.get_employees(**kwargs)

    def get_partner_context_types(self) -> Any:
        return self.partner.get_context_types()

    def get_partner_by_id(self, partner_id: int) -> Any:
        return self.partner.get_by_id(partner_id)

    def get_partner_by_account_number(self, account_number: int) -> Any:
        return self.partner.get_by_account_number(account_number)

    def create_partner(self, dto: dict[str, Any]) -> Any:
        return self.partner.create(dto)

    def update_partner(self, partner_id: int, dto: dict[str, Any]) -> Any:
        return self.partner.update(partner_id, dto)

    def get_partner_contexts(
        self,
        partner_id: int,
        *,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
    ) -> Any:
        return self.partner.get_contexts(
            partner_id,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
        )

    def add_partner_context(
        self,
        partner_id: int,
        context_type: str,
        *,
        invoice_email: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        return self.partner.add_context(
            partner_id,
            context_type,
            invoice_email=invoice_email,
            data=data,
        )

    def get_partner_gln_numbers(
        self,
        partner_id: int,
        *,
        query_string: str | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
    ) -> Any:
        return self.partner.get_gln_numbers(
            partner_id,
            query_string=query_string,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
        )

    def get_partner_gln_number(self, gln_id: int) -> Any:
        return self.partner.get_gln_number(gln_id)

    def add_partner_gln_number(
        self,
        partner_id: int,
        *,
        gln: str | None = None,
        description: str | None = None,
        attention: str | None = None,
    ) -> Any:
        return self.partner.add_gln_number(
            partner_id,
            gln=gln,
            description=description,
            attention=attention,
        )

    def update_partner_gln_number(
        self,
        gln_id: int,
        *,
        gln: str,
        description: str | None = None,
        attention: str | None = None,
        partner_id: int | None = None,
    ) -> Any:
        return self.partner.update_gln_number(
            gln_id,
            gln=gln,
            description=description,
            attention=attention,
            partner_id=partner_id,
        )

    def delete_partner_gln_number(self, gln_id: int) -> Any:
        return self.partner.delete_gln_number(gln_id)

    def get_partner_delivery_addresses(
        self,
        partner_id: int,
        *,
        query_string: str | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
    ) -> Any:
        return self.partner.get_delivery_addresses(
            partner_id,
            query_string=query_string,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
        )

    def get_partner_delivery_address(self, delivery_address_id: int) -> Any:
        return self.partner.get_delivery_address(delivery_address_id)

    def add_partner_delivery_address(self, dto: dict[str, Any]) -> Any:
        return self.partner.add_delivery_address(dto)

    def update_partner_delivery_address(self, delivery_address_id: int, dto: dict[str, Any]) -> Any:
        return self.partner.update_delivery_address(delivery_address_id, dto)

    def delete_partner_delivery_address(self, delivery_address_id: int) -> Any:
        return self.partner.delete_delivery_address(delivery_address_id)

    def add_supplier_address(
        self,
        partner_id: int,
        *,
        name: str,
        street: str,
        postal_number: str,
        city: str,
        country_name: str = "NO",
        note: str | None = None,
        contact_name: str | None = None,
        title: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_default: bool = False,
    ) -> Any:
        return self.partner.add_supplier_address(
            partner_id,
            name=name,
            street=street,
            postal_number=postal_number,
            city=city,
            country_name=country_name,
            note=note,
            contact_name=contact_name,
            title=title,
            phone=phone,
            email=email,
            is_default=is_default,
        )

    def create_customer(
        self,
        *,
        name: str,
        postal_number: str,
        email: str,
        street: str | None = None,
        country_name: str = "NO",
        partner_type: str = "xena_partnertype_company",
    ) -> dict[str, Any]:
        return self.partner.create_customer(
            name=name,
            postal_number=postal_number,
            email=email,
            street=street,
            country_name=country_name,
            partner_type=partner_type,
        )

    def create_supplier(
        self,
        *,
        name: str,
        postal_number: str,
        email: str,
        street: str | None = None,
        country_name: str = "NO",
        partner_type: str = "xena_partnertype_company",
    ) -> dict[str, Any]:
        return self.partner.create_supplier(
            name=name,
            postal_number=postal_number,
            email=email,
            street=street,
            country_name=country_name,
            partner_type=partner_type,
        )

    def get_partner_posts(
        self,
        partner_id: int,
        *,
        context_type: str | None = None,
        fiscal_period_id: int | None = None,
        fiscal_date_from: DateInput | None = None,
        fiscal_date_to: DateInput | None = None,
        is_settled: bool | None = None,
        post_type: str | None = None,
        is_parked: bool | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 30,
        force_no_paging: bool = False,
    ) -> Any:
        return self.partner_ledger.get_posts(
            partner_id,
            context_type=context_type,
            fiscal_period_id=fiscal_period_id,
            fiscal_date_from=fiscal_date_from,
            fiscal_date_to=fiscal_date_to,
            is_settled=is_settled,
            post_type=post_type,
            is_parked=is_parked,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
        )

    def get_partner_posts_for_year(
        self,
        partner_id: int,
        year: int | str,
        *,
        context_type: str | None = None,
        is_settled: bool | None = None,
        post_type: str | None = None,
        is_parked: bool | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 30,
        force_no_paging: bool = False,
    ) -> Any:
        return self.partner_ledger.get_posts_for_year(
            partner_id,
            year,
            context_type=context_type,
            is_settled=is_settled,
            post_type=post_type,
            is_parked=is_parked,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
        )

    def get_customer_partner_posts(self, partner_id: int, **kwargs: Any) -> Any:
        return self.partner_ledger.get_customer_posts(partner_id, **kwargs)

    def get_supplier_partner_posts(self, partner_id: int, **kwargs: Any) -> Any:
        return self.partner_ledger.get_supplier_posts(partner_id, **kwargs)

    def get_partner_balances_by_date(
        self,
        calculated_by: DateInput,
        *,
        context_type: str | None = "ContextType_Customer",
        account_number_from: int | None = None,
        account_number_to: int | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
    ) -> Any:
        return self.partner_ledger.get_balances_by_date(
            calculated_by,
            context_type=context_type,
            account_number_from=account_number_from,
            account_number_to=account_number_to,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
        )

    def get_customer_balances_by_date(self, calculated_by: DateInput, **kwargs: Any) -> Any:
        return self.partner_ledger.get_customer_balances_by_date(calculated_by, **kwargs)

    def get_supplier_balances_by_date(self, calculated_by: DateInput, **kwargs: Any) -> Any:
        return self.partner_ledger.get_supplier_balances_by_date(calculated_by, **kwargs)

    def get_partner_unsettled_posts(
        self,
        partner_id: int,
        *,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
        force_no_paging: bool = True,
    ) -> Any:
        return self.partner_ledger.get_unsettled_posts(
            partner_id,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
        )

    def get_currency_difference_tag(self, *, force_no_paging: bool = True) -> dict[str, Any]:
        return self.partner_ledger.get_currency_difference_tag(force_no_paging=force_no_paging)

    def build_partner_settlement_payload_safe(
        self,
        partner_id: int,
        partner_post_ids: list[int],
        *,
        pay_date: DateInput,
        partial_settle_id: int | None = None,
        currency_abbreviation: str | None = None,
    ) -> dict[str, Any]:
        return self.partner_ledger.build_settlement_payload_safe(
            partner_id,
            partner_post_ids,
            pay_date=pay_date,
            partial_settle_id=partial_settle_id,
            currency_abbreviation=currency_abbreviation,
        )

    def settle_partner_posts_safe(
        self,
        partner_id: int,
        partner_post_ids: list[int],
        *,
        pay_date: DateInput,
        partial_settle_id: int | None = None,
        currency_abbreviation: str | None = None,
    ) -> Any:
        return self.partner_ledger.settle_partner_posts_safe(
            partner_id,
            partner_post_ids,
            pay_date=pay_date,
            partial_settle_id=partial_settle_id,
            currency_abbreviation=currency_abbreviation,
        )

    def get_voucher_modified_history(
        self,
        *,
        force_no_paging: bool = True,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
    ) -> Any:
        return self.voucher_draft.get_modified_history(
            force_no_paging=force_no_paging,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
        )

    def get_voucher_draft_ledgers(self, **kwargs: Any) -> Any:
        return self.voucher_draft.list_ledgers(**kwargs)

    def get_voucher_draft_ledger_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self.voucher_draft.list_ledger_entities(**kwargs)

    def get_voucher_draft_ledger_by_id(self, ledger_id: int) -> Any:
        return self.voucher_draft.get_ledger_by_id(ledger_id)

    def get_voucher_draft_ledger_id_by_description(self, description: str, **kwargs: Any) -> int:
        return self.voucher_draft.get_ledger_id_by_description(description, **kwargs)

    def set_voucher_draft_ledger_by_name(self, description: str, **kwargs: Any) -> int:
        return self.voucher_draft.set_ledger_by_name(description, **kwargs)

    def set_voucher_draft_ledger_by_id(self, ledger_id: int, **kwargs: Any) -> int:
        return self.voucher_draft.set_ledger_by_id(ledger_id, **kwargs)

    def get_selected_voucher_draft_ledger_id(self) -> int | None:
        return self.voucher_draft.get_selected_ledger_id()

    def get_voucher_draft_lines(
        self,
        ledger_id: int,
        *,
        query_string: str | None = None,
        force_no_paging: bool = True,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 100,
    ) -> Any:
        return self.voucher_draft.get_lines(
            ledger_id,
            query_string=query_string,
            force_no_paging=force_no_paging,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
        )

    def get_voucher_draft_partner_payment_suggestions(
        self,
        query_string: str,
        *,
        per_date: DateInput | None = None,
        include_manual_payment: bool = True,
        context_type: str | None = None,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 30,
        force_no_paging: bool = False,
    ) -> Any:
        return self.voucher_draft.get_partner_payment_suggestions(
            query_string,
            per_date=per_date,
            include_manual_payment=include_manual_payment,
            context_type=context_type,
            show_deactivated=show_deactivated,
            page=page,
            page_size=page_size,
            force_no_paging=force_no_paging,
        )

    def apply_voucher_draft_settled_partner_posts(
        self,
        dto: dict[str, Any],
        *,
        settled_partner_post_ids: list[int],
        partial_settle_id: int | None = None,
    ) -> dict[str, Any]:
        return self.voucher_draft.apply_settled_partner_posts(
            dto,
            settled_partner_post_ids=settled_partner_post_ids,
            partial_settle_id=partial_settle_id,
        )

    def create_voucher_draft_line(self, dto: dict[str, Any]) -> Any:
        return self.voucher_draft.create_line(dto)

    def set_voucher_draft_ensure_xena_ui_is_happy(self, enabled: bool) -> bool:
        return self.voucher_draft.set_ensure_xena_ui_is_happy(enabled)

    def voucher_draft_dont_care_about_what_ui_feels(self) -> bool:
        return self.voucher_draft.dont_care_about_what_ui_feels()

    def create_voucher_draft_lines_convenience(
        self,
        rows: dict[str, Any] | list[dict[str, Any]],
        *,
        ledger_id: int | None = None,
        ledger_description: str | None = None,
        voucher_number: int | None = None,
        strict_settlement_contra: bool = True,
    ) -> dict[str, Any]:
        return self.voucher_draft.create_lines_convenience(
            rows,
            ledger_id=ledger_id,
            ledger_description=ledger_description,
            voucher_number=voucher_number,
            strict_settlement_contra=strict_settlement_contra,
        )

    def get_voucher_draft_convenience_dto_help(self) -> dict[str, Any]:
        return self.voucher_draft.get_convenience_dto_help()

    def create_simple_order(
        self,
        *,
        customer_account_number: int,
        our_reference: str | None = None,
        your_reference: str | None = None,
        order_date: DateInput | None = None,
        gln_number: str | None = None,
        lines: list[dict[str, Any]] | None = None,
        hydrate_partner: bool = True,
        hydrate_articles: bool = True,
    ) -> dict[str, Any]:
        return self.order_write.create_simple_order(
            customer_account_number=customer_account_number,
            our_reference=our_reference,
            your_reference=your_reference,
            order_date=order_date,
            gln_number=gln_number,
            lines=lines,
            hydrate_partner=hydrate_partner,
            hydrate_articles=hydrate_articles,
        )

    def create_and_send_invoice_simple(
        self,
        *,
        customer_account_number: int,
        lines: list[dict[str, Any]],
        distribution: str | None = None,
        our_reference: str | None = None,
        your_reference: str | None = None,
        order_date: DateInput | None = None,
        gln_number: str | None = None,
        email_to_addresses: str | None = None,
        email_subject: str | None = None,
        email_body_text: str | None = None,
        email_include_signature: bool = True,
        email_document_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        return self.order_write.create_and_send_invoice_simple(
            customer_account_number=customer_account_number,
            lines=lines,
            distribution=distribution,
            our_reference=our_reference,
            your_reference=your_reference,
            order_date=order_date,
            gln_number=gln_number,
            email_to_addresses=email_to_addresses,
            email_subject=email_subject,
            email_body_text=email_body_text,
            email_include_signature=email_include_signature,
            email_document_ids=email_document_ids,
        )

    def create_invoice_by_number(
        self,
        invoice_number: int | str,
        date: DateInput | None = None,
        distribution: str | None = None,
        *,
        email_to_addresses: str | None = None,
        email_subject: str | None = None,
        email_body_text: str | None = None,
        email_include_signature: bool = True,
        email_document_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        return self.order_write.create_invoice_by_number(
            invoice_number,
            date,
            distribution,
            email_to_addresses=email_to_addresses,
            email_subject=email_subject,
            email_body_text=email_body_text,
            email_include_signature=email_include_signature,
            email_document_ids=email_document_ids,
        )

    def update_voucher_draft_line(self, ledger_line_id: int, dto: dict[str, Any]) -> Any:
        return self.voucher_draft.update_line(ledger_line_id, dto)

    def delete_voucher_draft_line(self, ledger_line_id: int) -> Any:
        return self.voucher_draft.delete_line(ledger_line_id)

    def update_voucher_draft_ledger(self, ledger_id: int, dto: dict[str, Any]) -> Any:
        return self.voucher_draft.update_ledger(ledger_id, dto)

    def preview_voucher_draft_summary(
        self,
        ledger_id: int,
        *,
        bookkeep_all: bool = False,
        ledger_line_ids: list[int] | None = None,
    ) -> Any:
        return self.voucher_draft.preview_summary(
            ledger_id,
            bookkeep_all=bookkeep_all,
            ledger_line_ids=ledger_line_ids,
        )
