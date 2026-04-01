from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.utils.list_ledgers import (
    LedgerAmbiguousError,
    LedgerListWorkflow,
    LedgerNotFoundError,
)


def _sample_payload() -> dict[str, Any]:
    return {
        "Count": 2,
        "Entities": [
            {
                "Id": 2265976208,
                "Description": "Bank2Xena",
                "FiscalPeriodId": 2944485122,
                "IsBookkeeping": False,
            },
            {
                "Id": 2181157620,
                "Description": "Finans",
                "FiscalPeriodId": 2944485122,
                "IsBookkeeping": False,
            },
        ],
    }


class _FakeFinance:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

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
        return self.payload


class LedgerListWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        client = SimpleNamespace(finance=_FakeFinance(_sample_payload()))
        self.workflow = LedgerListWorkflow(client, "104779")

    def test_get_all_returns_raw_payload(self) -> None:
        result = self.workflow.get_all()
        self.assertEqual(result["Count"], 2)

    def test_get_entities_returns_ledgers(self) -> None:
        entities = self.workflow.get_entities()
        self.assertEqual(len(entities), 2)
        self.assertEqual(entities[0]["Description"], "Bank2Xena")

    def test_get_by_description_is_case_insensitive(self) -> None:
        row = self.workflow.get_by_description("bank2xena")
        self.assertEqual(row["Id"], 2265976208)

    def test_get_id_by_description(self) -> None:
        ledger_id = self.workflow.get_id_by_description("Finans")
        self.assertEqual(ledger_id, 2181157620)

    def test_get_by_id_accepts_string(self) -> None:
        row = self.workflow.get_by_id("2181157620")
        self.assertEqual(row["Description"], "Finans")

    def test_get_by_description_not_found(self) -> None:
        with self.assertRaises(LedgerNotFoundError):
            self.workflow.get_by_description("Missing")

    def test_get_by_description_ambiguous(self) -> None:
        payload = _sample_payload()
        payload["Entities"].append(
            {
                "Id": 999,
                "Description": "Bank2Xena",
            }
        )
        client = SimpleNamespace(finance=_FakeFinance(payload))
        workflow = LedgerListWorkflow(client, "104779")

        with self.assertRaises(LedgerAmbiguousError):
            workflow.get_by_description("Bank2Xena")


if __name__ == "__main__":
    unittest.main()
