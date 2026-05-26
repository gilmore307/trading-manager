"""Registry-id value helpers for manager scripts.

Scripts should depend on stable ``trading_registry.id`` values and resolve the
mutable payload/key text from the generated registry snapshot.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from trading_registry import create_csv_registry_query, create_registry_reader

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_CSV = REPO_ROOT / "scripts" / "registry" / "current.csv"
RegistryField = Literal["key", "payload", "path"]


@lru_cache(maxsize=4)
def _reader(registry_csv: str):
    query = create_csv_registry_query(registry_csv)
    return create_registry_reader(query)


def registry_item(item_id: str, *, registry_csv: Path = DEFAULT_REGISTRY_CSV):
    """Return a registry item by stable id from the local CSV snapshot."""
    return _reader(str(registry_csv)).require_item_by_id(item_id)


def registry_value(item_id: str, field: RegistryField = "payload", *, registry_csv: Path = DEFAULT_REGISTRY_CSV) -> str:
    """Return a selected registry field by stable id."""
    item = registry_item(item_id, registry_csv=registry_csv)
    value = getattr(item, field)
    if value is None:
        raise KeyError(f"Registry item {item_id} has no {field}")
    return value


def registry_payload(item_id: str, *, registry_csv: Path = DEFAULT_REGISTRY_CSV) -> str:
    """Return the registry payload for a stable id."""
    return registry_value(item_id, "payload", registry_csv=registry_csv)


def registry_payloads(item_ids: tuple[str, ...], *, registry_csv: Path = DEFAULT_REGISTRY_CSV) -> tuple[str, ...]:
    """Return registry payloads in the same order as stable ids."""
    return tuple(registry_payload(item_id, registry_csv=registry_csv) for item_id in item_ids)
