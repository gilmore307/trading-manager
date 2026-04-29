"""Template pipeline for a trading-source historical acquisition bundle.

Copy this file into:

    trading-source/src/data_sources/<bundle>/pipeline.py

Keep one public bundle entry point (`run`) while preserving clear internal step
boundaries for fetch, clean, save, and receipt generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BundleContext:
    """Runtime paths and shared state derived from the task key."""

    task_key: dict[str, Any]
    run_dir: Path
    raw_dir: Path
    cleaned_dir: Path
    saved_dir: Path
    receipt_path: Path
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StepResult:
    """Minimal step result shape used by the pipeline template."""

    status: str
    references: list[str] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def build_context(task_key: dict[str, Any], run_id: str) -> BundleContext:
    """Build development output paths for one run of a stable task key.

    `output_root` should normally be a stable ignored local runtime path such
    as `storage/<task-id>` until a durable storage contract exists.
    Each run writes under `output_root/runs/<run-id>`, while the task-level
    completion receipt lives at `output_root/completion_receipt.json`.
    """

    output_root = Path(task_key["output_root"])
    run_dir = output_root / "runs" / run_id
    return BundleContext(
        task_key=task_key,
        run_dir=run_dir,
        raw_dir=run_dir / "raw",
        cleaned_dir=run_dir / "cleaned",
        saved_dir=run_dir / "saved",
        receipt_path=output_root / "completion_receipt.json",
        metadata={"run_id": run_id},
    )


def fetch(context: BundleContext) -> StepResult:
    """Retrieve source data and write raw development files.

    Bundle-specific implementation belongs here.
    """

    raise NotImplementedError("Implement bundle-specific fetch step")


def clean(context: BundleContext, fetch_result: StepResult) -> StepResult:
    """Normalize raw files into cleaned development outputs.

    Bundle-specific implementation belongs here.
    """

    raise NotImplementedError("Implement bundle-specific clean step")


def save(context: BundleContext, clean_result: StepResult) -> StepResult:
    """Save cleaned outputs under the development run directory.

    Do not write to SQL by default during development.
    """

    raise NotImplementedError("Implement bundle-specific save step")


def write_receipt(
    context: BundleContext,
    *,
    status: str,
    fetch_result: StepResult | None = None,
    clean_result: StepResult | None = None,
    save_result: StepResult | None = None,
    error: BaseException | None = None,
) -> StepResult:
    """Append or update one run entry in the task-level completion receipt.

    Bundle-specific receipt serialization belongs here. This function should be
    able to run even when fetch, clean, or save fails.
    """

    raise NotImplementedError("Implement bundle-specific receipt step")


def run(task_key: dict[str, Any], *, run_id: str) -> StepResult:
    """Run one invocation of a stable manager-issued task key."""

    context = build_context(task_key, run_id)
    context.raw_dir.mkdir(parents=True, exist_ok=True)
    context.cleaned_dir.mkdir(parents=True, exist_ok=True)
    context.saved_dir.mkdir(parents=True, exist_ok=True)

    fetch_result: StepResult | None = None
    clean_result: StepResult | None = None
    save_result: StepResult | None = None

    try:
        fetch_result = fetch(context)
        clean_result = clean(context, fetch_result)
        save_result = save(context, clean_result)
        return write_receipt(
            context,
            status="succeeded",
            fetch_result=fetch_result,
            clean_result=clean_result,
            save_result=save_result,
        )
    except BaseException as exc:
        return write_receipt(
            context,
            status="failed",
            fetch_result=fetch_result,
            clean_result=clean_result,
            save_result=save_result,
            error=exc,
        )
