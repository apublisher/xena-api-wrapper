from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast


class ArticleGroupError(ValueError):
    """Base error for article group workflow operations."""


class ArticleGroupNotFoundError(ArticleGroupError):
    """Raised when no article group can be matched."""


class ArticleGroupAmbiguousError(ArticleGroupError):
    """Raised when more than one article group matches."""


@dataclass
class ArticleGroupWorkflow:
    """Workflow helper for article group list and CRUD operations."""

    _client: Any
    _fiscal_id: str

    def get_all(
        self,
        *,
        query_string: str | None = None,
        force_no_paging: bool = False,
        show_deactivated: bool = False,
        page: int = 0,
        page_size: int = 30,
    ) -> Any:
        base_kwargs: dict[str, Any] = {
            "fiscal_id": self._fiscal_id,
            "list_options_show_deactivated": show_deactivated,
            "list_options_page": page,
            "list_options_page_size": page_size,
            "list_options_force_no_paging": force_no_paging,
        }

        if query_string is None:
            return self._call_api(
                ["api_article_group__get_get__api__fiscal_fiscal_id__article_group"],
                **base_kwargs,
            )

        try:
            return self._call_api(
                ["api_article_group__get_get__api__fiscal_fiscal_id__article_group"],
                querystring=query_string,
                **base_kwargs,
            )
        except TypeError:
            return self._call_api(
                ["api_article_group__get_get__api__fiscal_fiscal_id__article_group"],
                query_string=query_string,
                **base_kwargs,
            )

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

        raise ArticleGroupError("Unexpected ArticleGroup response shape: could not read Entities list")

    def get_by_id(self, article_group_id: int) -> Any:
        return self._call_api(
            ["api_article_group__get_get__api__fiscal_fiscal_id__article_group_id"],
            id=article_group_id,
            fiscal_id=self._fiscal_id,
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

    def get_id_by_description(self, description: str, *, show_deactivated: bool = False) -> int:
        group = self.get_by_description(description, show_deactivated=show_deactivated)
        group_id = group.get("Id")
        if not isinstance(group_id, int):
            raise ArticleGroupError("ArticleGroup response missing integer Id field")
        return group_id

    def create(self, dto: dict[str, Any]) -> Any:
        method_candidates = ["api_article_group__post_post__api__fiscal_fiscal_id__article_group"]
        try:
            return self._call_api(
                method_candidates,
                article_group=dto,
                fiscal_id=self._fiscal_id,
            )
        except TypeError:
            return self._call_api(
                method_candidates,
                dto=dto,
                fiscal_id=self._fiscal_id,
            )

    def update(self, article_group_id: int, dto: dict[str, Any]) -> Any:
        method_candidates = ["api_article_group__put_put__api__fiscal_fiscal_id__article_group_id"]
        try:
            return self._call_api(
                method_candidates,
                article_group=dto,
                fiscal_id=self._fiscal_id,
                id=str(article_group_id),
            )
        except TypeError:
            return self._call_api(
                method_candidates,
                dto=dto,
                fiscal_id=self._fiscal_id,
                id=str(article_group_id),
            )

    def delete(self, article_group_id: int) -> Any:
        return self._call_api(
            ["api_article_group__delete_delete__api__fiscal_fiscal_id__article_group_id"],
            fiscal_id=self._fiscal_id,
            id=article_group_id,
        )

    def _call_api(self, method_candidates: list[str], **kwargs: Any) -> Any:
        namespaces = [
            getattr(self._client, "finance", None),
            getattr(self._client, "article", None),
        ]

        for namespace in namespaces:
            if namespace is None:
                continue
            for method_name in method_candidates:
                method = getattr(namespace, method_name, None)
                if callable(method):
                    return method(**kwargs)

        names = ", ".join(method_candidates)
        raise ArticleGroupError(f"Could not find generated client method. Tried: {names}")

    @staticmethod
    def _single_match(matches: list[dict[str, Any]], label: str) -> dict[str, Any]:
        if not matches:
            raise ArticleGroupNotFoundError(f"No article group found for {label}")
        if len(matches) > 1:
            raise ArticleGroupAmbiguousError(f"More than one article group matched {label}")
        return matches[0]
