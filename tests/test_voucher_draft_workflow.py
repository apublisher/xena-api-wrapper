from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

from xena_api_wrappers.core import to_fiscal_date_int
from xena_api_wrappers.workflows.utils.fiscal_period import FiscalPeriodNotFoundError

from xena_api_wrappers.workflows.bookkeeping import (
    VoucherDraftLedgerNotFoundError,
    VoucherDraftValidationError,
    VoucherDraftWorkflow,
)


class _FakeFinance:
    def __init__(self) -> None:
        self._next_id = 3037274927
        self.last_updated_dto: dict[str, Any] | None = None
        self.last_payment_suggestion_call: dict[str, Any] | None = None
        self.periods = [
            {"Id": year, "Description": str(year),
             "FiscalPeriodStartDays": to_fiscal_date_int(f"{year}-01-01"),
             "FiscalPeriodEndDays": to_fiscal_date_int(f"{year}-12-31")}
            for year in (2025, 2026)
        ]
        self.ledgers = {
            ledger_id: {"Id": ledger_id, "Description": name, "FiscalPeriodId": 2026,
                        "Version": 3, "Minimum": 10000, "Maximum": 99999}
            for ledger_id, name in ((2265976208, "Bank2Xena"), (2181157620, "Finans"))
        }
        self.lines: dict[int, dict[str, Any]] = {}
        self.events: list[tuple[str, int, int]] = []
        self.ledger_updates: list[dict[str, Any]] = []
        self.created_dtos: list[dict[str, Any]] = []

    def api_fiscal_period__get_get__api__fiscal_fiscal_id__fiscal_period(
        self, **kwargs: Any,
    ) -> dict[str, Any]:
        return {"Entities": self.periods}

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
        return dict(self.ledgers[id])

    def api_ledger_line__get_get__api__fiscal_fiscal_id__ledger_line_id(
        self, fiscal_id: str, id: int,
    ) -> dict[str, Any]:
        return dict(self.lines[id])

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
        entities = [dict(row) for row in self.lines.values() if row.get("LedgerId") == id]
        return {"Count": len(entities), "Entities": entities}

    def api_ledger_line__post_post__api__fiscal_fiscal_id__ledger_line(
        self, dto: dict[str, Any], fiscal_id: str
    ) -> dict[str, Any]:
        _ = fiscal_id
        self.created_dtos.append(dict(dto))
        period_id = self.ledgers[dto["LedgerId"]]["FiscalPeriodId"]
        self.events.append(("create", dto["LedgerId"], period_id))
        payload: dict[str, Any] = {"Id": self._next_id, "VoucherNumber": 15000 if period_id == 2026 else 14000, **dto}
        self.lines[self._next_id] = dict(payload)
        self._next_id += 1
        return payload

    def api_ledger_line__put_put__api__fiscal_fiscal_id__ledger_line_id(
        self, dto: dict[str, Any], fiscal_id: str, id: str
    ) -> dict[str, Any]:
        _ = fiscal_id
        self.last_updated_dto = dict(dto)
        self.lines[int(id)].update(dto)
        saved = self.lines[int(id)]
        self.events.append(("update", saved["LedgerId"], self.ledgers[saved["LedgerId"]]["FiscalPeriodId"]))
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
        self.ledger_updates.append(dict(ledger))
        self.ledgers[int(id)] = dict(ledger)
        self.events.append(("period", int(id), ledger["FiscalPeriodId"]))
        return {"Id": id, **ledger}

    def api_ledger__post_summary_post__api__fiscal_fiscal_id__ledger_id__summary(
        self, id: int, data: dict[str, Any], fiscal_id: str
    ) -> dict[str, Any]:
        _ = fiscal_id
        return {"LedgerId": id, "Payload": data}

    def api_payment__get_payment_suggestion_get__api__fiscal_fiscal_id__payment__unsettled_post(
        self,
        query_string: str,
        fiscal_id: str,
        per_date: int | None = None,
        include_manual_payment: bool | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        self.last_payment_suggestion_call = {
            "query_string": query_string,
            "fiscal_id": fiscal_id,
            "per_date": per_date,
            "include_manual_payment": include_manual_payment,
            "show_deactivated": list_options_show_deactivated,
            "page": list_options_page,
            "page_size": list_options_page_size,
            "force_no_paging": list_options_force_no_paging,
        }
        return {
            "Count": 3,
            "Entities": [
                {"Id": 1, "VoucherNumber": 1001, "PostType": "PartnerPostType_CustomerInvoice"},
                {"Id": 2, "VoucherNumber": 2001, "PostType": "PartnerPostType_SupplierInvoice"},
                {"Id": 3, "VoucherNumber": 2002, "PostType": "PartnerPostType_SupplierPayment"},
            ],
        }

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
        self.finance.lines = {
            3037274927: {"Id": 3037274927, "LedgerId": 2265976208, "VoucherId": None, "IsDeactivated": False},
            3037274928: {"Id": 3037274928, "LedgerId": 2265976208, "VoucherId": 999, "IsDeactivated": False},
            3037274929: {"Id": 3037274929, "LedgerId": 2265976208, "VoucherId": None, "IsDeactivated": True},
        }
        payload = self.workflow.get_lines(2265976208)
        self.assertEqual(payload["Entities"][0]["LedgerId"], 2265976208)

    def test_get_unbooked_lines_by_ledger_id(self) -> None:
        self.finance.lines = {
            3037274927: {"Id": 3037274927, "LedgerId": 2265976208, "VoucherId": None, "IsDeactivated": False},
            3037274928: {"Id": 3037274928, "LedgerId": 2265976208, "VoucherId": 999, "IsDeactivated": False},
            3037274929: {"Id": 3037274929, "LedgerId": 2265976208, "VoucherId": None, "IsDeactivated": True},
        }
        payload = self.workflow.get_unbooked_lines(ledger_id=2265976208, force_no_paging=True)
        self.assertEqual(payload["LedgerId"], 2265976208)
        self.assertEqual(payload["Count"], 1)
        self.assertEqual(payload["Entities"][0]["Id"], 3037274927)

    def test_get_unbooked_lines_by_ledger_description(self) -> None:
        self.finance.lines = {
            3037274927: {"Id": 3037274927, "LedgerId": 2265976208, "VoucherId": None, "IsDeactivated": False},
            3037274928: {"Id": 3037274928, "LedgerId": 2265976208, "VoucherId": 999, "IsDeactivated": False},
            3037274929: {"Id": 3037274929, "LedgerId": 2265976208, "VoucherId": None, "IsDeactivated": True},
        }
        payload = self.workflow.get_unbooked_lines(ledger_description="Bank2Xena", force_no_paging=True)
        self.assertEqual(payload["LedgerId"], 2265976208)
        self.assertEqual(payload["Count"], 1)

    def test_get_unbooked_lines_can_include_deactivated(self) -> None:
        self.finance.lines = {
            3037274927: {"Id": 3037274927, "LedgerId": 2265976208, "VoucherId": None, "IsDeactivated": False},
            3037274928: {"Id": 3037274928, "LedgerId": 2265976208, "VoucherId": 999, "IsDeactivated": False},
            3037274929: {"Id": 3037274929, "LedgerId": 2265976208, "VoucherId": None, "IsDeactivated": True},
        }
        payload = self.workflow.get_unbooked_lines(
            ledger_id=2265976208,
            force_no_paging=True,
            exclude_deactivated=False,
        )
        self.assertEqual(payload["Count"], 2)

    def test_get_partner_payment_suggestions_filters_by_context_type(self) -> None:
        payload = self.workflow.get_partner_payment_suggestions(
            "mps",
            per_date="2026-04-13",
            context_type="supplier",
            include_manual_payment=True,
            force_no_paging=True,
        )

        self.assertEqual(payload["Count"], 2)
        entities = payload["Entities"]
        self.assertEqual(len(entities), 2)
        self.assertTrue(all(str(row.get("PostType", "")).startswith("PartnerPostType_Supplier") for row in entities))

        self.assertIsNotNone(self.finance.last_payment_suggestion_call)
        call = self.finance.last_payment_suggestion_call or {}
        self.assertEqual(call.get("query_string"), "mps")
        self.assertEqual(call.get("per_date"), 20556)

    def test_apply_settled_partner_posts_hydrates_expected_fields(self) -> None:
        dto = {"LedgerLineType": "LedgerLineType_PartnerPayment"}
        hydrated = self.workflow.apply_settled_partner_posts(
            dto,
            settled_partner_post_ids=[2937818664],
            partial_settle_id=2937818664,
        )

        self.assertEqual(hydrated["SettledPartnerPosts"], [{"Id": 2937818664}])
        self.assertEqual(hydrated["PartiallySettledPostId"], 2937818664)

    def test_apply_settled_partner_posts_rejects_non_integer_ids(self) -> None:
        invalid_ids: Any = [2937818664, "invalid"]
        with self.assertRaisesRegex(
            VoucherDraftValidationError, "settled_partner_post_ids must contain only integers"
        ):
            self.workflow.apply_settled_partner_posts({}, settled_partner_post_ids=invalid_ids)

    def test_apply_settled_partner_posts_rejects_non_integer_partial_id(self) -> None:
        invalid_id: Any = "invalid"
        with self.assertRaisesRegex(
            VoucherDraftValidationError, "partial_settle_id must be an integer when provided"
        ):
            self.workflow.apply_settled_partner_posts(
                {}, settled_partner_post_ids=[2937818664], partial_settle_id=invalid_id
            )

    def test_create_update_delete_line(self) -> None:
        created = self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
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
        created = self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
        self.assertEqual(created["LedgerId"], 2265976208)

    def test_create_line_requires_ledger_when_no_default_set(self) -> None:
        with self.assertRaises(VoucherDraftLedgerNotFoundError):
            self.workflow.create_line({"FiscalDateDays": 20544})

    def test_create_line_switches_period_before_post_and_preserves_ledger_fields(self) -> None:
        original = dict(self.finance.ledgers[2265976208])
        dto = {"LedgerId": 2265976208, "FiscalDateDays": to_fiscal_date_int("2025-12-31")}
        self.workflow.create_line(dto)

        self.assertEqual(self.finance.ledger_updates, [{**original, "FiscalPeriodId": 2025}])
        self.assertEqual([event[0] for event in self.finance.events], ["period", "create", "update"])
        self.assertTrue(all(event[2] == 2025 for event in self.finance.events))
        self.assertEqual(dto, {"LedgerId": 2265976208, "FiscalDateDays": to_fiscal_date_int("2025-12-31")})

    def test_same_period_does_not_update_ledger(self) -> None:
        self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
        self.assertEqual(self.finance.ledger_updates, [])

    def test_each_post_rechecks_period_even_if_another_caller_changed_it(self) -> None:
        dto = {"LedgerId": 2265976208, "FiscalDateDays": 20544}
        self.workflow.create_line(dto)
        self.finance.ledgers[2265976208]["FiscalPeriodId"] = 2025
        self.workflow.create_line(dto)
        self.assertEqual([row["FiscalPeriodId"] for row in self.finance.ledger_updates], [2026])

    def test_missing_fiscal_year_stops_before_any_write(self) -> None:
        with self.assertRaisesRegex(FiscalPeriodNotFoundError, "needs to be set up in Xena"):
            self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": to_fiscal_date_int("2027-01-01")})
        self.assertEqual(self.finance.events, [])

    def test_create_line_requires_explicit_integer_posting_date(self) -> None:
        for value in (None, True, "2026-04-01"):
            with self.subTest(value=value), self.assertRaisesRegex(VoucherDraftValidationError, "FiscalDateDays"):
                self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": value})
        self.assertEqual(self.finance.events, [])

    def test_failed_period_switch_does_not_create_line(self) -> None:
        self.workflow.update_ledger = Mock(side_effect=RuntimeError("Ledger cannot be updated"))
        with self.assertRaisesRegex(RuntimeError, "cannot be updated"):
            self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": to_fiscal_date_int("2025-01-01")})
        self.assertEqual(self.finance.created_dtos, [])
        self.assertIsNone(self.workflow._active_ledger_instance)

    def test_unconfirmed_period_switch_does_not_create_line(self) -> None:
        self.workflow.update_ledger = Mock(return_value=dict(self.finance.ledgers[2265976208]))
        with self.assertRaisesRegex(VoucherDraftValidationError, "did not confirm"):
            self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": to_fiscal_date_int("2025-01-01")})
        self.assertEqual(self.finance.created_dtos, [])

    def test_partial_update_uses_saved_line_date_and_ledger(self) -> None:
        self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": to_fiscal_date_int("2025-12-31")})
        self.finance.ledgers[2265976208]["FiscalPeriodId"] = 2026
        self.workflow.set_ledger_by_name("Finans")
        self.finance.events.clear()
        self.workflow.update_line(3037274927, {"Description": "Updated"})
        self.assertEqual(self.finance.events, [("period", 2265976208, 2025), ("update", 2265976208, 2025)])

    def test_update_to_another_year_is_rejected_before_writes(self) -> None:
        self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
        self.finance.events.clear()
        with self.assertRaisesRegex(VoucherDraftValidationError, "another fiscal period"):
            self.workflow.update_line(3037274927, {"FiscalDateDays": to_fiscal_date_int("2025-12-31")})
        self.assertEqual(self.finance.events, [])

    def test_mixed_period_sequence_rejected_before_any_write(self) -> None:
        with self.assertRaisesRegex(VoucherDraftValidationError, "same fiscal period"):
            self.workflow.create_lines_convenience(
                [{"date": day, "amount": 1} for day in ("2026-01-01", "2026-01-01", "2025-01-10")],
                ledger_id=2265976208,
            )
        self.assertEqual(self.finance.events, [])

    def test_later_missing_period_rejected_before_any_write(self) -> None:
        with self.assertRaises(FiscalPeriodNotFoundError):
            self.workflow.create_lines_convenience(
                [{"date": day, "amount": 1} for day in ("2025-01-01", "2027-01-01")],
                ledger_id=2265976208,
            )
        self.assertEqual(self.finance.events, [])

    def test_separate_sequence_cannot_change_year_of_populated_ledger(self) -> None:
        self.workflow.create_lines_convenience({"date": "2026-01-01", "amount": 1}, ledger_id=2265976208)
        self.finance.events.clear()
        with self.assertRaisesRegex(VoucherDraftValidationError, "another fiscal period"):
            self.workflow.create_lines_convenience({"date": "2025-01-10", "amount": 1}, ledger_id=2265976208)
        self.assertEqual(self.finance.events, [])

    def test_existing_voucher_id_does_not_bypass_guard(self) -> None:
        self.finance.lines[1] = {"Id": 1, "LedgerId": 2265976208,
            "FiscalDateDays": to_fiscal_date_int("2025-01-10"), "VoucherId": 999}
        with self.assertRaisesRegex(VoucherDraftValidationError, "another fiscal period"):
            self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
        self.assertEqual(self.finance.events, [])

    def test_unreadable_existing_dates_fail_closed(self) -> None:
        self.finance.lines[1] = {"Id": 1, "LedgerId": 2265976208}
        with self.assertRaisesRegex(VoucherDraftValidationError, "FiscalDateDays"):
            self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
        self.assertEqual(self.finance.events, [])

    def test_incomplete_listing_fails_closed(self) -> None:
        self.workflow.get_lines = Mock(return_value={"Count": 2, "Entities": []})
        with self.assertRaisesRegex(VoucherDraftValidationError, "all existing"):
            self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
        self.assertEqual(self.finance.events, [])

    def test_same_fiscal_period_can_span_calendar_years(self) -> None:
        self.finance.periods = [{"Id": 42,
            "FiscalPeriodStartDays": to_fiscal_date_int("2025-07-01"),
            "FiscalPeriodEndDays": to_fiscal_date_int("2026-06-30")}]
        result = self.workflow.create_lines_convenience(
            [{"date": day, "amount": amount} for day, amount in [("2025-12-31", 1), ("2026-01-01", -1)]],
            ledger_id=2265976208,
        )
        self.assertEqual([r["FiscalPeriodId"] for r in result["Lines"]], [42, 42])
        self.assertEqual(len(self.finance.ledger_updates), 1)

    def test_two_periods_in_same_calendar_year_are_rejected(self) -> None:
        self.finance.periods = [
            {"Id": 1, "FiscalPeriodStartDays": to_fiscal_date_int("2026-01-01"),
             "FiscalPeriodEndDays": to_fiscal_date_int("2026-06-30")},
            {"Id": 2, "FiscalPeriodStartDays": to_fiscal_date_int("2026-07-01"),
             "FiscalPeriodEndDays": to_fiscal_date_int("2026-12-31")},
        ]
        with self.assertRaisesRegex(VoucherDraftValidationError, "same fiscal period"):
            self.workflow.create_lines_convenience(
                [{"date": day, "amount": 1} for day in ("2026-01-01", "2026-07-01")],
                ledger_id=2265976208,
            )
        self.assertEqual(self.finance.events, [])

    def test_invalid_later_row_fails_before_period_change(self) -> None:
        with self.assertRaises(ValueError):
            self.workflow.create_lines_convenience(
                [{"date": "2025-01-01", "amount": 1},
                 {"date": "2025-01-02", "amount": "invalid"}], ledger_id=2265976208,
            )
        self.assertEqual(self.finance.events, [])

    def test_deactivated_lines_do_not_block_empty_draft_year_selection(self) -> None:
        self.finance.lines[1] = {"Id": 1, "LedgerId": 2265976208,
            "FiscalDateDays": 20544, "IsDeactivated": True}
        self.workflow.create_line({"LedgerId": 2265976208,
            "FiscalDateDays": to_fiscal_date_int("2025-01-01")})
        self.assertEqual(self.finance.ledger_updates[0]["FiscalPeriodId"], 2025)

    def test_list_response_and_partial_update_detect_existing_conflict(self) -> None:
        self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
        self.workflow.get_lines = Mock(return_value=[
            {"Id": 2, "LedgerId": 2265976208, "FiscalDateDays": to_fiscal_date_int("2025-01-01")}])
        self.finance.events.clear()
        with self.assertRaisesRegex(VoucherDraftValidationError, "another fiscal period"):
            self.workflow.update_line(3037274927, {"Description": "No write"})
        self.assertEqual(self.finance.events, [])

    def test_listing_failure_blocks_all_writes(self) -> None:
        for response in ({}, {"Entities": None}, {"Entities": [None]}):
            self.workflow.get_lines = Mock(return_value=response)
            with self.assertRaises(VoucherDraftValidationError):
                self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
        self.workflow.get_lines = Mock(side_effect=RuntimeError("Xena unavailable"))
        with self.assertRaises(RuntimeError):
            self.workflow.create_line({"LedgerId": 2265976208, "FiscalDateDays": 20544})
        self.assertEqual(self.finance.events, [])

    def test_convenience_missing_year_does_not_write_line(self) -> None:
        with self.assertRaises(FiscalPeriodNotFoundError):
            self.workflow.create_lines_convenience({"date": "2027-01-01", "amount": 100}, ledger_id=2265976208)
        self.assertEqual(self.finance.events, [])

    def test_convenience_explicit_voucher_number_is_preserved(self) -> None:
        result = self.workflow.create_lines_convenience(
            [{"date": "2026-01-01", "amount": 100}, {"date": "2026-01-02", "amount": 100}],
            ledger_id=2265976208, voucher_number=12345,
        )
        self.assertEqual([row["Updated"]["VoucherNumber"] for row in result["Lines"]], [12345, 12345])

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

    def test_create_lines_convenience_partnerpayment_allows_settled_posts(self) -> None:
        self.workflow.set_ledger_by_name("Bank2Xena")
        result = self.workflow.create_lines_convenience(
            {
                "date": "2026-04-13",
                "type": "partnerpayment",
                "amount": 1859.38,
                "partner_number": 20001,
                "account": 1920,
                "settled_partner_post_ids": [2937818664],
                "partial_settle_id": 2937818664,
                "description": "Partnerbetaling: 20001",
            }
        )

        self.assertEqual(result["LineCount"], 1)
        line = result["Lines"][0]["Updated"]
        self.assertEqual(line["SettledPartnerPosts"], [{"Id": 2937818664}])
        self.assertEqual(line["PartiallySettledPostId"], 2937818664)

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
