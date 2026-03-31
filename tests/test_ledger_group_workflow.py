from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.utils.ledger_group import (
    LedgerGroupAmbiguousError,
    LedgerGroupNotFoundError,
    LedgerGroupWorkflow,
)


def _sample_payload() -> dict[str, Any]:
    return {
        "Count": 3,
        "Entities": [
            {"Value": "Xena_Domain_Income_Accounts", "Text": "Resultatregnskap"},
            {"Value": "Xena_Domain_Asset_Accounts", "Text": "Eiendeler"},
            {"Value": "Xena_Domain_Liability_Accounts", "Text": "Egenkapital + Gjeld"},
        ],
    }


class _FakeFinance:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def api_ledger_tag__get_ledger_group_list_get__api__fiscal_fiscal_id__ledger_tag__ledger_group(
        self,
        fiscal_id: str,
        list_option_force_no_paging: bool | None = None,
    ) -> dict[str, Any]:
        _ = fiscal_id
        _ = list_option_force_no_paging
        return self.payload


class LedgerGroupWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        client = SimpleNamespace(finance=_FakeFinance(_sample_payload()))
        self.workflow = LedgerGroupWorkflow(client, "104779")

    def test_get_all_returns_raw_payload(self) -> None:
        result = self.workflow.get_all()
        self.assertEqual(result["Count"], 3)

    def test_get_entities_returns_value_text_pairs(self) -> None:
        entities = self.workflow.get_entities()
        self.assertEqual(len(entities), 3)
        self.assertEqual(entities[0]["Value"], "Xena_Domain_Income_Accounts")

    def test_get_by_value(self) -> None:
        result = self.workflow.get_by_value("Xena_Domain_Asset_Accounts")
        self.assertEqual(result["Text"], "Eiendeler")

    def test_get_value_by_text(self) -> None:
        value = self.workflow.get_value_by_text("Egenkapital + Gjeld")
        self.assertEqual(value, "Xena_Domain_Liability_Accounts")

    def test_get_by_value_not_found(self) -> None:
        with self.assertRaises(LedgerGroupNotFoundError):
            self.workflow.get_by_value("does-not-exist")

    def test_get_value_by_text_ambiguous(self) -> None:
        payload = _sample_payload()
        payload["Entities"].append({"Value": "Xena_Domain_Income_Accounts_2", "Text": "Resultatregnskap"})
        client = SimpleNamespace(finance=_FakeFinance(payload))
        workflow = LedgerGroupWorkflow(client, "104779")

        with self.assertRaises(LedgerGroupAmbiguousError):
            workflow.get_value_by_text("Resultatregnskap")


if __name__ == "__main__":
    unittest.main()
