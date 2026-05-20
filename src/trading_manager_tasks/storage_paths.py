"""Storage-owned filesystem roots for manager orchestration artifacts."""

from __future__ import annotations

import os
from pathlib import Path


def _path_from_env(name: str, default: Path) -> Path:
    value = os.environ.get(name, "").strip()
    return Path(value).expanduser() if value else default


def projects_root() -> Path:
    return _path_from_env("TRADING_PROJECTS_ROOT", Path("/root/projects"))


def trading_storage_root() -> Path:
    return _path_from_env("TRADING_STORAGE_ROOT", projects_root() / "trading-storage")


def component_storage_root(component: str) -> Path:
    return trading_storage_root() / "storage" / component


def manager_storage_root() -> Path:
    return _path_from_env("TRADING_MANAGER_STORAGE_ROOT", component_storage_root("manager"))


def data_storage_root() -> Path:
    return _path_from_env("TRADING_DATA_STORAGE_ROOT", component_storage_root("data"))


def model_storage_root() -> Path:
    return _path_from_env("TRADING_MODEL_STORAGE_ROOT", component_storage_root("model"))


def model_runtime_root() -> Path:
    return model_storage_root() / "runtime"


__all__ = [
    "component_storage_root",
    "data_storage_root",
    "manager_storage_root",
    "model_runtime_root",
    "model_storage_root",
    "projects_root",
    "trading_storage_root",
]
