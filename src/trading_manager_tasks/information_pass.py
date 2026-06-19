"""Controlled information pass for the first formal historical month.

The information pass is a manager-owned evidence-gathering surface. It prepares
safe artifacts and summarizes what must be measured before broad defaults are
accepted. It performs no provider calls, model activation, broker execution, or
storage lifecycle mutation.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, TextIO

from .dataset_evidence import collect_dataset_evidence_from_database
from .dataset_expansion import (
    DatasetExpansionPlan,
    DatasetRoleEvidence,
    LayerDatasetEvidence,
    build_dataset_expansion_plan,
    load_dataset_evidence,
)
from .provider_dispatch import ProviderDispatchSummary, dispatch_layer_one_provider_acquisition
from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_INFORMATION_PASS_PATH = DEFAULT_STORAGE_ROOT / "runtime" / "information_pass" / "controlled_information_pass_2016-01.json"


@dataclass(frozen=True)
class ResourceSnapshot:
    """Lightweight host capacity facts for later concurrency decisions."""

    cpu_count: int | None
    memory_total_mb: int | None
    storage_root: str
    storage_free_mb: int | None
    storage_total_mb: int | None

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InformationNeed:
    """One unresolved decision area and the evidence needed to close it."""

    topic: str
    status: str
    evidence_needed: tuple[str, ...]
    safe_next_action: str

    def summary_row(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "status": self.status,
            "evidence_needed": list(self.evidence_needed),
            "safe_next_action": self.safe_next_action,
        }


@dataclass(frozen=True)
class ControlledInformationPass:
    """Manager report for the 2016-01 controlled information pass."""

    contract_type: str
    start_month: str
    end_month: str
    purpose: str
    resource_snapshot: ResourceSnapshot
    dataset_expansion_plan: DatasetExpansionPlan
    provider_dispatch_validation: ProviderDispatchSummary | None
    information_needs: tuple[InformationNeed, ...]
    wrote_report: bool
    report_path: str | None
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "start_month": self.start_month,
            "end_month": self.end_month,
            "purpose": self.purpose,
            "resource_snapshot": self.resource_snapshot.summary_row(),
            "dataset_expansion_plan": self.dataset_expansion_plan.summary_row(),
            "provider_dispatch_validation": self.provider_dispatch_validation.summary_row()
            if self.provider_dispatch_validation
            else None,
            "information_needs": [item.summary_row() for item in self.information_needs],
            "wrote_report": self.wrote_report,
            "report_path": self.report_path,
            "provider_calls": self.provider_calls,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
            "storage_lifecycle_mutation_performed": self.storage_lifecycle_mutation_performed,
        }


def _memory_total_mb() -> int | None:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return None
    for line in meminfo.read_text(encoding="utf-8").splitlines():
        if line.startswith("MemTotal:"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1]) // 1024
    return None


def collect_resource_snapshot(storage_root: Path = DEFAULT_STORAGE_ROOT) -> ResourceSnapshot:
    """Collect safe host facts without stress testing the machine."""

    try:
        usage = shutil.disk_usage(storage_root if storage_root.exists() else storage_root.parent)
        free_mb = int(usage.free // (1024 * 1024))
        total_mb = int(usage.total // (1024 * 1024))
    except OSError:
        free_mb = None
        total_mb = None
    return ResourceSnapshot(
        cpu_count=os.cpu_count(),
        memory_total_mb=_memory_total_mb(),
        storage_root=str(storage_root),
        storage_free_mb=free_mb,
        storage_total_mb=total_mb,
    )


def _empty_evidence() -> tuple[LayerDatasetEvidence, ...]:
    return load_dataset_evidence(None)


def _information_needs(*, dispatch: ProviderDispatchSummary | None, plan: DatasetExpansionPlan) -> tuple[InformationNeed, ...]:
    provider_status = "plan_previewed_without_provider_calls" if dispatch else "needs_plan_only_preview"
    selected = plan.selected_decision
    selected_action = selected.action if selected else "no_dataset_expansion_selected"
    return (
        InformationNeed(
            topic="provider_dispatch_expansion",
            status=provider_status,
            evidence_needed=(
                "plan-only preview for each provider-backed acquisition adapter",
                "actual 2016-01 request counts, latency, error classes, retry behavior, and provider quota pressure during autonomous acquisition",
            ),
            safe_next_action="prepare task keys and preview provider dispatch; do not execute provider calls inside the information pass",
        ),
        InformationNeed(
            topic="concurrency_defaults",
            status="needs_controlled_runtime_measurement",
            evidence_needed=(
                "CPU, memory, disk I/O, PostgreSQL pressure during a small autonomous 2016-01 batch",
                "worker saturation point outside regular-trading-day protection windows",
                "throttle behavior under provider rate-limit or host pressure signals",
            ),
            safe_next_action="record baseline resource snapshot now; derive worker defaults only after measured batch evidence",
        ),
        InformationNeed(
            topic="l3_l7_target_queue_rules",
            status="needs_candidate_pool_inventory",
            evidence_needed=(
                "candidate source universe and target_candidate_id inventory",
                "ranking signals such as liquidity, event density, sector coverage, data completeness, and representativeness",
                "one-target-at-a-time chain receipt evidence through Layers 3-7",
            ),
            safe_next_action="inventory candidate pools after M01/M02 coverage exists; keep L3-L7 target-major serial default",
        ),
        InformationNeed(
            topic="dataset_thresholds",
            status="needs_real_dataset_evidence",
            evidence_needed=(
                "observed month/sample/label/evaluation coverage per layer and dataset role",
                "baseline improvement, split stability, regime coverage, and no-leakage evidence",
                "forward-holdout evidence when promotion gaps remain",
            ),
            safe_next_action=f"use current dataset expansion decision `{selected_action}` as the next safe evidence-producing step",
        ),
        InformationNeed(
            topic="artifact_discovery",
            status="needs_component_receipt_samples",
            evidence_needed=(
                "real component completion receipts for feed/source/feature/model/eval/review stages",
                "stable output artifact refs, hashes, schema refs, retention hints, and ready-signal refs",
                "component-specific artifact discovery rules once receipt samples exist",
            ),
            safe_next_action="collect receipt samples from dry-run and approved 2016-01 stages before generalizing discovery rules",
        ),
        InformationNeed(
            topic="storage_lifecycle_implementation",
            status="needs_artifact_index_and_protected_set_dry_run",
            evidence_needed=(
                "storage artifact index rows over real 2016-01 outputs",
                "protected-set builder evidence for promoted model bodies, source data, and reusable intermediates",
                "quarantine, tombstone, compression/archive manifest, and restore-verifier dry-runs before destructive executors",
            ),
            safe_next_action="run lifecycle planning in dry-run/protected-set mode only; keep physical delete/compress/archive disabled",
        ),
    )


def build_controlled_information_pass(
    *,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    evidence: tuple[LayerDatasetEvidence, ...] | None = None,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    preview_provider_dispatch: bool = False,
    write: bool = False,
    output_path: Path = DEFAULT_INFORMATION_PASS_PATH,
) -> ControlledInformationPass:
    """Build the safe information pass report.

    If ``write`` is true, this may write manager-side report/task-key artifacts,
    but it still performs no provider calls, model activation, broker execution,
    or storage lifecycle mutation.
    """

    evidence = evidence if evidence is not None else _empty_evidence()
    expansion_plan = build_dataset_expansion_plan(
        start_month=start_month,
        end_month=end_month,
        evidence=evidence,
        storage_root=storage_root,
        write=write,
        output_path=output_path.parent / "manager_dataset_expansion_plan.json",
    )
    dispatch_summary = None
    if preview_provider_dispatch:
        dispatch_summary = dispatch_layer_one_provider_acquisition(
            start_month=start_month,
            end_month=end_month,
            storage_root=storage_root,
            execute_provider_calls=False,
        )
    report = ControlledInformationPass(
        contract_type="manager_controlled_information_pass",
        start_month=start_month,
        end_month=end_month,
        purpose="Measure the remaining provider, concurrency, target-queue, dataset-threshold, artifact-discovery, and storage-lifecycle unknowns for the first formal historical month before accepting broad automation defaults.",
        resource_snapshot=collect_resource_snapshot(storage_root),
        dataset_expansion_plan=expansion_plan,
        provider_dispatch_validation=dispatch_summary,
        information_needs=_information_needs(dispatch=dispatch_summary, plan=expansion_plan),
        wrote_report=write,
        report_path=str(output_path) if write else None,
    )
    if write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def write_information_pass(report: ControlledInformationPass, *, output: TextIO) -> None:
    json.dump(report.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def _load_evidence(args: argparse.Namespace) -> tuple[LayerDatasetEvidence, ...]:
    if args.evidence and args.collect_evidence_from_db:
        raise SystemExit("use either --evidence or --collect-evidence-from-db, not both")
    if args.collect_evidence_from_db:
        collected = collect_dataset_evidence_from_database(database_url_value=args.database_url, model_schema=args.model_schema)
        return tuple(
            LayerDatasetEvidence(
                layer=layer.layer,
                layer_key=layer.layer_key,
                roles=tuple(
                    DatasetRoleEvidence(
                        role=role.role,
                        month_count=role.month_count,
                        sample_count=role.sample_count,
                        snapshot_ref=role.snapshot_ref,
                    )
                    for role in layer.roles
                ),
                promotion_gaps=layer.promotion_gaps,
                production_approved=layer.production_approved,
            )
            for layer in collected.layers
        )
    return load_dataset_evidence(args.evidence)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a safe 2016-01 controlled information pass report.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--evidence", type=Path, help="Optional manager_dataset_evidence JSON file.")
    parser.add_argument("--collect-evidence-from-db", action="store_true", help="Collect current dataset evidence from SQL before planning.")
    parser.add_argument("--database-url")
    parser.add_argument("--model-schema", default="trading_model")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--preview-provider-dispatch", action="store_true", help="Include a plan-only provider dispatch preview without calling providers.")
    parser.add_argument("--output-path", type=Path, default=DEFAULT_INFORMATION_PASS_PATH)
    parser.add_argument("--write", action="store_true", help="Write safe report and preparation artifacts. Does not call providers.")
    args = parser.parse_args(argv)

    report = build_controlled_information_pass(
        start_month=args.start_month,
        end_month=args.end_month,
        evidence=_load_evidence(args),
        storage_root=args.storage_root,
        preview_provider_dispatch=args.preview_provider_dispatch,
        write=args.write,
        output_path=args.output_path,
    )
    write_information_pass(report, output=sys.stdout)
    return 0


__all__ = [
    "ControlledInformationPass",
    "InformationNeed",
    "ResourceSnapshot",
    "build_controlled_information_pass",
    "collect_resource_snapshot",
    "write_information_pass",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
