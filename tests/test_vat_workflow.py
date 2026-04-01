from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.utils.vat import (
    VatAmbiguousError,
    VatNotFoundError,
    VatWorkflow,
)


class _FakeFinance:
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
        _ = kwargs
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
        )
        return {
            "Count": 3,
            "Entities": [
                {"Id": 1, "Abbreviation": "0", "Description": "Ingen", "VatType": "VatType_Purchasing"},
                {"Id": 2, "Abbreviation": "1", "Description": "Fradrag 25", "VatType": "VatType_Purchasing"},
                {"Id": 3, "Abbreviation": "3", "Description": "Utgaaende 25", "VatType": "VatType_Sales"},
            ],
        }

    def api_vat__get_get__api__fiscal_fiscal_id__vat_id(
        self, id: int, fiscal_id: str, **kwargs: Any
    ) -> dict[str, Any]:
        _ = kwargs
        _ = fiscal_id
        return {"Id": id, "Abbreviation": "1"}

    def api_vat__get_vat_type_get__api__fiscal_fiscal_id__vat__vat_type(
        self,
        fiscal_id: str,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        _ = (
            fiscal_id,
            list_options_show_deactivated,
            list_options_page,
            list_options_page_size,
            list_options_force_no_paging,
        )
        return {
            "Count": 2,
            "Entities": [
                {"Value": "VatType_Sales", "Text": "Salgsmoms"},
                {"Value": "VatType_Purchasing", "Text": "Kjopsmoms"},
            ],
        }

    def api_vat__get_by_type_get__api__fiscal_fiscal_id__vat__by_type(
        self,
        fiscal_id: str,
        query_string: str | None = None,
        vat_type: str | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        _ = (
            fiscal_id,
            query_string,
            list_options_show_deactivated,
            list_options_page,
            list_options_page_size,
            list_options_force_no_paging,
        )
        entities: list[dict[str, Any]]
        if vat_type == "VatType_Purchasing":
            entities = [
                {"Id": 1, "Abbreviation": "0", "VatType": "VatType_Purchasing"},
                {"Id": 2, "Abbreviation": "1", "VatType": "VatType_Purchasing"},
            ]
        else:
            entities = [{"Id": 3, "Abbreviation": "3", "VatType": "VatType_Sales"}]
        return {"Count": len(entities), "Entities": entities}


class VatWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake_finance = _FakeFinance()
        client = SimpleNamespace(finance=self.fake_finance)
        self.workflow = VatWorkflow(client, "104779")

    def test_get_entities(self) -> None:
        entities = self.workflow.get_entities()
        self.assertEqual(len(entities), 3)

    def test_get_by_id(self) -> None:
        row = self.workflow.get_by_id(2)
        self.assertEqual(row["Id"], 2)

    def test_get_types(self) -> None:
        payload = self.workflow.get_types(force_no_paging=True)
        self.assertEqual(payload["Count"], 2)

    def test_get_by_type(self) -> None:
        payload = self.workflow.get_by_type("VatType_Purchasing", force_no_paging=True)
        self.assertEqual(payload["Count"], 2)

    def test_get_by_abbreviation(self) -> None:
        row = self.workflow.get_by_abbreviation("1")
        self.assertEqual(row["Id"], 2)

    def test_get_id_by_abbreviation(self) -> None:
        vat_id = self.workflow.get_id_by_abbreviation("3")
        self.assertEqual(vat_id, 3)

    def test_get_by_abbreviation_not_found(self) -> None:
        with self.assertRaises(VatNotFoundError):
            self.workflow.get_by_abbreviation("999")

    def test_get_by_abbreviation_ambiguous(self) -> None:
        original = self.fake_finance.api_vat__get_get__api__fiscal_fiscal_id__vat

        def _dup(*args: Any, **kwargs: Any) -> dict[str, Any]:
            data = original(*args, **kwargs)
            data["Entities"].append({"Id": 999, "Abbreviation": "1"})
            return data

        self.fake_finance.api_vat__get_get__api__fiscal_fiscal_id__vat = _dup  # type: ignore[method-assign]

        with self.assertRaises(VatAmbiguousError):
            self.workflow.get_by_abbreviation("1")


if __name__ == "__main__":
    unittest.main()
