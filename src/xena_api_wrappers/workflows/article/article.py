from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast


class ArticleError(ValueError):
    """Base error for article workflow operations."""


class ArticleNotFoundError(ArticleError):
    """Raised when no article can be matched."""


class ArticleAmbiguousError(ArticleError):
    """Raised when more than one article matches."""


@dataclass
class ArticleWorkflow:
    """Workflow helper for article list, read, and CRUD operations."""

    _client: Any
    _fiscal_id: str

    def get_all(
        self,
        *,
        query_string: str | None = None,
        include_defaults: bool | None = None,
        required_has_inventory_management: bool | None = None,
        excluded_id: int | None = None,
        force_no_paging: bool = False,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 30,
    ) -> Any:
        method_candidates = ["api_article__get_get__api__fiscal_fiscal_id__article"]
        base_kwargs: dict[str, Any] = {
            "fiscal_id": self._fiscal_id,
            "excluded_id": excluded_id,
            "include_defaults": include_defaults,
            "required_has_inventory_management": required_has_inventory_management,
            "list_options_show_deactivated": show_deactivated,
            "list_options_page": page,
            "list_options_page_size": page_size,
            "list_options_force_no_paging": force_no_paging,
        }

        if query_string is None:
            return self._call_api(method_candidates, **base_kwargs)

        try:
            return self._call_api(method_candidates, query_string=query_string, **base_kwargs)
        except TypeError:
            return self._call_api(method_candidates, querystring=query_string, **base_kwargs)

    def get_entities(self, **kwargs: Any) -> list[dict[str, Any]]:
        raw: Any = self.get_all(**kwargs)

        if isinstance(raw, dict):
            raw_dict = cast(dict[str, Any], raw)
            entities_obj = raw_dict.get("Entities")
            if isinstance(entities_obj, list):
                entities = cast(list[Any], entities_obj)
                return [cast(dict[str, Any], item) for item in entities if isinstance(item, dict)]

        to_dict = getattr(cast(object, raw), "to_dict", None)
        if callable(to_dict):
            converted = to_dict()
            if isinstance(converted, dict):
                converted_dict = cast(dict[str, Any], converted)
                entities_obj = converted_dict.get("Entities")
                if isinstance(entities_obj, list):
                    entities = cast(list[Any], entities_obj)
                    return [cast(dict[str, Any], item) for item in entities if isinstance(item, dict)]

        raise ArticleError("Unexpected Article response shape: could not read Entities list")

    def get_by_id(self, article_id: int) -> Any:
        return self._call_api(
            ["api_article__get_get__api__fiscal_fiscal_id__article_id"],
            id=article_id,
            fiscal_id=self._fiscal_id,
        )

    def get_by_number(self, article_number: str) -> Any:
        return self._call_api(
            ["api_article__get_by_number_get__api__fiscal_fiscal_id__article__by_number"],
            article_number=article_number,
            fiscal_id=self._fiscal_id,
        )

    def exists_by_number(self, article_number: str) -> Any:
        return self._call_api(
            ["api_article__get_exists_get__api__fiscal_fiscal_id__article__exists"],
            article_number=article_number,
            fiscal_id=self._fiscal_id,
        )

    def search(
        self,
        *,
        article_number: str | None = None,
        description: str | None = None,
        force_no_paging: bool = False,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 30,
    ) -> Any:
        return self._call_api(
            ["api_article__get_search_get__api__fiscal_fiscal_id__article__search"],
            fiscal_id=self._fiscal_id,
            list_options_show_deactivated=show_deactivated,
            list_options_page=page,
            list_options_page_size=page_size,
            list_options_force_no_paging=force_no_paging,
            filter_article_number=article_number,
            filter_description=description,
        )

    def get_by_description(self, description: str, *, show_deactivated: bool = False) -> dict[str, Any]:
        matches = [
            entity
            for entity in self.get_entities(
                force_no_paging=True,
                show_deactivated=show_deactivated,
                page=0,
                page_size=100,
            )
            if entity.get("Description") == description
        ]
        return self._single_match(matches, f"description '{description}'")

    def get_id_by_number(self, article_number: str) -> int:
        raw = self.get_by_number(article_number)
        article = self._as_dict(raw)
        article_id = article.get("Id")
        if not isinstance(article_id, int):
            raise ArticleError("Article response missing integer Id field")
        return article_id

    def create(self, article: dict[str, Any]) -> Any:
        method_candidates = ["api_article__post_post__api__fiscal_fiscal_id__article"]
        try:
            return self._call_api(
                method_candidates,
                article=article,
                fiscal_id=self._fiscal_id,
            )
        except TypeError:
            return self._call_api(
                method_candidates,
                dto=article,
                fiscal_id=self._fiscal_id,
            )

    def update(self, article_id: int, article: dict[str, Any]) -> Any:
        method_candidates = ["api_article__put_put__api__fiscal_fiscal_id__article_id"]
        try:
            return self._call_api(
                method_candidates,
                article=article,
                fiscal_id=self._fiscal_id,
                id=str(article_id),
            )
        except TypeError:
            return self._call_api(
                method_candidates,
                dto=article,
                fiscal_id=self._fiscal_id,
                id=str(article_id),
            )

    def delete(self, article_id: int) -> Any:
        return self._call_api(
            ["api_article__delete_delete__api__fiscal_fiscal_id__article_id"],
            id=article_id,
            fiscal_id=self._fiscal_id,
        )

    def _call_api(self, method_candidates: list[str], **kwargs: Any) -> Any:
        namespaces = [
            getattr(self._client, "article", None),
            getattr(self._client, "finance", None),
        ]

        for namespace in namespaces:
            if namespace is None:
                continue
            for method_name in method_candidates:
                method = getattr(namespace, method_name, None)
                if callable(method):
                    return method(**kwargs)

        names = ", ".join(method_candidates)
        raise ArticleError(f"Could not find generated client method. Tried: {names}")

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return cast(dict[str, Any], value)
        to_dict = getattr(cast(object, value), "to_dict", None)
        if callable(to_dict):
            converted = to_dict()
            if isinstance(converted, dict):
                return cast(dict[str, Any], converted)
        raise ArticleError(f"Unexpected Article response shape: expected dict-like payload, got {type(value)!r}")

    @staticmethod
    def _single_match(matches: list[dict[str, Any]], label: str) -> dict[str, Any]:
        if not matches:
            raise ArticleNotFoundError(f"No article found for {label}")
        if len(matches) > 1:
            raise ArticleAmbiguousError(f"More than one article matched {label}")
        return matches[0]
