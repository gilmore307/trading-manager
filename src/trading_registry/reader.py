"""Id-based trading registry reader helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

SELECT_COLUMNS = """
SELECT
  id,
  kind,
  key,
  payload_format,
  payload,
  path,
  applies_to,
  artifact_sync_policy,
  note,
  created_at,
  updated_at
FROM trading_registry
"""

QueryResult = Any
QueryFn = Callable[[str, Sequence[str]], QueryResult]


@dataclass(frozen=True)
class RegistryItem:
    """Mapped ``trading_registry`` row."""

    id: str
    kind: str
    key: str
    payload_format: str
    payload: str
    path: str | None
    applies_to: str | None
    artifact_sync_policy: str | None
    note: str | None
    created_at: Any
    updated_at: Any


def _non_empty_string(label: str, value: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise TypeError(f"{label} must be a non-empty string")
    return value


def _optional_non_empty(value: Any) -> str | None:
    if isinstance(value, str) and value.strip() != "":
        return value
    return None


def map_registry_item_row(row: Mapping[str, Any]) -> RegistryItem:
    """Map a snake_case database row into a ``RegistryItem``."""
    if not isinstance(row, Mapping):
        raise TypeError("Cannot map trading_registry row: expected a mapping row")

    return RegistryItem(
        id=row["id"],
        kind=row["kind"],
        key=row["key"],
        payload_format=row["payload_format"],
        payload=row["payload"],
        path=_optional_non_empty(row.get("path")),
        applies_to=_optional_non_empty(row.get("applies_to")),
        artifact_sync_policy=_optional_non_empty(row.get("artifact_sync_policy")),
        note=row.get("note"),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


def _normalize_query_result(result: QueryResult) -> list[Mapping[str, Any]]:
    if isinstance(result, list):
        return result

    if isinstance(result, tuple):
        return list(result)

    rows = getattr(result, "rows", None)
    if isinstance(rows, list):
        return rows

    if isinstance(result, Mapping) and isinstance(result.get("rows"), list):
        return result["rows"]

    raise TypeError(
        "Invalid registry query result: expected a list of rows or an object/mapping with a rows list"
    )


class RegistryReader:
    """Read registry values by stable registry id."""

    def __init__(self, query: QueryFn):
        if not callable(query):
            raise TypeError("RegistryReader requires a callable query function")
        self._query = query

    def _fetch_one(self, sql: str, params: Sequence[str]) -> RegistryItem | None:
        rows = _normalize_query_result(self._query(sql, params))
        return map_registry_item_row(rows[0]) if rows else None

    def _fetch_many(self, sql: str, params: Sequence[str]) -> list[RegistryItem]:
        return [map_registry_item_row(row) for row in _normalize_query_result(self._query(sql, params))]

    def get_item_by_id(self, item_id: str) -> RegistryItem | None:
        return self._fetch_one(f"{SELECT_COLUMNS} WHERE id = %s", [_non_empty_string("id", item_id)])

    def require_item_by_id(self, item_id: str) -> RegistryItem:
        item = self.get_item_by_id(item_id)
        if item is None:
            raise KeyError(f"Registry item not found for id: {item_id}")
        return item

    def get_key_by_id(self, item_id: str) -> str | None:
        item = self.get_item_by_id(item_id)
        return item.key if item else None

    def get_payload_by_id(self, item_id: str) -> str | None:
        item = self.get_item_by_id(item_id)
        return item.payload if item else None

    def get_path_by_id(self, item_id: str) -> str | None:
        item = self.get_item_by_id(item_id)
        return item.path if item else None

    def list_items_by_kind(self, kind: str) -> list[RegistryItem]:
        return self._fetch_many(
            f"{SELECT_COLUMNS} WHERE kind = %s ORDER BY key ASC",
            [_non_empty_string("kind", kind)],
        )


def create_registry_reader(query: QueryFn) -> RegistryReader:
    """Create a ``RegistryReader`` from a query callable."""
    return RegistryReader(query)


def create_csv_registry_query(registry_csv: str | Path) -> QueryFn:
    """Create a tiny id/kind query function backed by ``scripts/current.csv``.

    This is for helper scripts that need registry ids before a database
    connection is available. It intentionally supports only the query shapes
    used by ``RegistryReader``.
    """
    path = Path(registry_csv)

    def query(sql: str, params: Sequence[str]) -> list[Mapping[str, Any]]:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if "WHERE id = %s" in sql:
            wanted = params[0]
            return [row for row in rows if row.get("id") == wanted]
        if "WHERE kind = %s" in sql:
            wanted = params[0]
            return sorted((row for row in rows if row.get("kind") == wanted), key=lambda row: row.get("key", ""))
        raise ValueError("CSV registry query only supports WHERE id = %s or WHERE kind = %s")

    return query
