"""Secret-alias helpers backed by registry config ids."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .reader import QueryFn, RegistryReader

ReadTextFn = Callable[[str], str]


def _non_empty_string(label: str, value: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise TypeError(f"{label} must be a non-empty string")
    return value.strip()


def parse_registry(json_text: str, registry_path: str) -> Mapping[str, Any]:
    """Parse the local secrets registry JSON object."""
    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError as error:
        raise ValueError(f"Secrets registry at {registry_path} is not valid JSON: {error.msg}") from error

    if not isinstance(parsed, Mapping):
        raise ValueError(f"Secrets registry at {registry_path} must be a JSON object")

    return parsed


def get_secret_entry_from_registry(
    registry: Mapping[str, Any], alias: str, registry_path: str
) -> dict[str, str | None]:
    """Resolve a slash-delimited secret alias from the local secrets registry."""
    normalized_alias = _non_empty_string("alias", alias)
    segments = [segment for segment in normalized_alias.split("/") if segment]
    if not segments:
        raise ValueError("alias must contain at least one path segment")

    current: Any = registry
    for segment in segments:
        if not isinstance(current, Mapping) or segment not in current:
            raise KeyError(f"Secret alias not found in registry {registry_path}: {normalized_alias}")
        current = current[segment]

    if not isinstance(current, Mapping):
        raise ValueError(
            f"Secret alias entry must be an object in registry {registry_path}: {normalized_alias}"
        )

    path = current.get("path")
    if not isinstance(path, str) or path.strip() == "":
        raise ValueError(
            f"Secret alias entry is missing a readable path in registry {registry_path}: {normalized_alias}"
        )

    return {
        "alias": normalized_alias,
        "path": path,
        "kind": current.get("kind") if isinstance(current.get("kind"), str) else None,
        "use": current.get("use") if isinstance(current.get("use"), str) else None,
    }


class SecretResolver:
    """Resolve secret text by stable registry config id."""

    def __init__(
        self,
        query: QueryFn,
        *,
        registry_path: str = "/root/secrets/registry.json",
        read_text: ReadTextFn | None = None,
    ):
        self._reader = RegistryReader(query)
        self._registry_path = registry_path
        self._read_text = read_text or (lambda path: Path(path).read_text(encoding="utf-8"))

    def _load_registry(self) -> Mapping[str, Any]:
        return parse_registry(self._read_text(self._registry_path), self._registry_path)

    def load_secret_text_by_config_id(self, config_id: str) -> str:
        normalized = _non_empty_string("config_id", config_id)
        item = self._reader.require_item_by_id(normalized)

        if item.kind != "config":
            raise ValueError(
                f"Registry item {normalized} must be kind=config to resolve a secret alias by id"
            )

        alias = _non_empty_string(f"registry config payload for {normalized}", item.payload)
        entry = get_secret_entry_from_registry(self._load_registry(), alias, self._registry_path)
        return self._read_text(str(entry["path"])).strip()
