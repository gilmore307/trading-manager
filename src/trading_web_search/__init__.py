"""Shared code-level web search helpers."""

from .brave import BRAVE_SEARCH_CONFIG_ID, BraveSearchClient, SearchResult, brave_search

__all__ = [
    "BRAVE_SEARCH_CONFIG_ID",
    "BraveSearchClient",
    "SearchResult",
    "brave_search",
]
