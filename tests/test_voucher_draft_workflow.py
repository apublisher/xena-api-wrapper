from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.bookkeeping import (
    VoucherDraftLedgerNotFoundError,
    VoucherDraftWorkflow,
)


class _FakeFinance:
    def __init__(self) -> None:
        self._next_id = 3037274927
        self.last_updated_dto: dict[str, Any] | None = None

    def api_bookkeeping__get_voucher_modified_history_get__api__fiscal_fiscal_id__bookkeeping__voucher_modified_history(
        self,
        fiscal_id: str,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
    ) -> dict[str, Any]:
        _ = (
            fiscal_id,
            list_options_show_deactivated,
            list_options_page,
            list_options_page_size,
            list_options_force_no_paging,
        )
        return {"Count": 1, "Entities": [{"LedgerId": 2265976208}]}

    def api_ledger__get_get__api__fiscal_fiscal_id__ledger(
        self,
        fiscal_id: str,
        querystring: str | None = None,
        include_defaults: bool | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
    ) -> dict[str, Any]:
        _ = (
            fiscal_id,
            querystring,
            include_defaults,
            list_options_show_deactivated,
            list_options_page,
            list_options_page_size,
            list_options_force_no_paging,
        )
        return {
            "Count": 2,
            "Entities": [
                {"Id": 2265976208, "Description": "Bank2Xena"},
                {"Id": 2181157620, "Description": "Finans"},
            ],
        }

    def api_ledger__get_get__api__fiscal_fiscal_id__ledger_id(self, fiscal_id: str, id: int) -> dict[str, Any]:
        _ = fiscal_id
        return {"Id": id, "Description": "Bank2Xena"}

    def api_ledger_line__get_get__api__fiscal_fiscal_id__ledger_id__line(
        self,
        id: int,
        fiscal_id: str,
        query_string: str | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
    ) -> dict[str, Any]:
        _ = (
            fiscal_id,
            query_string,
            list_options_show_deactivated,
            list_options_page,
            list_options_page_size,
            list_options_force_no_paging,
        )
        return {"Count": 1, "Entities": [{"Id": 3037274927, "LedgerId": id}]}

    def api_ledger_line__post_post__api__fiscal_fiscal_id__ledger_line(
        self, dto: dict[str, Any], fiscal_id: str
    ) -> dict[str, Any]:
        _ = fiscal_id
        payload: dict[str, Any] = {"Id": self._next_id, "VoucherNumber": 15000, **dto}
        self._next_id += 1
        return payload

    def api_ledger_line__put_put__api__fiscal_fiscal_id__ledger_line_id(
        self, dto: dict[str, Any], fiscal_id: str, id: str
    ) -> dict[str, Any]:
        _ = fiscal_id
        self.last_updated_dto = dict(dto)
        return {"Id": id, **dto}

    def api_ledger_line__delete_delete__api__fiscal_fiscal_id__ledger_line_id(
        self, fiscal_id: str, id: int
    ) -> dict[str, Any]:
        _ = fiscal_id
        return {"Deleted": id}

    def api_ledger__put_put__api__fiscal_fiscal_id__ledger_id(
        self, ledger: dict[str, Any], fiscal_id: str, id: str
    ) -> dict[str, Any]:
        _ = fiscal_id
        return {"Id": id, **ledger}

    def api_ledger__post_summary_post__api__fiscal_fiscal_id__ledger_id__summary(
        self, id: int, data: dict[str, Any], fiscal_id: str
    ) -> dict[str, Any]:
        _ = fiscal_id
        return {"LedgerId": id, "Payload": data}

    def api_ledger_tag__get_get__api__fiscal_fiscal_id__ledger_tag(
        self,
        fiscal_id: str,
        ledger_account: str | None = None,
        query_string: str | None = None,
        include_defaults: bool | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (
            fiscal_id,
            ledger_account,
            query_string,
            include_defaults,
            list_options_show_deactivated,
            list_options_page,
            list_options_page_size,
            list_options_force_no_paging,
            kwargs,
        )
        return {
            "Count": 4,
            "Entities": [
                {"Id": 10, "Number": 1920, "Description": "DNB", "LedgerTagType": "LedgerTagType_Settlement"},
                {"Id": 11, "Number": 3000, "Description": "Sales", "LedgerTagType": "LedgerTagType_Default"},
                {"Id": 12, "Number": 1900, "Description": "Cash", "LedgerTagType": "LedgerTagType_Settlement"},
                {"Id": 13, "Number": 2700, "Description": "MVA", "LedgerTagType": "LedgerTagType_Settlement"},
            ],
        }

    def api_ledger_account__get_list_get__api__fiscal_fiscal_id__ledger_account(
        self,
        fiscal_id: str,
        ledger_account: str | None = None,
        query_string: str | None = None,
        include_default: bool | None = None,
        exclude_vats: bool | None = None,
        exclude_article_groups: bool | None = None,
        exclude_ledger_tags: bool | None = None,
        exclude_system_accounts: bool | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
    ) -> dict[str, Any]:
        _ = (
            fiscal_id,
            ledger_account,
            query_string,
            include_default,
            exclude_vats,
            exclude_article_groups,
            exclude_ledger_tags,
            exclude_system_accounts,
            list_options_show_deactivated,
            list_options_page,
            list_options_page_size,
            list_options_force_no_paging,
        )
        return {
            "Count": 2,
            "Entities": [
                {"Id": "acct-3001", "AccountNumber": 3001, "LedgerTagId": None},
                {"Id": "acct-1920", "AccountNumber": 1920, "LedgerTagId": 10},
            ],
        }

    def api_vat__get_get__api__fiscal_fiscal_id__vat(
        self,
        fiscal_id: str,
        querystring: str | None = None,
        include_defaults: bool | None = None,
        excluded_vat_id: int | None = None,
        exclude_import_type: bool | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (
            fiscal_id,
            querystring,
            include_defaults,
            excluded_vat_id,
            exclude_import_type,
            list_options_show_deactivated,
            list_options_page,
            list_options_page_size,
            list_options_force_no_paging,
            kwargs,
        )
        return {
            "Count": 2,
            "Entities": [
                {"Id": 100, "Abbreviation": "1", "Description": "Input 25%"},
                {"Id": 101, "Abbreviation": "3", "Description": "Output 25%"},
            ],
        }


class _FakePartner:
    def api_partner__get_by_account_number_get__api__fiscal_fiscal_id__partner__by_account_number_account_number(
        self,
        account_number: int,
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        if account_number == 20001:
            return {"Id": 555, "AccountNumber": 20001}
        return {"Id": None}


class VoucherDraftWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.finance = _FakeFinance()
        client = SimpleNamespace(finance=self.finance, partner=_FakePartner())
        self.workflow = VoucherDraftWorkflow(client, "104779")

    def test_get_modified_history(self) -> None:
        payload = self.workflow.get_modified_history()
        self.assertEqual(payload["Count"], 1)

    def test_list_ledger_entities(self) -> None:
        entities = self.workflow.list_ledger_entities(force_no_paging=True)
        self.assertEqual(len(entities), 2)
        self.assertEqual(entities[0]["Description"], "Bank2Xena")

    def test_get_ledger_id_by_description(self) -> None:
        ledger_id = self.workflow.get_ledger_id_by_description("Finans")
        self.assertEqual(ledger_id, 2181157620)

    def test_get_lines(self) -> None:
        payload = self.workflow.get_lines(2265976208)
        self.assertEqual(payload["Entities"][0]["LedgerId"], 2265976208)

    def test_create_update_delete_line(self) -> None:
        created = self.workflow.create_line({"LedgerId": 2265976208})
        self.assertEqual(created["Id"], 3037274927)

        updated = self.workflow.update_line(3037274927, {"Description": "Updated"})
        self.assertEqual(updated["Description"], "Updated")

        deleted = self.workflow.delete_line(3037274927)
        self.assertEqual(deleted["Deleted"], 3037274927)

    def test_create_line_defaults_to_ui_happy_roundtrip(self) -> None:
        _ = self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
        self.assertIsNotNone(self.finance.last_updated_dto)

    def test_create_line_can_skip_ui_happy_roundtrip(self) -> None:
        self.workflow.set_ensure_xena_ui_is_happy(False)
        _ = self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
        self.assertIsNone(self.finance.last_updated_dto)

    def test_create_line_uses_selected_default_ledger(self) -> None:
        selected_id = self.workflow.set_ledger_by_name("Finans")
        self.assertEqual(selected_id, 2181157620)

        created = self.workflow.create_line({"FiscalDateDays": 20544, "VoucherNumber": None})
        self.assertEqual(created["LedgerId"], 2181157620)

    def test_create_line_uses_dto_description_when_present(self) -> None:
        created = self.workflow.create_line(
            {
                "LedgerDescription": "Bank2Xena",
                "FiscalDateDays": 20544,
            }
        )
        self.assertEqual(created["LedgerId"], 2265976208)

    def test_create_line_dto_ledger_overrides_selected_default(self) -> None:
        self.workflow.set_ledger_by_name("Finans")
        created = self.workflow.create_line({"LedgerId": 2265976208})
        self.assertEqual(created["LedgerId"], 2265976208)

    def test_create_line_requires_ledger_when_no_default_set(self) -> None:
        with self.assertRaises(VoucherDraftLedgerNotFoundError):
            self.workflow.create_line({"FiscalDateDays": 20544})

    def test_preview_summary(self) -> None:
        payload = self.workflow.preview_summary(2265976208, bookkeep_all=False, ledger_line_ids=[1, 2])
        self.assertEqual(payload["Payload"]["bookkeepAll"], False)
        self.assertEqual(payload["Payload"]["ledgerLineIds"], [1, 2])

    def test_resolve_ledger_id(self) -> None:
        self.assertEqual(self.workflow.resolve_ledger_id(ledger_id=123), 123)
        self.assertEqual(
            self.workflow.resolve_ledger_id(ledger_description="Bank2Xena"),
            2265976208,
        )

    def test_set_voucher_alias_methods(self) -> None:
        ledger_id = self.workflow.setVoucherByName("Bank2Xena")
        self.assertEqual(ledger_id, 2265976208)
        self.assertEqual(self.workflow.get_selected_ledger_id(), 2265976208)

        ledger_id = self.workflow.setVoucherById(2181157620)
        self.assertEqual(ledger_id, 2181157620)
        self.assertEqual(self.workflow.get_selected_ledger_id(), 2181157620)

    def test_resolve_ledger_id_requires_input(self) -> None:
        with self.assertRaises(VoucherDraftLedgerNotFoundError):
            self.workflow.resolve_ledger_id()

    def test_create_lines_convenience_single_finance_row(self) -> None:
        self.workflow.set_ledger_by_name("Bank2Xena")
        result = self.workflow.create_lines_convenience(
            {
                "date": "2026-04-01",
                "type": "finance",
                "amount": "200,00",
                "account": 3000,
                "contra_account": 1920,
                "description": "Test line",
                "vatnumber": "3",
            }
        )

        self.assertEqual(result["LineCount"], 1)
        line = result["Lines"][0]["Updated"]
        self.assertEqual(line["LedgerTagId"], 11)
        self.assertEqual(line["ContraTagId"], 10)
        self.assertEqual(line["VatId"], 101)
        self.assertEqual(line["Amount"], 200.0)

    def test_create_lines_convenience_multi_row_reuses_voucher_number(self) -> None:
        self.workflow.set_ledger_by_name("Bank2Xena")
        result = self.workflow.create_lines_convenience(
            [
                {
                    "date": "2026-04-01",
                    "type": "finance",
                    "amount": 100,
                    "account": 3000,
                    "contra_account": 1920,
                    "description": "line1",
                },
                {
                    "date": "2026-04-01",
                    "type": "partnerpayment",
                    "amount": "-100.00",
                    "partner_number": "20001",
                    "account": 3000,
                    "description": "line2",
                },
            ]
        )

        self.assertEqual(result["LineCount"], 2)
        self.assertEqual(result["VoucherNumber"], 15000)
        second = result["Lines"][1]["Updated"]
        self.assertEqual(second["VoucherNumber"], 15000)
        self.assertEqual(second["PartnerId"], 555)

    def test_create_lines_convenience_rejects_non_settlement_contra(self) -> None:
        self.workflow.set_ledger_by_name("Bank2Xena")
        with self.assertRaisesRegex(Exception, "not a settlement tag"):
            self.workflow.create_lines_convenience(
                {
                    "date": "2026-04-01",
                    "type": "finance",
                    "amount": 100,
                    "account": 3000,
                    "contra_account": 3000,
                    "description": "bad contra",
                }
            )

    def test_create_lines_convenience_rejects_unknown_alias_key(self) -> None:
        self.workflow.set_ledger_by_name("Bank2Xena")
        with self.assertRaisesRegex(Exception, r"Unsupported key\(s\) in convenience row"):
            self.workflow.create_lines_convenience(
                {
                    "date": "2026-04-01",
                    "type": "partnerpayment",
                    "amount": 2000,
                    "partner_number": 20001,
                    "counteraccount": 1920,
                    "description": "alias contra",
                }
            )

    def test_create_lines_convenience_partnerpayment_requires_account(self) -> None:
        self.workflow.set_ledger_by_name("Bank2Xena")
        with self.assertRaisesRegex(Exception, "partnerpayment requires account"):
            self.workflow.create_lines_convenience(
                {
                    "date": "2026-04-01",
                    "type": "partnerpayment",
                    "amount": 2000,
                    "partner_number": 20001,
                    "description": "missing account",
                }
            )

    def test_get_convenience_dto_help(self) -> None:
        help_data = self.workflow.get_convenience_dto_help()
        accepted = help_data["accepted_keys"]
        self.assertIn("date", accepted)
        self.assertIn("contra_account", accepted)
        self.assertNotIn("counteraccount", accepted)
        self.assertEqual(
            help_data["required_keys"]["type_partnerpayment"],
            ["partner_number", "account"],
        )

    def test_create_lines_convenience_rejects_account_without_ledger_tag_link(self) -> None:
        self.workflow.set_ledger_by_name("Bank2Xena")

        with self.assertRaisesRegex(Exception, "not linked to a ledger tag"):
            self.workflow.create_lines_convenience(
                {
                    "date": "2026-04-01",
                    "type": "finance",
                    "amount": 100,
                    "account": 3001,
                    "contra_account": 1920,
                    "description": "account without tag link",
                }
            )


if __name__ == "__main__":
    unittest.main()
