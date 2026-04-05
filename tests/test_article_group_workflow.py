from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.article.article_group import (
    ArticleGroupAmbiguousError,
    ArticleGroupError,
    ArticleGroupNotFoundError,
    ArticleGroupWorkflow,
)


class _FakeFinance:
    def __init__(self) -> None:
        self.last_list_kwargs: dict[str, Any] | None = None
        self.last_create_dto: dict[str, Any] | None = None
        self.last_update_dto: dict[str, Any] | None = None
        self.last_update_id: str | None = None
        self.last_delete_id: int | None = None

    def api_article_group__get_get__api__fiscal_fiscal_id__article_group(
        self,
        fiscal_id: str,
        querystring: str | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        self.last_list_kwargs = {
            "fiscal_id": fiscal_id,
            "querystring": querystring,
            "show_deactivated": list_options_show_deactivated,
            "page": list_options_page,
            "page_size": list_options_page_size,
            "force_no_paging": list_options_force_no_paging,
        }
        return {
            "Count": 2,
            "Entities": [
                {"Id": 10, "Description": "Konsulenttjenester", "Version": 2},
                {"Id": 11, "Description": "Programvare", "Version": 1},
            ],
        }

    def api_article_group__get_get__api__fiscal_fiscal_id__article_group_id(
        self,
        id: int,
        fiscal_id: str,
    ) -> dict[str, Any]:
        return {"Id": id, "Description": "ById", "FiscalId": fiscal_id}

    def api_article_group__post_post__api__fiscal_fiscal_id__article_group(
        self,
        dto: dict[str, Any],
        fiscal_id: str,
    ) -> dict[str, Any]:
        _ = fiscal_id
        self.last_create_dto = dict(dto)
        return {"Id": 3038057174, **dto}

    def api_article_group__put_put__api__fiscal_fiscal_id__article_group_id(
        self,
        dto: dict[str, Any],
        fiscal_id: str,
        id: str,
    ) -> dict[str, Any]:
        _ = fiscal_id
        self.last_update_dto = dict(dto)
        self.last_update_id = id
        return {"Id": int(id), **dto}

    def api_article_group__delete_delete__api__fiscal_fiscal_id__article_group_id(
        self,
        fiscal_id: str,
        id: int,
    ) -> dict[str, Any]:
        _ = fiscal_id
        self.last_delete_id = id
        return {"Deleted": id}


class ArticleGroupWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.finance = _FakeFinance()
        self.workflow = ArticleGroupWorkflow(SimpleNamespace(finance=self.finance), "104779")

    def test_get_all_passes_expected_list_options(self) -> None:
        result = self.workflow.get_all(show_deactivated=False, page=0, page_size=30, force_no_paging=False)
        self.assertEqual(result["Count"], 2)
        assert self.finance.last_list_kwargs is not None
        self.assertEqual(self.finance.last_list_kwargs["fiscal_id"], "104779")
        self.assertEqual(self.finance.last_list_kwargs["page_size"], 30)

    def test_get_entities_extracts_entities(self) -> None:
        entities = self.workflow.get_entities()
        self.assertEqual(len(entities), 2)
        self.assertEqual(entities[0]["Description"], "Konsulenttjenester")

    def test_get_by_id(self) -> None:
        one = self.workflow.get_by_id(10)
        self.assertEqual(one["Id"], 10)

    def test_get_by_description_and_get_id_by_description(self) -> None:
        one = self.workflow.get_by_description("Programvare")
        self.assertEqual(one["Id"], 11)
        self.assertEqual(self.workflow.get_id_by_description("Konsulenttjenester"), 10)

    def test_get_by_description_not_found(self) -> None:
        with self.assertRaises(ArticleGroupNotFoundError):
            self.workflow.get_by_description("does-not-exist")

    def test_get_by_description_ambiguous(self) -> None:
        original = self.finance.api_article_group__get_get__api__fiscal_fiscal_id__article_group

        def dupes(**kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            return {
                "Count": 2,
                "Entities": [
                    {"Id": 1, "Description": "Same"},
                    {"Id": 2, "Description": "Same"},
                ],
            }

        self.finance.api_article_group__get_get__api__fiscal_fiscal_id__article_group = dupes  # type: ignore[method-assign]
        with self.assertRaises(ArticleGroupAmbiguousError):
            self.workflow.get_by_description("Same")
        self.finance.api_article_group__get_get__api__fiscal_fiscal_id__article_group = original  # type: ignore[method-assign]

    def test_create_update_delete(self) -> None:
        created = self.workflow.create({"Description": "Testgruppe - kan slettes", "Version": 0})
        self.assertEqual(created["Id"], 3038057174)
        assert self.finance.last_create_dto is not None
        self.assertEqual(self.finance.last_create_dto["Description"], "Testgruppe - kan slettes")

        updated = self.workflow.update(3038057174, {"Description": "Oppdatert", "Version": 1})
        self.assertEqual(updated["Id"], 3038057174)
        self.assertEqual(self.finance.last_update_id, "3038057174")

        deleted = self.workflow.delete(3038057174)
        self.assertEqual(deleted["Deleted"], 3038057174)
        self.assertEqual(self.finance.last_delete_id, 3038057174)

    def test_missing_generated_method_raises(self) -> None:
        workflow = ArticleGroupWorkflow(SimpleNamespace(finance=SimpleNamespace()), "104779")
        with self.assertRaises(ArticleGroupError):
            workflow.get_all()


if __name__ == "__main__":
    unittest.main()
