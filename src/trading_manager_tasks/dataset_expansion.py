"""Manager-owned dataset expansion decisions for historical model training.

The manager decides which dataset role needs expansion next, then prepares the
allowed work without weakening provider, model-activation, or execution gates.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, TextIO

from .historical_training import HistoricalTrainingBatchPreparation, prepare_layer_one_historical_training_batch
from .request_payloads import DEFAULT_STORAGE_ROOT

DatasetRole = Literal["train", "calibration", "validation", "test", "forward_holdout", "shadow_monitoring"]
ExpansionStatus = Literal["planned", "prepared", "blocked", "not_applicable"]

DEFAULT_DATASET_EXPANSION_PATH = Path("storage/runtime/dataset_expansion/manager_dataset_expansion_plan.json")

ROLE_ORDER: tuple[DatasetRole, ...] = ("train", "calibration", "validation", "test", "forward_holdout")
PROMOTION_GAPS_REQUIRING_FORWARD_HOLDOUT = {
    "coverage",
    "drift",
    "split_stability",
    "stale_holdout",
    "regime_coverage",
    "baseline_instability",
}

LAYER_SLUGS: dict[int, str] = {
    1: "market_regime",
    2: "sector_context",
    3: "target_state_vector",
    4: "event_overlay",
    5: "alpha_confidence",
    6: "position_projection",
    7: "underlying_action",
    8: "option_expression",
}

LAYER_DEPENDENCIES: dict[int, tuple[int, ...]] = {
    1: (),
    2: (1,),
    3: (1, 2),
    4: (1, 2, 3),
    5: (1, 2, 3, 4),
    6: (5,),
    7: (5, 6),
    8: (7,),
}

DEFAULT_MINIMUM_MONTHS: dict[DatasetRole, int] = {
    "train": 60,
    "calibration": 12,
    "validation": 12,
    "test": 12,
    "forward_holdout": 6,
    "shadow_monitoring": 1,
}


@dataclass(frozen=True)
class DatasetRoleEvidence:
    """Observed dataset coverage for one layer/role."""

    role: DatasetRole
    month_count: int = 0
    sample_count: int = 0
    snapshot_ref: str | None = None

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LayerDatasetEvidence:
    """Manager-visible evidence for one model layer."""

    layer: int
    layer_key: str
    roles: tuple[DatasetRoleEvidence, ...]
    promotion_gaps: tuple[str, ...] = ()
    production_approved: bool = False

    def role(self, role: DatasetRole) -> DatasetRoleEvidence:
        by_role = {item.role: item for item in self.roles}
        return by_role.get(role, DatasetRoleEvidence(role=role))

    def minimum_roles_satisfied(self, minimum_months: Mapping[DatasetRole, int]) -> bool:
        return all(self.role(role).month_count >= int(minimum_months[role]) for role in ("train", "calibration", "validation", "test"))

    def summary_row(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "layer_key": self.layer_key,
            "roles": [role.summary_row() for role in self.roles],
            "promotion_gaps": list(self.promotion_gaps),
            "production_approved": self.production_approved,
        }


@dataclass(frozen=True)
class DatasetExpansionDecision:
    """The next dataset expansion manager has selected."""

    layer: int
    layer_key: str
    dataset_role: DatasetRole
    reason: str
    action: str
    requires_provider_approval: bool
    approval_gate_required: str | None
    safe_without_provider_calls: bool
    provider_calls_allowed: bool = False
    model_activation_allowed: bool = False
    broker_execution_allowed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetExpansionImplementation:
    """What manager did to implement the selected expansion."""

    status: ExpansionStatus
    wrote_plan: bool
    plan_path: str | None
    wrote_layer_one_payloads: bool = False
    layer_one_preparation: dict[str, Any] | None = None
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    note: str | None = None

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DatasetExpansionPlan:
    """Manager-owned dataset expansion plan and optional preparation receipt."""

    contract_type: str
    start_month: str
    end_month: str
    minimum_months: dict[DatasetRole, int]
    evidence: tuple[LayerDatasetEvidence, ...]
    selected_decision: DatasetExpansionDecision | None
    implementation: DatasetExpansionImplementation

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "start_month": self.start_month,
            "end_month": self.end_month,
            "minimum_months": dict(self.minimum_months),
            "evidence": [item.summary_row() for item in self.evidence],
            "selected_decision": self.selected_decision.summary_row() if self.selected_decision else None,
            "implementation": self.implementation.summary_row(),
            "provider_calls": self.implementation.provider_calls,
            "model_activation_performed": self.implementation.model_activation_performed,
            "broker_execution_performed": self.implementation.broker_execution_performed,
        }


def layer_key(layer: int) -> str:
    return f"layer_{layer:02d}_{LAYER_SLUGS[layer]}"


def _role_from_payload(role: str) -> DatasetRole:
    if role not in DEFAULT_MINIMUM_MONTHS:
        raise ValueError(f"unsupported dataset role: {role}")
    return role  # type: ignore[return-value]


def _coerce_layer_evidence(layer: int, payload: Mapping[str, Any]) -> LayerDatasetEvidence:
    role_payload = payload.get("roles") or {}
    roles = []
    if isinstance(role_payload, Mapping):
        for role_name, role_row in role_payload.items():
            role = _role_from_payload(str(role_name))
            row = role_row if isinstance(role_row, Mapping) else {}
            roles.append(
                DatasetRoleEvidence(
                    role=role,
                    month_count=int(row.get("month_count") or 0),
                    sample_count=int(row.get("sample_count") or 0),
                    snapshot_ref=row.get("snapshot_ref"),
                )
            )
    return LayerDatasetEvidence(
        layer=layer,
        layer_key=layer_key(layer),
        roles=tuple(sorted(roles, key=lambda item: ROLE_ORDER.index(item.role) if item.role in ROLE_ORDER else 99)),
        promotion_gaps=tuple(str(item) for item in payload.get("promotion_gaps") or ()),
        production_approved=bool(payload.get("production_approved", False)),
    )


def load_dataset_evidence(path: Path | None) -> tuple[LayerDatasetEvidence, ...]:
    """Load manager-visible dataset evidence, or return empty layer evidence."""

    if path is None or not path.exists():
        return tuple(LayerDatasetEvidence(layer=layer, layer_key=layer_key(layer), roles=()) for layer in range(1, 9))
    payload = json.loads(path.read_text(encoding="utf-8"))
    layers_payload = payload.get("layers") if isinstance(payload, Mapping) else None
    if not isinstance(layers_payload, Mapping):
        raise ValueError("dataset evidence JSON must contain object field 'layers'")
    rows = []
    for layer in range(1, 9):
        row = layers_payload.get(str(layer)) or layers_payload.get(layer) or {}
        if not isinstance(row, Mapping):
            row = {}
        rows.append(_coerce_layer_evidence(layer, row))
    return tuple(rows)


def _upstream_ready(layer: int, evidence_by_layer: Mapping[int, LayerDatasetEvidence], minimum_months: Mapping[DatasetRole, int]) -> tuple[bool, str | None]:
    missing = []
    for dep in LAYER_DEPENDENCIES[layer]:
        dep_evidence = evidence_by_layer[dep]
        if not dep_evidence.minimum_roles_satisfied(minimum_months):
            missing.append(dep_evidence.layer_key)
    if missing:
        return False, "waiting for upstream minimum train/calibration/validation/test coverage: " + ",".join(missing)
    return True, None


def decide_dataset_expansion(
    evidence: tuple[LayerDatasetEvidence, ...],
    *,
    minimum_months: Mapping[DatasetRole, int] = DEFAULT_MINIMUM_MONTHS,
) -> DatasetExpansionDecision | None:
    """Select the next dataset role manager should expand.

    The manager walks layers in dependency order. For each eligible layer, it
    fills training, calibration, validation, and test coverage before expanding
    forward holdout. Shadow monitoring is only selected after production approval.
    """

    by_layer = {item.layer: item for item in evidence}
    for layer in range(1, 9):
        layer_evidence = by_layer[layer]
        upstream_ready, upstream_reason = _upstream_ready(layer, by_layer, minimum_months)
        if not upstream_ready:
            continue
        for role in ("train", "calibration", "validation", "test"):
            required = int(minimum_months[role])
            observed = layer_evidence.role(role).month_count
            if observed < required:
                return _decision_for_role(
                    layer_evidence,
                    role,
                    reason=f"{role} coverage {observed}/{required} months; {upstream_reason or 'upstream coverage ready'}",
                )
        normalized_gaps = {gap.strip().lower() for gap in layer_evidence.promotion_gaps}
        if normalized_gaps & PROMOTION_GAPS_REQUIRING_FORWARD_HOLDOUT:
            observed = layer_evidence.role("forward_holdout").month_count
            required = int(minimum_months["forward_holdout"])
            if observed < required:
                return _decision_for_role(
                    layer_evidence,
                    "forward_holdout",
                    reason=(
                        f"promotion gaps require forward holdout {observed}/{required} months: "
                        + ",".join(sorted(normalized_gaps & PROMOTION_GAPS_REQUIRING_FORWARD_HOLDOUT))
                    ),
                )
        if layer_evidence.production_approved:
            observed = layer_evidence.role("shadow_monitoring").month_count
            required = int(minimum_months["shadow_monitoring"])
            if observed < required:
                return _decision_for_role(
                    layer_evidence,
                    "shadow_monitoring",
                    reason=f"production-approved layer needs shadow monitoring coverage {observed}/{required} months",
                )
    return None


def _decision_for_role(layer_evidence: LayerDatasetEvidence, role: DatasetRole, *, reason: str) -> DatasetExpansionDecision:
    requires_provider = layer_evidence.layer in {1, 8}
    if layer_evidence.layer == 1:
        action = "prepare_layer_one_historical_training_batch"
    elif layer_evidence.layer == 8:
        action = "prepare_approval_gated_option_expression_acquisition"
    else:
        action = "queue_offline_dataset_materialization"
    return DatasetExpansionDecision(
        layer=layer_evidence.layer,
        layer_key=layer_evidence.layer_key,
        dataset_role=role,
        reason=reason,
        action=action,
        requires_provider_approval=requires_provider,
        approval_gate_required="live_call_approval_v1" if requires_provider else None,
        safe_without_provider_calls=True,
    )


def build_dataset_expansion_plan(
    *,
    start_month: str,
    end_month: str,
    evidence: tuple[LayerDatasetEvidence, ...],
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    write: bool = False,
    output_path: Path = DEFAULT_DATASET_EXPANSION_PATH,
) -> DatasetExpansionPlan:
    decision = decide_dataset_expansion(evidence)
    implementation = DatasetExpansionImplementation(status="planned", wrote_plan=False, plan_path=None)
    layer_one_preparation: HistoricalTrainingBatchPreparation | None = None
    if write and decision and decision.action == "prepare_layer_one_historical_training_batch":
        layer_one_preparation, _, _, _ = prepare_layer_one_historical_training_batch(
            start_month=start_month,
            end_month=end_month,
            storage_root=storage_root,
            write=True,
            persist_sql=False,
            validate_handoff=True,
        )
        implementation = DatasetExpansionImplementation(
            status="prepared",
            wrote_plan=True,
            plan_path=str(output_path),
            wrote_layer_one_payloads=True,
            layer_one_preparation=layer_one_preparation.summary_row(),
            note="Prepared Layer 1 task-key payloads only; provider dispatch still requires live_call_approval_v1.",
        )
    elif write and decision:
        implementation = DatasetExpansionImplementation(
            status="prepared" if not decision.requires_provider_approval else "blocked",
            wrote_plan=True,
            plan_path=str(output_path),
            note=(
                "Expansion request selected by manager; component-specific implementation is queued through the workflow state."
                if not decision.requires_provider_approval
                else "Provider-backed expansion selected; dispatch remains blocked until live_call_approval_v1."
            ),
        )
    elif decision is None:
        implementation = DatasetExpansionImplementation(
            status="not_applicable",
            wrote_plan=False,
            plan_path=None,
            note="No dataset expansion gap selected from current evidence.",
        )

    plan = DatasetExpansionPlan(
        contract_type="manager_dataset_expansion_plan_v1",
        start_month=start_month,
        end_month=end_month,
        minimum_months=dict(DEFAULT_MINIMUM_MONTHS),
        evidence=evidence,
        selected_decision=decision,
        implementation=implementation,
    )
    if write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(plan.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return plan


def write_plan(plan: DatasetExpansionPlan, *, output: TextIO) -> None:
    json.dump(plan.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Let manager decide and prepare the next historical-training dataset expansion.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--evidence", type=Path, help="Optional manager-visible dataset evidence JSON.")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--output-path", type=Path, default=DEFAULT_DATASET_EXPANSION_PATH)
    parser.add_argument("--write", action="store_true", help="Prepare the selected safe expansion artifact/payloads without provider calls.")
    args = parser.parse_args(argv)

    evidence = load_dataset_evidence(args.evidence)
    plan = build_dataset_expansion_plan(
        start_month=args.start_month,
        end_month=args.end_month,
        evidence=evidence,
        storage_root=args.storage_root,
        write=args.write,
        output_path=args.output_path,
    )
    write_plan(plan, output=sys.stdout)
    return 0


__all__ = [
    "DatasetExpansionDecision",
    "DatasetExpansionImplementation",
    "DatasetExpansionPlan",
    "DatasetRoleEvidence",
    "LayerDatasetEvidence",
    "build_dataset_expansion_plan",
    "decide_dataset_expansion",
    "load_dataset_evidence",
]


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())
