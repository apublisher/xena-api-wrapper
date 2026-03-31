from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any, cast

from xena_api_wrappers.workflows.utils.fiscal_period import (
    FiscalPeriodAmbiguousError,
    FiscalPeriodNotFoundError,
    FiscalPeriodWorkflow,
)


def _sample_payload() -> dict[str, Any]:
    return {
        "Count": 4,
        "Entities": [
            {
                "FiscalPeriodStartDays": 20454,
                "FiscalPeriodEndDays": 20818,
                "Description": "2026",
                "Id": 2944485122,
            },
            {
                "FiscalPeriodStartDays": 20089,
                "FiscalPeriodEndDays": 20453,
                "Description": "2025",
                "Id": 2586516686,
            },
            {
                "FiscalPeriodStartDays": 19723,
                "FiscalPeriodEndDays": 20088,
                "Description": "2024",
                "Id": 2188936542,
            },
            {
                "FiscalPeriodStartDays": 19358,
                "FiscalPeriodEndDays": 19722,
                "Description": "2023",
                "Id": 2181157216,
            },
        ],
    }


class _FakeFinance:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def api_fiscal_period__get_get__api__fiscal_fiscal_id__fiscal_period(
        self,
        fiscal_id: str,
        list_options_force_no_paging: bool | None = None,
    ) -> dict[str, Any]:
        _ = fiscal_id
        _ = list_options_force_no_paging
        return self.payload


class FiscalPeriodWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        client = SimpleNamespace(finance=_FakeFinance(_sample_payload()))
        self.workflow = FiscalPeriodWorkflow(client, "104779")

    def test_get_all_returns_raw_payload(self) -> None:
        result = self.workflow.get_all()
        self.assertEqual(result["Count"], 4)

    def test_get_id_by_date_with_iso_string(self) -> None:
        period_id = self.workflow.get_id_by_date("2026-01-15")
        self.assertEqual(period_id, 2944485122)

    def test_get_id_by_date_with_norwegian_format(self) -> None:
        period_id = self.workflow.get_id_by_date("15.01.2025")
        self.assertEqual(period_id, 2586516686)

    def test_get_id_by_year(self) -> None:
        period_id = self.workflow.get_id_by_year("2024")
        self.assertEqual(period_id, 2188936542)

    def test_get_by_date_raises_clear_error_when_missing(self) -> None:
        with self.assertRaises(FiscalPeriodNotFoundError) as ctx:
            self.workflow.get_by_date("2030-01-01")

        self.assertIn("needs to be set up in Xena", str(ctx.exception))

    def test_get_by_year_raises_when_invalid_format(self) -> None:
        with self.assertRaises(ValueError):
            self.workflow.get_id_by_year("26")

    def test_get_by_date_raises_when_ambiguous(self) -> None:
        payload = _sample_payload()
        entities = cast(list[dict[str, Any]], payload["Entities"])
        entities.append(
            {
                "FiscalPeriodStartDays": 20400,
                "FiscalPeriodEndDays": 20500,
                "Description": "2026-overlap",
                "Id": 999,
            }
        )
        client = SimpleNamespace(finance=_FakeFinance(payload))
        workflow = FiscalPeriodWorkflow(client, "104779")

        with self.assertRaises(FiscalPeriodAmbiguousError):
            workflow.get_by_date("2026-01-20")


if __name__ == "__main__":
    unittest.main()
