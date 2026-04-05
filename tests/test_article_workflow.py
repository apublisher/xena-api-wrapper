from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import Any

from xena_api_wrappers.workflows.article.article import (
    ArticleAmbiguousError,
    ArticleError,
    ArticleNotFoundError,
    ArticleWorkflow,
)


class _FakeArticleApi:
    def __init__(self) -> None:
        self.last_list_kwargs: dict[str, Any] | None = None
        self.last_search_kwargs: dict[str, Any] | None = None
        self.last_exists_number: str | None = None
        self.last_create_payload: dict[str, Any] | None = None
        self.last_update_payload: dict[str, Any] | None = None
        self.last_update_id: str | None = None
        self.last_delete_id: int | None = None

    def api_article__get_get__api__fiscal_fiscal_id__article(
        self,
        fiscal_id: str,
        excluded_id: int | None = None,
        query_string: str | None = None,
        include_defaults: bool | None = None,
        required_has_inventory_management: bool | None = None,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        self.last_list_kwargs = {
            "fiscal_id": fiscal_id,
            "excluded_id": excluded_id,
            "query_string": query_string,
            "include_defaults": include_defaults,
            "required_has_inventory_management": required_has_inventory_management,
            "show_deactivated": list_options_show_deactivated,
            "page": list_options_page,
            "page_size": list_options_page_size,
            "force_no_paging": list_options_force_no_paging,
        }
        return {
            "Count": 2,
            "Entities": [
                {"Id": 3038211807, "ArticleNumber": "2500", "Description": "Slettes - api-test"},
                {"Id": 3038211808, "ArticleNumber": "2501", "Description": "Service"},
            ],
        }

    def api_article__get_get__api__fiscal_fiscal_id__article_id(self, id: int, fiscal_id: str, **kwargs: Any) -> dict[str, Any]:
        _ = kwargs
        return {"Id": id, "FiscalId": fiscal_id, "ArticleNumber": "2500", "Description": "One"}

    def api_article__get_by_number_get__api__fiscal_fiscal_id__article__by_number(
        self,
        article_number: str,
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        return {"Id": 3038211807, "ArticleNumber": article_number, "Description": "One"}

    def api_article__get_exists_get__api__fiscal_fiscal_id__article__exists(
        self,
        article_number: str,
        fiscal_id: str,
        **kwargs: Any,
    ) -> bool:
        _ = (fiscal_id, kwargs)
        self.last_exists_number = article_number
        return article_number == "2500"

    def api_article__get_search_get__api__fiscal_fiscal_id__article__search(
        self,
        fiscal_id: str,
        list_options_show_deactivated: bool | None = None,
        list_options_page: int | None = None,
        list_options_page_size: int | None = None,
        list_options_force_no_paging: bool | None = None,
        filter_article_number: str | None = None,
        filter_description: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = kwargs
        self.last_search_kwargs = {
            "fiscal_id": fiscal_id,
            "show_deactivated": list_options_show_deactivated,
            "page": list_options_page,
            "page_size": list_options_page_size,
            "force_no_paging": list_options_force_no_paging,
            "filter_article_number": filter_article_number,
            "filter_description": filter_description,
        }
        return {
            "Count": 1,
            "Entities": [
                {"Id": 3038211807, "ArticleNumber": filter_article_number or "2500", "Description": filter_description or "One"}
            ],
        }

    def api_article__post_post__api__fiscal_fiscal_id__article(
        self,
        article: dict[str, Any],
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_create_payload = dict(article)
        return {"Id": 3038232000, **article}

    def api_article__put_put__api__fiscal_fiscal_id__article_id(
        self,
        article: dict[str, Any],
        fiscal_id: str,
        id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_update_payload = dict(article)
        self.last_update_id = id
        return {"Id": int(id), **article}

    def api_article__delete_delete__api__fiscal_fiscal_id__article_id(
        self,
        id: int,
        fiscal_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        _ = (fiscal_id, kwargs)
        self.last_delete_id = id
        return {"Deleted": id, "Success": True}


class ArticleWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = _FakeArticleApi()
        self.workflow = ArticleWorkflow(SimpleNamespace(article=self.api), "104779")

    def test_get_all_and_get_entities(self) -> None:
        payload = self.workflow.get_all(query_string="", page_size=30)
        self.assertEqual(payload["Count"], 2)
        entities = self.workflow.get_entities()
        self.assertEqual(len(entities), 2)
        self.assertEqual(entities[0]["ArticleNumber"], "2500")

    def test_get_by_id(self) -> None:
        one = self.workflow.get_by_id(3038211807)
        self.assertEqual(one["Id"], 3038211807)

    def test_get_by_number_and_id_by_number(self) -> None:
        one = self.workflow.get_by_number("2500")
        self.assertEqual(one["ArticleNumber"], "2500")
        article_id = self.workflow.get_id_by_number("2500")
        self.assertEqual(article_id, 3038211807)

    def test_exists_by_number(self) -> None:
        self.assertTrue(self.workflow.exists_by_number("2500"))
        self.assertFalse(self.workflow.exists_by_number("does-not-exist"))

    def test_search_maps_filters(self) -> None:
        result = self.workflow.search(article_number="2500", description="Slettes", page=0, page_size=3)
        self.assertEqual(result["Count"], 1)
        assert self.api.last_search_kwargs is not None
        self.assertEqual(self.api.last_search_kwargs["filter_article_number"], "2500")
        self.assertEqual(self.api.last_search_kwargs["filter_description"], "Slettes")

    def test_create_update_delete(self) -> None:
        created = self.workflow.create({"ArticleNumber": "2500", "Description": "Slettes - api-test", "Version": 0})
        self.assertEqual(created["Id"], 3038232000)
        assert self.api.last_create_payload is not None
        self.assertEqual(self.api.last_create_payload["ArticleNumber"], "2500")

        updated = self.workflow.update(3038232000, {"ArticleNumber": "2500", "Description": "Edited", "Version": 1})
        self.assertEqual(updated["Id"], 3038232000)
        self.assertEqual(self.api.last_update_id, "3038232000")

        deleted = self.workflow.delete(3038232000)
        self.assertTrue(deleted["Success"])
        self.assertEqual(self.api.last_delete_id, 3038232000)

    def test_get_by_description_and_failures(self) -> None:
        one = self.workflow.get_by_description("Service")
        self.assertEqual(one["ArticleNumber"], "2501")

        with self.assertRaises(ArticleNotFoundError):
            self.workflow.get_by_description("not-here")

        original = self.api.api_article__get_get__api__fiscal_fiscal_id__article

        def dupes(**kwargs: Any) -> dict[str, Any]:
            _ = kwargs
            return {
                "Count": 2,
                "Entities": [
                    {"Id": 1, "Description": "Same", "ArticleNumber": "1"},
                    {"Id": 2, "Description": "Same", "ArticleNumber": "2"},
                ],
            }

        self.api.api_article__get_get__api__fiscal_fiscal_id__article = dupes  # type: ignore[method-assign]
        with self.assertRaises(ArticleAmbiguousError):
            self.workflow.get_by_description("Same")
        self.api.api_article__get_get__api__fiscal_fiscal_id__article = original  # type: ignore[method-assign]

    def test_missing_generated_method_raises(self) -> None:
        workflow = ArticleWorkflow(SimpleNamespace(article=SimpleNamespace()), "104779")
        with self.assertRaises(ArticleError):
            workflow.get_all()


if __name__ == "__main__":
    unittest.main()
