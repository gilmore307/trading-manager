"""Workflow-state invalidation helpers for stale downstream model outputs."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, TextIO

from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_RUNTIME_ROOT = Path("runtime")
DEFAULT_REASON = "stale_provisional_invalidated_event_sources_incomplete_rebuild_from_residual_event_governance_required"
DEFAULT_SOURCE_LAYER = 10


@dataclass(frozen=True)
class InvalidationSummary:
    contract_type: str
    state_file_count: int
    invalidated_stage_count: int
    preserved_stage_count: int
    affected_files: tuple[str, ...]
    layer_floor: int
    reason: str
    write_performed: bool
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "state_file_count": self.state_file_count,
            "invalidated_stage_count": self.invalidated_stage_count,
            "preserved_stage_count": self.preserved_stage_count,
            "affected_files": list(self.affected_files),
            "layer_floor": self.layer_floor,
            "reason": self.reason,
            "write_performed": self.write_performed,
            "provider_calls": self.provider_calls,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
        }


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _state_paths(runtime_root: Path, explicit_paths: Iterable[Path] = ()) -> list[Path]:
    explicit = [Path(path) for path in explicit_paths]
    if explicit:
        return explicit
    return sorted(runtime_root.glob("model_training_fold_state_*.json"))


def invalidate_layer_downstream_outputs(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    runtime_root: Path | None = None,
    state_paths: Iterable[Path] = (),
    layer_floor: int = 10,
    reason: str = DEFAULT_REASON,
    source_layer: int = DEFAULT_SOURCE_LAYER,
    write: bool = False,
) -> InvalidationSummary:
    """Mark stale event-risk-dependent workflow stages as failed/rebuild-required.

    This is deliberately state-only and offline: it never deletes artifacts, calls
    providers, activates models, submits orders, or writes storage read models.
    """

    root = runtime_root or (storage_root / DEFAULT_RUNTIME_ROOT)
    paths = _state_paths(root, state_paths)
    invalidated = 0
    preserved = 0
    affected: list[str] = []
    now = _utc_now()
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        stages = []
        for raw_stage in payload.get("stages") or []:
            if not isinstance(raw_stage, dict):
                continue
            stage = dict(raw_stage)
            layer = int(stage.get("layer") or 0)
            if layer >= layer_floor and stage.get("status") in {"succeeded", "ready", "blocked", "pending"}:
                if stage.get("last_reason") != reason or stage.get("status") != "failed":
                    stage["status"] = "failed"
                    stage["last_reason"] = reason
                    stage["status_updated_at_utc"] = now
                    stage["updated_utc"] = now
                    refs = list(stage.get("artifact_refs") or [])
                    marker = f"manager://stale_downstream_from_layer_{source_layer:02d}_event_source_rebuild_required"
                    if marker not in refs:
                        refs.append(marker)
                    stage["artifact_refs"] = refs
                    changed = True
                invalidated += 1
            else:
                preserved += 1
            stages.append(stage)
        if changed:
            payload["stages"] = stages
            payload["updated_utc"] = now
            affected.append(str(path))
            if write:
                tmp = path.with_suffix(path.suffix + ".tmp")
                tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                tmp.replace(path)
    return InvalidationSummary(
        contract_type="manager_model_training_downstream_invalidation",
        state_file_count=len(paths),
        invalidated_stage_count=invalidated,
        preserved_stage_count=preserved,
        affected_files=tuple(affected),
        layer_floor=layer_floor,
        reason=reason,
        write_performed=write,
    )


def write_summary(summary: InvalidationSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mark stale event-risk-dependent model-training workflow stages as rebuild-required without deleting artifacts.")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--state-path", action="append", type=Path, default=[])
    parser.add_argument("--layer-floor", type=int, default=10)
    parser.add_argument("--source-layer", type=int, default=DEFAULT_SOURCE_LAYER)
    parser.add_argument("--reason", default=DEFAULT_REASON)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    summary = invalidate_layer_downstream_outputs(
        storage_root=args.storage_root,
        runtime_root=args.runtime_root,
        state_paths=args.state_path,
        layer_floor=args.layer_floor,
        reason=args.reason,
        source_layer=args.source_layer,
        write=args.write,
    )
    write_summary(summary, output=sys.stdout)
    return 0


__all__ = ["DEFAULT_REASON", "DEFAULT_SOURCE_LAYER", "InvalidationSummary", "invalidate_layer_downstream_outputs"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
