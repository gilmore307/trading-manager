"""Collect manager-visible dataset evidence for expansion decisions.

This module turns durable model-governance and manager-control-plane facts into
`manager_dataset_evidence`, the evidence input consumed by the dataset
expansion planner. It does not call providers, train models, activate models, or
mutate broker/execution state.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .dataset_expansion import DatasetRole, ROLE_ORDER
from .model_training_workflow import LAYER_METADATA, layer_key as workflow_layer_key
from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_MODEL_SCHEMA = "trading_model"
DEFAULT_DATASET_EVIDENCE_PATH = DEFAULT_STORAGE_ROOT / "runtime" / "dataset_expansion" / "evidence.json"
DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")

MODEL_IDS_BY_LAYER: dict[int, str] = {
    int(meta["layer"]): f"{meta['slug']}_model" if meta["slug"] != "target_state_vector" else "target_state_vector_model"
    for meta in LAYER_METADATA
}
MODEL_ID_ALIASES_BY_LAYER: dict[int, tuple[str, ...]] = {
    1: ("market_regime_model",),
    2: ("sector_context_model", "target_state_vector_model"),
    5: ("option_expression_model",),
    6: ("event_risk_governor_model",),
}
LAYER_KEYS_BY_LAYER: dict[int, str] = {
    int(meta["layer"]): workflow_layer_key(int(meta["layer"]), str(meta["slug"])) for meta in LAYER_METADATA
}

SPLIT_ROLE_ALIASES: dict[str, DatasetRole] = {
    "train": "train",
    "training": "train",
    "in_sample": "train",
    "is": "train",
    "calibration": "calibration",
    "calibrate": "calibration",
    "calib": "calibration",
    "validation": "validation",
    "valid": "validation",
    "val": "validation",
    "test": "test",
    "holdout": "test",
    "hold_out": "test",
    "promotion_holdout": "test",
    "final_holdout": "test",
    "forward": "forward_holdout",
    "forward_holdout": "forward_holdout",
    "out_of_time": "forward_holdout",
    "oot": "forward_holdout",
    "out_of_sample": "forward_holdout",
    "oos": "forward_holdout",
    "shadow": "shadow_monitoring",
    "shadow_monitoring": "shadow_monitoring",
    "paper": "shadow_monitoring",
    "paper_monitoring": "shadow_monitoring",
}

EVIDENCE_ROLE_ORDER: tuple[DatasetRole, ...] = (*ROLE_ORDER, "shadow_monitoring")

PROMOTION_GAP_KEYWORDS: dict[str, str] = {
    "coverage": "coverage",
    "drift": "drift",
    "split_stability": "split_stability",
    "stability": "split_stability",
    "stale_holdout": "stale_holdout",
    "regime": "regime_coverage",
    "baseline": "baseline_instability",
    "label": "missing_labels",
    "eval": "missing_eval_run",
}


@dataclass(frozen=True)
class DatasetEvidenceRoleSummary:
    """Collected evidence for one layer/role."""

    role: DatasetRole
    month_count: int = 0
    sample_count: int = 0
    label_count: int = 0
    eval_run_count: int = 0
    artifact_count: int = 0
    ready_signal_count: int = 0
    snapshot_ref: str | None = None
    split_refs: tuple[str, ...] = ()

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["split_refs"] = list(self.split_refs)
        return row


@dataclass(frozen=True)
class DatasetEvidenceLayerSummary:
    """Collected evidence for one model layer."""

    layer: int
    layer_key: str
    model_id: str
    roles: tuple[DatasetEvidenceRoleSummary, ...]
    promotion_gaps: tuple[str, ...] = ()
    production_approved: bool = False
    evidence_sources: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def summary_row(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "layer_key": self.layer_key,
            "model_id": self.model_id,
            "roles": {role.role: role.summary_row() for role in self.roles},
            "promotion_gaps": list(self.promotion_gaps),
            "production_approved": self.production_approved,
            "evidence_sources": list(self.evidence_sources),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class DatasetEvidenceCollection:
    """Manager dataset evidence contract consumed by expansion planning."""

    contract_type: str
    layers: tuple[DatasetEvidenceLayerSummary, ...]
    source_summary: dict[str, int]
    warnings: tuple[str, ...] = ()
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "layers": {str(layer.layer): layer.summary_row() for layer in self.layers},
            "source_summary": dict(self.source_summary),
            "warnings": list(self.warnings),
            "provider_calls": self.provider_calls,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
        }


def database_url(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    value = os.environ.get("OPENCLAW_DATABASE_URL", "").strip() or os.environ.get("DATABASE_URL", "").strip()
    if value:
        return value
    if DEFAULT_DB_URL_FILE.exists():
        return DEFAULT_DB_URL_FILE.read_text(encoding="utf-8").strip()
    raise TaskSystemError(f"database URL required: pass --database-url or create {DEFAULT_DB_URL_FILE}")


def normalize_split_role(split_name: Any) -> DatasetRole | None:
    raw = str(split_name or "").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in SPLIT_ROLE_ALIASES:
        return SPLIT_ROLE_ALIASES[raw]
    for token, role in SPLIT_ROLE_ALIASES.items():
        if token and token in raw:
            return role
    return None


def _coerce_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def month_coverage(start: Any, end: Any) -> int:
    start_dt = _coerce_datetime(start)
    end_dt = _coerce_datetime(end)
    if start_dt is None or end_dt is None or end_dt < start_dt:
        return 0
    return (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1


def _json_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, Mapping) else {}
    return {}


def _row_count_from_payload(row: Mapping[str, Any], *payload_keys: str) -> int:
    for key in ("sample_count", "row_count", "feature_row_count"):
        value = row.get(key)
        if isinstance(value, int):
            return value
    payload = _json_mapping(row.get("split_payload_json") or row.get("snapshot_payload_json") or row.get("metric_payload_json"))
    for key in (*payload_keys, "sample_count", "row_count", "feature_row_count"):
        value = payload.get(key)
        if isinstance(value, int):
            return value
    return 0


def _promotion_gaps_from_metrics(metric_rows: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    gaps: set[str] = set()
    for row in metric_rows:
        haystack_parts = [str(row.get("metric_name") or ""), str(row.get("factor_name") or ""), str(row.get("label_name") or "")]
        payload = _json_mapping(row.get("metric_payload_json"))
        haystack_parts.extend(str(value) for key, value in payload.items() if key in {"status", "gate_status", "reason", "gap", "failure"})
        haystack = " ".join(haystack_parts).lower()
        failed = any(token in haystack for token in ("fail", "failed", "missing", "insufficient", "unstable", "defer"))
        if not failed:
            continue
        for keyword, gap in PROMOTION_GAP_KEYWORDS.items():
            if keyword in haystack:
                gaps.add(gap)
    return tuple(sorted(gaps))


def collect_dataset_evidence_from_rows(
    *,
    snapshot_rows: Sequence[Mapping[str, Any]] = (),
    split_rows: Sequence[Mapping[str, Any]] = (),
    label_rows: Sequence[Mapping[str, Any]] = (),
    eval_run_rows: Sequence[Mapping[str, Any]] = (),
    metric_rows: Sequence[Mapping[str, Any]] = (),
    artifact_rows: Sequence[Mapping[str, Any]] = (),
    ready_signal_rows: Sequence[Mapping[str, Any]] = (),
    warnings: Sequence[str] = (),
) -> DatasetEvidenceCollection:
    snapshots_by_id = {str(row.get("snapshot_id")): row for row in snapshot_rows if row.get("snapshot_id")}
    splits_by_snapshot: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in split_rows:
        if row.get("snapshot_id"):
            splits_by_snapshot[str(row["snapshot_id"])].append(row)
    labels_by_snapshot: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in label_rows:
        if row.get("snapshot_id"):
            labels_by_snapshot[str(row["snapshot_id"])].append(row)
    evals_by_snapshot: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in eval_run_rows:
        if row.get("snapshot_id"):
            evals_by_snapshot[str(row["snapshot_id"])].append(row)
    metrics_by_model: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    eval_model_by_run = {str(row.get("eval_run_id")): str(row.get("model_id")) for row in eval_run_rows if row.get("eval_run_id")}
    for row in metric_rows:
        model_id = eval_model_by_run.get(str(row.get("eval_run_id")))
        if model_id:
            metrics_by_model[model_id].append(row)

    artifact_count_by_model_role: dict[tuple[str, DatasetRole], int] = defaultdict(int)
    for row in artifact_rows:
        model_id = str(row.get("model_id") or row.get("model") or "")
        role = normalize_split_role(row.get("dataset_role") or row.get("split_name") or row.get("consumer_hint"))
        if model_id and role:
            artifact_count_by_model_role[(model_id, role)] += 1
    ready_count_by_model_role: dict[tuple[str, DatasetRole], int] = defaultdict(int)
    for row in ready_signal_rows:
        model_id = str(row.get("model_id") or row.get("model") or "")
        role = normalize_split_role(row.get("dataset_role") or row.get("consumer_hint") or row.get("signal_kind"))
        if model_id and role:
            ready_count_by_model_role[(model_id, role)] += 1

    layers: list[DatasetEvidenceLayerSummary] = []
    global_warnings = list(warnings)
    for layer in sorted(MODEL_IDS_BY_LAYER):
        model_id = MODEL_IDS_BY_LAYER[layer]
        model_ids = (model_id, *MODEL_ID_ALIASES_BY_LAYER.get(layer, ()))
        model_id_set = set(model_ids)
        model_snapshots = [row for row in snapshot_rows if row.get("model_id") in model_id_set]
        role_accumulator: dict[DatasetRole, dict[str, Any]] = {
            role: {
                "month_count": 0,
                "sample_count": 0,
                "label_count": 0,
                "eval_run_count": 0,
                "artifact_count": sum(artifact_count_by_model_role[(candidate_model_id, role)] for candidate_model_id in model_ids),
                "ready_signal_count": sum(ready_count_by_model_role[(candidate_model_id, role)] for candidate_model_id in model_ids),
                "snapshot_ref": None,
                "split_refs": [],
            }
            for role in EVIDENCE_ROLE_ORDER
        }
        evidence_sources: set[str] = set()
        layer_warnings: list[str] = []
        for snapshot in model_snapshots:
            snapshot_id = str(snapshot.get("snapshot_id"))
            snapshot_sample_count = _row_count_from_payload(snapshot)
            for split in splits_by_snapshot.get(snapshot_id, []):
                role = normalize_split_role(split.get("split_name"))
                if role is None:
                    layer_warnings.append(f"ignored unknown split_name={split.get('split_name')!r} for snapshot {snapshot_id}")
                    continue
                acc = role_accumulator[role]
                acc["month_count"] += month_coverage(split.get("split_start_time"), split.get("split_end_time"))
                acc["sample_count"] += _row_count_from_payload(split) or snapshot_sample_count
                acc["snapshot_ref"] = acc["snapshot_ref"] or snapshot_id
                if split.get("split_id"):
                    acc["split_refs"].append(str(split["split_id"]))
                evidence_sources.add("trading_model.model_dataset_split")
            if labels_by_snapshot.get(snapshot_id):
                evidence_sources.add("trading_model.model_eval_label")
            if evals_by_snapshot.get(snapshot_id):
                evidence_sources.add("trading_model.model_eval_run")
            label_count = sum(int(row.get("label_count") or 1) for row in labels_by_snapshot.get(snapshot_id, []))
            eval_count = sum(
                int(row.get("eval_run_count") or 1)
                for row in evals_by_snapshot.get(snapshot_id, [])
                if str(row.get("run_status") or "").lower() in {"succeeded", "success", "completed", "complete"}
            )
            for role in EVIDENCE_ROLE_ORDER:
                if role_accumulator[role]["snapshot_ref"] == snapshot_id:
                    role_accumulator[role]["label_count"] += label_count
                    role_accumulator[role]["eval_run_count"] += eval_count
        role_summaries = []
        for role in EVIDENCE_ROLE_ORDER:
            acc = role_accumulator[role]
            role_summaries.append(
                DatasetEvidenceRoleSummary(
                    role=role,
                    month_count=int(acc["month_count"]),
                    sample_count=int(acc["sample_count"]),
                    label_count=int(acc["label_count"]),
                    eval_run_count=int(acc["eval_run_count"]),
                    artifact_count=int(acc["artifact_count"]),
                    ready_signal_count=int(acc["ready_signal_count"]),
                    snapshot_ref=acc["snapshot_ref"],
                    split_refs=tuple(dict.fromkeys(acc["split_refs"])),
                )
            )
        gaps = set()
        for candidate_model_id in model_ids:
            gaps.update(_promotion_gaps_from_metrics(metrics_by_model[candidate_model_id]))
        if not model_snapshots:
            gaps.add("coverage")
            layer_warnings.append("no model_dataset_snapshot rows found")
        else:
            for role in ("train", "calibration", "validation", "test"):
                summary = next(item for item in role_summaries if item.role == role)
                if summary.month_count == 0:
                    gaps.add("coverage")
                elif summary.label_count == 0 and role != "train":
                    gaps.add("missing_labels")
                elif summary.eval_run_count == 0 and role in {"validation", "test"}:
                    gaps.add("missing_eval_run")
        layers.append(
            DatasetEvidenceLayerSummary(
                layer=layer,
                layer_key=LAYER_KEYS_BY_LAYER[layer],
                model_id=model_id,
                roles=tuple(role_summaries),
                promotion_gaps=tuple(sorted(gaps)),
                production_approved=False,
                evidence_sources=tuple(sorted(evidence_sources)),
                warnings=tuple(dict.fromkeys(layer_warnings)),
            )
        )

    return DatasetEvidenceCollection(
        contract_type="manager_dataset_evidence",
        layers=tuple(layers),
        source_summary={
            "model_dataset_snapshot": len(snapshot_rows),
            "model_dataset_split": len(split_rows),
            "model_eval_label": sum(int(row.get("label_count") or 1) for row in label_rows),
            "model_eval_run": len(eval_run_rows),
            "model_promotion_metric": len(metric_rows),
            "manager_artifact_ref": len(artifact_rows),
            "manager_ready_signal": len(ready_signal_rows),
        },
        warnings=tuple(global_warnings),
    )


def _quote_identifier(identifier: str) -> str:
    if not identifier.replace("_", "a").isalnum() or not identifier or identifier[0].isdigit():
        raise TaskSystemError(f"unsafe SQL identifier: {identifier!r}")
    return '"' + identifier.replace('"', '""') + '"'


def _qualified(schema: str, table: str) -> str:
    return f"{_quote_identifier(schema)}.{_quote_identifier(table)}"


def _fetch_table_rows(connection: Any, *, schema: str, table: str, columns: Sequence[str]) -> tuple[list[dict[str, Any]], str | None]:
    from psycopg.rows import dict_row

    regclass = f"{schema}.{table}"
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute("SELECT to_regclass(%s) AS table_ref", [regclass])
        if cursor.fetchone()["table_ref"] is None:
            return [], f"missing table {regclass}"
        cursor.execute(f"SELECT {', '.join(_quote_identifier(column) for column in columns)} FROM {_qualified(schema, table)}")
        return [dict(row) for row in cursor.fetchall()], None


def _fetch_query_rows_if_table(connection: Any, *, schema: str, table: str, sql: str) -> tuple[list[dict[str, Any]], str | None]:
    from psycopg.rows import dict_row

    regclass = f"{schema}.{table}"
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute("SELECT to_regclass(%s) AS table_ref", [regclass])
        if cursor.fetchone()["table_ref"] is None:
            return [], f"missing table {regclass}"
        cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()], None


def collect_dataset_evidence_from_database(*, database_url_value: str | None = None, model_schema: str = DEFAULT_MODEL_SCHEMA) -> DatasetEvidenceCollection:
    import psycopg
    from psycopg.rows import dict_row

    warnings: list[str] = []
    with psycopg.connect(database_url(database_url_value)) as connection:
        snapshot_rows, warning = _fetch_table_rows(
            connection,
            schema=model_schema,
            table="model_dataset_snapshot",
            columns=("snapshot_id", "model_id", "data_start_time", "data_end_time", "feature_row_count", "snapshot_payload_json"),
        )
        if warning:
            warnings.append(warning)
        split_rows, warning = _fetch_table_rows(
            connection,
            schema=model_schema,
            table="model_dataset_split",
            columns=("split_id", "snapshot_id", "split_name", "split_start_time", "split_end_time", "split_payload_json"),
        )
        if warning:
            warnings.append(warning)
        label_rows, warning = _fetch_query_rows_if_table(
            connection,
            schema=model_schema,
            table="model_eval_label",
            sql=f"SELECT snapshot_id, COUNT(*)::BIGINT AS label_count FROM {_qualified(model_schema, 'model_eval_label')} GROUP BY snapshot_id",
        )
        if warning:
            warnings.append(warning)
        eval_run_rows, warning = _fetch_table_rows(
            connection,
            schema=model_schema,
            table="model_eval_run",
            columns=("eval_run_id", "model_id", "snapshot_id", "run_status", "run_payload_json", "started_at", "completed_at"),
        )
        if warning:
            warnings.append(warning)
        metric_rows, warning = _fetch_table_rows(
            connection,
            schema=model_schema,
            table="model_promotion_metric",
            columns=("metric_id", "eval_run_id", "split_id", "label_name", "horizon", "factor_name", "metric_name", "metric_value", "metric_payload_json"),
        )
        if warning:
            warnings.append(warning)
        artifact_rows: list[dict[str, Any]] = []
        ready_signal_rows: list[dict[str, Any]] = []
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT to_regclass(%s) AS table_ref", ["trading_manager.artifact_ref"])
            if cursor.fetchone()["table_ref"] is not None:
                cursor.execute(
                    """
                    SELECT ar.artifact_id, ar.artifact_kind, ar.uri, ar.row_count, rm.component_id, rm.repo_id
                    FROM trading_manager.artifact_ref ar
                    JOIN trading_manager.run_manifest rm ON rm.run_id = ar.producer_run_id
                    WHERE ar.lifecycle_status IN ('active', 'ready')
                    """
                )
                artifact_rows = [dict(row) for row in cursor.fetchall()]
            else:
                warnings.append("missing table trading_manager.artifact_ref")
            cursor.execute("SELECT to_regclass(%s) AS table_ref", ["trading_manager.ready_signal"])
            if cursor.fetchone()["table_ref"] is not None:
                cursor.execute(
                    """
                    SELECT rs.ready_signal_id, rs.signal_kind, rs.status, rs.consumer_hint, rs.producer_component_id
                    FROM trading_manager.ready_signal rs
                    WHERE rs.status IN ('ready', 'partial')
                    """
                )
                ready_signal_rows = [dict(row) for row in cursor.fetchall()]
            else:
                warnings.append("missing table trading_manager.ready_signal")

    return collect_dataset_evidence_from_rows(
        snapshot_rows=snapshot_rows,
        split_rows=split_rows,
        label_rows=label_rows,
        eval_run_rows=eval_run_rows,
        metric_rows=metric_rows,
        artifact_rows=artifact_rows,
        ready_signal_rows=ready_signal_rows,
        warnings=warnings,
    )


def write_collection(collection: DatasetEvidenceCollection, *, output: TextIO) -> None:
    json.dump(collection.summary_row(), output, indent=2, sort_keys=True, default=str)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect manager-visible dataset evidence for expansion planning.")
    parser.add_argument("--database-url")
    parser.add_argument("--model-schema", default=DEFAULT_MODEL_SCHEMA)
    parser.add_argument("--output-path", type=Path)
    parser.add_argument("--write", action="store_true", help="Write evidence JSON to --output-path or the default runtime evidence path.")
    args = parser.parse_args(argv)

    collection = collect_dataset_evidence_from_database(database_url_value=args.database_url, model_schema=args.model_schema)
    if args.write:
        output_path = args.output_path or DEFAULT_DATASET_EVIDENCE_PATH
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(collection.summary_row(), indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    write_collection(collection, output=sys.stdout)
    return 0


__all__ = [
    "DatasetEvidenceCollection",
    "DatasetEvidenceLayerSummary",
    "DatasetEvidenceRoleSummary",
    "collect_dataset_evidence_from_database",
    "collect_dataset_evidence_from_rows",
    "month_coverage",
    "normalize_split_role",
]


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())
