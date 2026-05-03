"""Brave Search API helper.

The default helper resolves the Brave API key from the trading-manager registry
config id and local secret alias. Secret values are never stored in repo files.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from trading_registry import SecretResolver, create_csv_registry_query

BRAVE_SEARCH_CONFIG_ID = "cfg_BRAVESEARCH"
DEFAULT_REGISTRY_CSV = Path("/root/projects/trading-manager/scripts/registry/current.csv")
DEFAULT_SECRETS_REGISTRY = Path("/root/secrets/registry.json")
DEFAULT_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
DEFAULT_TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class SearchResult:
    """Normalized Brave web search result."""

    title: str
    url: str
    description: str | None = None
    site_name: str | None = None
    published: str | None = None


class BraveSearchError(RuntimeError):
    """Raised when Brave Search request or response handling fails."""


def _load_default_api_key(
    *,
    config_id: str = BRAVE_SEARCH_CONFIG_ID,
    registry_csv: Path = DEFAULT_REGISTRY_CSV,
    secrets_registry: Path = DEFAULT_SECRETS_REGISTRY,
) -> str:
    resolver = SecretResolver(
        create_csv_registry_query(registry_csv),
        registry_path=str(secrets_registry),
    )
    return resolver.load_secret_text_by_config_id(config_id, "api_key")


def _normalize_web_results(payload: Mapping[str, Any]) -> list[SearchResult]:
    web = payload.get("web")
    results = web.get("results", []) if isinstance(web, Mapping) else []
    normalized: list[SearchResult] = []
    for item in results:
        if not isinstance(item, Mapping):
            continue
        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or "").strip()
        if not title or not url:
            continue
        normalized.append(
            SearchResult(
                title=title,
                url=url,
                description=str(item["description"]).strip() if item.get("description") is not None else None,
                site_name=str(item["site_name"]).strip() if item.get("site_name") is not None else None,
                published=str(item["published"]).strip() if item.get("published") is not None else None,
            )
        )
    return normalized


class BraveSearchClient:
    """Small urllib-based Brave Search API client."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = (api_key or _load_default_api_key()).strip()
        if not self.api_key:
            raise BraveSearchError("Brave Search API key is empty")
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    def search(
        self,
        query: str,
        *,
        count: int = 10,
        country: str = "US",
        search_lang: str | None = None,
        ui_lang: str | None = None,
        freshness: str | None = None,
        extra_params: Mapping[str, str] | None = None,
    ) -> list[SearchResult]:
        q = query.strip()
        if not q:
            raise ValueError("query must be non-empty")
        if count < 1 or count > 20:
            raise ValueError("count must be between 1 and 20")

        params: dict[str, str] = {
            "q": q,
            "count": str(count),
            "country": country,
        }
        if search_lang:
            params["search_lang"] = search_lang
        if ui_lang:
            params["ui_lang"] = ui_lang
        if freshness:
            params["freshness"] = freshness
        if extra_params:
            params.update({str(key): str(value) for key, value in extra_params.items()})

        url = self.endpoint + "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key,
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise BraveSearchError(f"Brave Search HTTP {error.code}: {error.reason}") from error
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            raise BraveSearchError(f"Brave Search request failed: {error}") from error
        if not isinstance(payload, Mapping):
            raise BraveSearchError("Brave Search response was not a JSON object")
        return _normalize_web_results(payload)


def brave_search(query: str, **kwargs: Any) -> list[SearchResult]:
    """Run a Brave web search using the default local secret-backed client."""
    return BraveSearchClient().search(query, **kwargs)
