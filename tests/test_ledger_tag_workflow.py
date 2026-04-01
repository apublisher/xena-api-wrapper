from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.utils.ledger_tag import (
    LedgerTagAmbiguousError,
    LedgerTagNotFoundError,
    LedgerTagWorkflow,
)


class _FakeFinance:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

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
        _ = kwargs
        _ = ledger_account
        _ = query_string
        _ = include_defaults
        _ = list_options_show_deactivated
        _ = list_options_page
        _ = list_options_page_size
        _ = list_options_force_no_paging
        self.calls.append({"fiscal_id": fiscal_id})
        return {
            "Count": 3,
            "Entities": [
                {"Id": 1, "Number": 1920, "Description": "Bank"},
                {"Id": 2, "TagNumber": "3000", "Description": "Revenue"},
                {"Id": 3, "LedgerTagNumber": 2700, "Description": "MVA"},
            ],
        }

    def api_ledger_tag__get_get__api__fiscal_fiscal_id__ledger_tag_id(
        self, id: int, fiscal_id: str, **kwargs: Any
    ) -> dict[str, Any]:
        _ = kwargs
        _ = fiscal_id
        return {"Id": id, "Number": 1920}

    def api_ledger_tag__get_settlement_tag_get__api__fiscal_fiscal_id__ledger_tag__settlement_tag(
        self,
        fiscal_id: str,
        include_default: bool | None = None,
        query_string: str | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        _ = (
            fiscal_id,
            include_default,
            query_string,
            list_options_show_deactivated,
            list_options_page,
            list_options_page_size,
            list_options_force_no_paging,
        )
        return {"Count": 1, "Entities": [{"Id": 99, "Number": 7760}]}


class LedgerTagWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_finance = _FakeFinance()
        client = SimpleNamespace(finance=self.fake_finance)
        self.workflow = LedgerTagWorkflow(client, "104779")

    def test_get_entities(self) -> None:
        entities = self.workflow.get_entities()
        self.assertEqual(len(entities), 3)

    def test_get_by_number_int(self) -> None:
        row = self.workflow.get_by_number(1920)
        self.assertEqual(row["Id"], 1)

    def test_get_by_number_string(self) -> None:
        row = self.workflow.get_by_number("3000")
        self.assertEqual(row["Id"], 2)

    def test_get_id_by_number(self) -> None:
        tag_id = self.workflow.get_id_by_number(2700)
        self.assertEqual(tag_id, 3)

    def test_get_by_id(self) -> None:
        row = self.workflow.get_by_id(1)
        self.assertEqual(row["Id"], 1)

    def test_get_settlement_tags(self) -> None:
        payload = self.workflow.get_settlement_tags(force_no_paging=True)
        self.assertEqual(payload["Count"], 1)

    def test_get_by_number_not_found(self) -> None:
        with self.assertRaises(LedgerTagNotFoundError):
            self.workflow.get_by_number(9999)

    def test_get_by_number_ambiguous(self) -> None:
        original = self.fake_finance.api_ledger_tag__get_get__api__fiscal_fiscal_id__ledger_tag

        def _dup(*args: Any, **kwargs: Any) -> dict[str, Any]:
            data = original(*args, **kwargs)
            data["Entities"].append({"Id": 999, "Number": 1920})
            return data

        self.fake_finance.api_ledger_tag__get_get__api__fiscal_fiscal_id__ledger_tag = _dup  # type: ignore[method-assign]

        with self.assertRaises(LedgerTagAmbiguousError):
            self.workflow.get_by_number(1920)


if __name__ == "__main__":
    unittest.main()
