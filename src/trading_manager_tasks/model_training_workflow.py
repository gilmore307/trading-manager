"""Historical six-model research workflow graph.

The manager owns orchestration across the historical-modeling service. This
module defines reusable foundation substrate, target substrate, full-minute
six-model generation, replay, M06 residual-event governance, evaluation,
promotion, and maintenance boundaries.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Mapping as MappingABC
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, TextIO

from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER, load_market_regime_universe
from .request_payloads import DEFAULT_STORAGE_ROOT
from .storage_paths import data_storage_root, model_runtime_root

StageStatus = Literal["ready", "blocked", "complete", "not_applicable"]

BASE_STACK_LAYER_COUNT = 6
BASE_INPUT_STAGE_LAYERS = (1, 2, 3, 5)
LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS = 19
LAYER_TWO_REQUIRED_ALPACA_BAR_REQUESTS = 12
DATASET_UNIT_MONTHS = 6
FOUNDATION_CATCH_UP_LAYERS = (1, 3)
MONTHLY_SUBSTRATE_LAYERS = (1, 3)
FOUNDATION_CATCH_UP_STAGE_TYPES = ("data_acquisition", "feature_generation")
FOUNDATION_CATCH_UP_BLOCKER = "model_01_03_historical_catch_up_to_current_required"
POST_MODEL_GENERATION_REBUILD_BLOCKER = "post_model_generation_rebuild_required_after_model_01_03_catch_up"
ROLLING_FOLD_TRAIN_MONTHS = 4
ROLLING_FOLD_VALIDATION_MONTHS = 1
ROLLING_FOLD_TEST_MONTHS = 1
ROLLING_FOLD_SIZE_MONTHS = ROLLING_FOLD_TRAIN_MONTHS + ROLLING_FOLD_VALIDATION_MONTHS + ROLLING_FOLD_TEST_MONTHS
ROLLING_FOLD_SPLIT_MONTHS = (
    ("train", ROLLING_FOLD_TRAIN_MONTHS),
    ("validation", ROLLING_FOLD_VALIDATION_MONTHS),
    ("test", ROLLING_FOLD_TEST_MONTHS),
)
REQUIRED_MODEL_GENERATION_SPLIT_NAMES = tuple(split_name for split_name, _months in ROLLING_FOLD_SPLIT_MONTHS)
PROMOTION_STAGE_TYPE = "promotion_review"
FOLD_STACK_PROMOTION_BLOCKER = "fold_models_01_06_model_generation_complete"
MODEL_GROUP_REPLAY_COMPLETE_BLOCKER = "model_group_replay_complete"
MULTI_TARGET_SYMBOL_BLOCKER = "multiple_target_symbols_require_separate_workflows"
MODEL_RUNTIME_ROOT = model_runtime_root()
MODEL_THREE_EVENT_OBSERVATION_COVERAGE_BLOCKER = "model_03_event_state_event_observation_pool_ready"
MODEL_SIX_EVENT_FEED_COVERAGE_BLOCKER = "model_06_event_feed_coverage_ready"
MODEL_TWO_TARGET_LOCAL_FEED_ARTIFACTS_BLOCKER = "model_02_target_local_feed_artifacts_ready"
MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID = "model_05_option_expression.option_chain_data_acquisition"
MODEL_FIVE_OPTION_CHAIN_SOURCE_BLOCKER = f"{MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID}_complete"
NO_LISTED_OPTION_STATUSES = {"confirmed_no_listed_options", "no_listed_options", "no_listed_options_or_unverified"}
NO_OPTION_ASSET_CLASSES = {"crypto_spot", "spot_crypto", "crypto"}


@dataclass(frozen=True)
class DatasetUnit:
    """Operator-visible historical-training dataset work unit."""

    unit_kind: str
    unit_months: int
    start_month: str
    end_month: str
    target_symbol: str | None
    target_required: bool
    description: str

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowStage:
    """One manager-orchestrated stage for a model layer."""

    stage_id: str
    layer: int
    layer_key: str
    stage_type: str
    description: str
    status: StageStatus
    command: list[str]
    dataset_unit: DatasetUnit
    blockers: tuple[str, ...] = ()
    dataset_split: dict[str, Any] | None = None
    approval_gate_required: str | None = None
    safe_without_provider_calls: bool = True
    provider_calls_allowed: bool = False
    model_activation_allowed: bool = False
    broker_execution_allowed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["dataset_unit"] = self.dataset_unit.summary_row()
        row["blockers"] = list(self.blockers)
        return row


@dataclass(frozen=True)
class LayerWorkflow:
    """Manager workflow coverage for one model layer."""

    layer: int
    layer_key: str
    model_name: str
    depends_on_layers: tuple[int, ...]
    progression_mode: str
    candidate_axis: str
    candidate_progression_policy: str
    dataset_unit: DatasetUnit
    data_surface: str
    feature_command: list[str]
    model_generate_command: list[str]
    model_evaluate_command: list[str]
    promotion_review_command: list[str]
    maintenance_command: list[str]
    stages: tuple[WorkflowStage, ...]

    def summary_row(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "layer_key": self.layer_key,
            "model_name": self.model_name,
            "depends_on_layers": list(self.depends_on_layers),
            "progression_mode": self.progression_mode,
            "candidate_axis": self.candidate_axis,
            "candidate_progression_policy": self.candidate_progression_policy,
            "dataset_unit": self.dataset_unit.summary_row(),
            "data_surface": self.data_surface,
            "feature_command": self.feature_command,
            "model_generate_command": self.model_generate_command,
            "model_evaluate_command": self.model_evaluate_command,
            "promotion_review_command": self.promotion_review_command,
            "maintenance_command": self.maintenance_command,
            "stages": [stage.summary_row() for stage in self.stages],
        }


@dataclass(frozen=True)
class ModelTrainingWorkflowPlan:
    """Manager-owned base-stack workflow plan inside the historical service."""

    contract_type: str
    start_month: str
    end_month: str
    selected_target_symbol: str | None
    layer_count: int
    layer_one_task_key_count: int
    layer_two_task_key_count: int
    layers: tuple[LayerWorkflow, ...]
    next_stage: WorkflowStage | None
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    foundation_catch_up_only: bool = True
    foundation_catch_up_layers: tuple[int, ...] = FOUNDATION_CATCH_UP_LAYERS
    reusable_substrate_stage_types: tuple[str, ...] = FOUNDATION_CATCH_UP_STAGE_TYPES
    post_model_generation_artifacts_policy: str = "supersede_and_rebuild_after_model_01_03_historical_catch_up"

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "start_month": self.start_month,
            "end_month": self.end_month,
            "selected_target_symbol": self.selected_target_symbol,
            "layer_count": self.layer_count,
            "layer_one_task_key_count": self.layer_one_task_key_count,
            "layer_two_task_key_count": self.layer_two_task_key_count,
            "layers": [layer.summary_row() for layer in self.layers],
            "next_stage": self.next_stage.summary_row() if self.next_stage else None,
            "provider_calls": self.provider_calls,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
            "foundation_catch_up_only": self.foundation_catch_up_only,
            "foundation_catch_up_layers": list(self.foundation_catch_up_layers),
            "reusable_substrate_stage_types": list(self.reusable_substrate_stage_types),
            "post_model_generation_artifacts_policy": self.post_model_generation_artifacts_policy,
        }


def _stage_field(stage: Any, field_name: str) -> Any:
    if isinstance(stage, MappingABC):
        return stage.get(field_name)
    return getattr(stage, field_name, None)


def _model_generation_split_name(stage: Any) -> str | None:
    dataset_split = _stage_field(stage, "dataset_split")
    if not isinstance(dataset_split, MappingABC):
        return None
    split_name = str(dataset_split.get("split_name") or "")
    return split_name if split_name in REQUIRED_MODEL_GENERATION_SPLIT_NAMES else None


def model_generation_splits_complete(stages: Any, *, layer_number: int) -> bool:
    """Return whether one layer has completed every required chronological split."""

    split_statuses: dict[str, str] = {}
    for stage in stages:
        if str(_stage_field(stage, "stage_type") or "") != "model_generation":
            continue
        try:
            stage_layer = int(_stage_field(stage, "layer") or 0)
        except (TypeError, ValueError):
            continue
        if stage_layer != layer_number:
            continue
        split_name = _model_generation_split_name(stage)
        if split_name is None:
            continue
        split_statuses[split_name] = str(_stage_field(stage, "status") or "").lower()
    return all(split_statuses.get(split_name) in {"succeeded", "not_applicable"} for split_name in REQUIRED_MODEL_GENERATION_SPLIT_NAMES)


def base_stack_model_generation_splits_complete(stages: Any, *, layer_count: int = BASE_STACK_LAYER_COUNT) -> bool:
    """Return whether M01-M06 have completed train/validation/test generation."""

    return all(model_generation_splits_complete(stages, layer_number=layer_number) for layer_number in range(1, layer_count + 1))


LAYER_METADATA: tuple[dict[str, Any], ...] = (
    {
        "layer": 1,
        "slug": "background_context",
        "model_name": "BackgroundContextModel",
        "depends_on_layers": (),
        "progression_mode": "background_panel_continuous",
        "candidate_axis": "six_month_window",
        "candidate_progression_policy": "complete fixed M01 market and sector background substrate for each six-month chronological unit; promotion waits for M01-M06 model generation, model-group replay, and residual-event attribution",
        "data_surface": "autonomous Alpaca market/background ETF bars acquisition plus migration-source m01/m02 context features",
        "feature_cli": "trading-data-m01-market-regime-feature-generation",
    },
    {
        "layer": 2,
        "slug": "target_state",
        "model_name": "TargetStateModel",
        "depends_on_layers": (1,),
        "progression_mode": "target_state_full_minute_coverage",
        "candidate_axis": "target_symbol;six_month_window;target_candidate_id",
        "candidate_progression_policy": "materialize anonymous target-state samples for every eligible minute; evaluation and promotion must aggregate by fold and candidate-universe policy batch",
        "data_surface": "target-local source artifacts, accepted target-context mappings, m03_target_state_vector_data_acquisition, and m03_target_state_vector_feature_generation as migration-source input",
        "feature_cli": "trading-data-m03-target-state-vector-feature-generation",
    },
    {
        "layer": 3,
        "slug": "event_state",
        "model_name": "EventStateModel",
        "depends_on_layers": (1, 2),
        "progression_mode": "event_state_full_minute_coverage",
        "candidate_axis": "target_symbol;six_month_window;target_candidate_id;event_state_context_id",
        "candidate_progression_policy": "apply M06-governed event-family attributes point-in-time, including no-event minutes and option-vs-underlying impact channels",
        "data_surface": "fold-scoped event observation inputs and reviewed event_interpretation normalization; no raw event alpha requirement",
        "input_stage": True,
        "feature_cli": None,
    },
    {
        "layer": 4,
        "slug": "unified_decision",
        "model_name": "UnifiedDecisionModel",
        "depends_on_layers": (1, 2, 3),
        "progression_mode": "target_major_serial_chain",
        "candidate_axis": "target_symbol;six_month_window;target_candidate_id;decision_context_id",
        "candidate_progression_policy": "train the full-minute direct-underlying utility decision, including no-trade and maintain outcomes as first-class rows",
        "data_surface": "M01 background, M02 target state, M03 event state, costs, account capacity, risk budget, current/pending position, and labels",
        "feature_cli": None,
    },
    {
        "layer": 5,
        "slug": "option_expression",
        "model_name": "OptionExpressionModel",
        "depends_on_layers": (4,),
        "progression_mode": "conditional_option_expression_after_underlying_intent",
        "candidate_axis": "target_symbol;six_month_window;minute_timestamp;option_contract_bucket",
        "candidate_progression_policy": "train option-expression and explicit no-option/not-applicable states after M04 direct-underlying intent exists; live/replay invocation remains conditional",
        "data_surface": "m05_option_expression_feature_generation migration-source rows derived from shared option_chain_state_source after M04 intent",
        "feature_cli": "trading-data-m05-option-expression-feature-generation",
    },
    {
        "layer": 6,
        "slug": "residual_event_governance",
        "model_name": "ResidualEventGovernanceModel",
        "depends_on_layers": (1, 3, 4, 5),
        "progression_mode": "residual_event_governance_after_thesis",
        "candidate_axis": "target_symbol;six_month_window;target_candidate_id;residual_event_context_id",
        "candidate_progression_policy": "train residual event intervention, overblock/underblock, missed-event, and underlying-vs-option failure attribution after M04/M05 thesis formation",
        "data_surface": "M01 background, M03 event state, M04 decision, optional M05 expression, event observations, and settled replay/failure evidence",
        "feature_cli": None,
    },
)

def layer_key(layer: int, slug: str) -> str:
    return f"model_{layer:02d}_{slug}"


REVIEW_SCRIPT_NAMES: dict[int, str] = {
    1: "review_background_context_promotion.py",
    2: "review_target_state_promotion.py",
    3: "review_event_state_promotion.py",
    4: "review_unified_decision_promotion.py",
    5: "review_option_expression_promotion.py",
    6: "review_residual_event_governance_promotion.py",
}


def model_script(layer: int, slug: str, verb: str) -> list[str]:
    script_name = REVIEW_SCRIPT_NAMES[layer] if verb == "review" else f"{verb}_model_{layer:02d}_{slug}.py"
    physical_model_key = f"model_{layer:02d}_{slug}"
    command = [
        "PYTHONPATH=/root/projects/trading-model/src",
        "python3",
        f"/root/projects/trading-model/scripts/models/{physical_model_key}/{script_name}",
    ]
    if layer in {2, 4, 5, 6} and verb == "generate":
        command.extend([
            "--from-database",
            "--source-start",
            "${START_MONTH_START_ET}",
            "--source-end",
            "${END_MONTH_EXCLUSIVE_START_ET}",
        ])
    if verb == "evaluate":
        command.extend([
            "--output-json",
            f"{MODEL_RUNTIME_ROOT}/{physical_model_key}/evaluation_summary_${{START_MONTH}}.json",
        ])
        if layer == 5:
            command.extend([
                "--from-database",
                "--source-start",
                "${START_MONTH_START_ET}",
                "--source-end",
                "${END_MONTH_EXCLUSIVE_START_ET}",
            ])
    if verb == "review":
        command.extend([
            "--evaluation-summary-json",
            f"{MODEL_RUNTIME_ROOT}/{physical_model_key}/evaluation_summary_${{START_MONTH}}.json",
            "--output-json",
            f"{MODEL_RUNTIME_ROOT}/{physical_model_key}/promotion_review_${{START_MONTH}}.json",
        ])
    return command


def _target_scoped_generation_command(command: list[str], *, layer: int, selected_target_symbol: str | None) -> list[str]:
    _ = (layer, selected_target_symbol)
    return command


FEATURE_MODULES: dict[str, str] = {
    "trading-data-m01-market-regime-feature-generation": "data_feature.m01_market_regime_feature_generation.from_feed_artifacts",
    "trading-data-m02-sector-context-feature-generation": "data_feature.m02_sector_context_feature_generation.from_feed_artifacts",
    "trading-data-m03-target-state-vector-feature-generation": "data_feature.m03_target_state_vector_feature_generation",
    "trading-data-m06-residual-event-governance-feature-generation": "data_feature.m06_residual_event_governance_feature_generation",
    "trading-data-m05-option-expression-feature-generation": "data_feature.m05_option_expression_feature_generation",
}


def feature_command(feature_cli: str | None, *, selected_target_symbol: str | None = None) -> list[str]:
    if feature_cli is None:
        return ["manager-internal", "no-dedicated-trading-data-feature-stage"]
    if feature_cli == "manager-model-03-event-state-feature-generation":
        return [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/materialize_layer_four_event_observation_inputs.py",
            "--start-month",
            "${START_MONTH}",
            "--end-month",
            "${END_MONTH}",
            "--write",
        ]
    if feature_cli == "trading-data-m02-sector-context-feature-generation":
        return [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/execute_layer_two_feature_generation.py",
            "--month",
            "${START_MONTH}",
            "--write",
        ]
    if feature_cli == "trading-data-m05-option-expression-feature-generation":
        command = [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/execute_m05_option_expression_feature_generation.py",
            "--start-month",
            "${START_MONTH}",
            "--end-month",
            "${END_MONTH}",
        ]
        if selected_target_symbol:
            command.extend(["--target-symbol", selected_target_symbol])
        return command
    command = ["PYTHONPATH=/root/projects/trading-data/src", "python3", "-m", FEATURE_MODULES[feature_cli]]
    if feature_cli in {"trading-data-m01-market-regime-feature-generation", "trading-data-m02-sector-context-feature-generation"}:
        command.extend(["--month", "${START_MONTH}"])
    if feature_cli in {"trading-data-m03-target-state-vector-feature-generation", "trading-data-m06-residual-event-governance-feature-generation"}:
        command.extend([
            "--source-start",
            "${START_MONTH_START_ET}",
            "--source-end",
            "${END_MONTH_EXCLUSIVE_START_ET}",
            "--run-id",
            f"{FEATURE_MODULES[feature_cli].split('.')[-1]}_${{START_MONTH}}",
        ])
    return command


def maintenance_command(layer: int, slug: str) -> list[str]:
    physical_model_key = f"model_{layer:02d}_{slug}"
    return [
        "PYTHONPATH=src",
        "python3",
        "scripts/tasks/plan_model_promotion_review.py",
        "--model",
        physical_model_key,
        "--candidate-ref",
        f"storage://trading-model/promotion-candidates/{physical_model_key}_latest.json",
    ]


def _symbols_for_model_layer(model_layer: str) -> tuple[str, ...]:
    return tuple(member.symbol for member in load_market_regime_universe(model_layers=(model_layer,)))


def count_alpaca_bar_task_keys(storage_root: Path, *, start_month: str, model_layer: str) -> int:
    root = storage_root / "monthly_backfill" / "alpaca_bars"
    if not root.exists():
        return 0
    symbols = set(_symbols_for_model_layer(model_layer))
    return sum(1 for symbol in symbols if (root / symbol / start_month / "task_key.json").exists())


def count_layer_one_task_keys(storage_root: Path, *, start_month: str) -> int:
    return count_alpaca_bar_task_keys(storage_root, start_month=start_month, model_layer=LAYER_ONE_MODEL_LAYER)


def count_layer_two_task_keys(storage_root: Path, *, start_month: str) -> int:
    return count_alpaca_bar_task_keys(storage_root, start_month=start_month, model_layer=LAYER_TWO_MODEL_LAYER)


def _stage_status_for_provider_acquisition(
    *,
    task_key_count: int,
    required_count: int,
    preparation_blocker: str,
) -> tuple[StageStatus, tuple[str, ...], str | None]:
    if task_key_count < required_count:
        return "blocked", (preparation_blocker,), None
    return "ready", (), None


def _dataset_unit_for_layer(
    *,
    layer: int,
    start_month: str,
    end_month: str,
    selected_target_symbol: str | None,
) -> DatasetUnit:
    if layer == 1:
        return DatasetUnit(
            unit_kind="six_month_panel",
            unit_months=DATASET_UNIT_MONTHS,
            start_month=start_month,
            end_month=end_month,
            target_symbol=None,
            target_required=False,
            description="M01 dataset unit: fixed background panel over one six-month window; no single target symbol applies.",
        )
    target = _normalize_selected_target_symbol(selected_target_symbol)
    target_text = target if target else "UNSELECTED_TARGET"
    return DatasetUnit(
        unit_kind="target_symbol_six_month",
        unit_months=DATASET_UNIT_MONTHS,
        start_month=start_month,
        end_month=end_month,
        target_symbol=target,
        target_required=True,
        description=f"M{layer:02d} dataset unit: target {target_text} over one six-month window.",
    )


def _input_dataset_unit_for_layer(
    *,
    layer: int,
    start_month: str,
    end_month: str,
    selected_target_symbol: str | None,
) -> DatasetUnit:
    if layer == 3:
        return DatasetUnit(
            unit_kind="event_observation_fold_panel",
            unit_months=DATASET_UNIT_MONTHS,
            start_month=start_month,
            end_month=end_month,
            target_symbol=None,
            target_required=False,
            description="M03 input unit: fold-scoped global/sector event-observation substrate; no single target symbol applies.",
        )
    return _dataset_unit_for_layer(
        layer=layer,
        start_month=start_month,
        end_month=end_month,
        selected_target_symbol=selected_target_symbol,
    )


def _stage_requires_target(*, layer: int, stage_type: str) -> bool:
    if layer < 2:
        return False
    if layer == 3 and stage_type in {"data_acquisition", "feature_generation"}:
        return False
    return True


def _with_target_blocker(
    blockers: tuple[str, ...],
    *,
    layer: int,
    selected_target_symbol: str | None,
    stage_type: str,
) -> tuple[str, ...]:
    if _stage_requires_target(layer=layer, stage_type=stage_type) and not (selected_target_symbol and selected_target_symbol.strip()):
        return ("selected_target_symbol_required",) + blockers
    return blockers


def _normalize_selected_target_symbol(selected_target_symbol: str | None) -> str | None:
    if not selected_target_symbol:
        return None
    symbol = selected_target_symbol.strip().upper()
    if not symbol:
        return None
    if any(separator in symbol for separator in (",", ";", " ")) or "\t" in symbol or "\n" in symbol:
        raise ValueError(MULTI_TARGET_SYMBOL_BLOCKER)
    return symbol


def _read_csv_rows_if_exists(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple({str(key): str(value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle))


def _target_option_overlay_required(*, selected_target_symbol: str | None, trading_storage_root: Path) -> bool:
    target = _normalize_selected_target_symbol(selected_target_symbol)
    if target is None:
        return True

    from . import layer_three_target_state

    mapping_rows = _read_csv_rows_if_exists(layer_three_target_state.DEFAULT_TARGET_CONTEXT_MAPPING)
    for row in mapping_rows:
        if row.get("target_symbol", "").upper() != target:
            continue
        if row.get("review_status", "").lower() != "accepted":
            continue
        asset_class = row.get("target_asset_class", "").lower()
        option_status = row.get("optionable_proxy_status", "").lower()
        if asset_class in NO_OPTION_ASSET_CLASSES or option_status in NO_LISTED_OPTION_STATUSES:
            return False

    shared_root = trading_storage_root / "main" / "shared"
    for path in (shared_root / "historical_candidate_universe.csv", shared_root / "equity_total_symbol_pool.csv"):
        for row in _read_csv_rows_if_exists(path):
            if row.get("symbol", "").upper() != target:
                continue
            asset_class = (row.get("target_asset_class") or row.get("asset_class") or row.get("instrument_type") or "").lower()
            option_status = (
                row.get("optionable_underlying_status")
                or row.get("optionable_proxy_status")
                or row.get("listed_option_status")
                or ""
            ).lower()
            if asset_class in NO_OPTION_ASSET_CLASSES or option_status in NO_LISTED_OPTION_STATUSES:
                return False
    return True


def _upstream_model_ready_blockers(depends_on_layers: tuple[int, ...], *, foundation_catch_up_only: bool) -> tuple[str, ...]:
    suffix = "complete" if foundation_catch_up_only else "model_generation_complete"
    return tuple(f"upstream_model_{dep:02d}_{suffix}" for dep in depends_on_layers)


def _event_feed_coverage_blockers(*, start_month: str, end_month: str, trading_storage_root: Path) -> tuple[str, ...]:
    from .residual_event_governance_inputs import (
        _discover_event_feed_artifacts,
        _event_feed_row_coverage,
        _missing_event_feed_artifacts,
        _missing_event_feed_rows,
    )

    event_artifact_paths, event_feed_coverage = _discover_event_feed_artifacts(
        trading_storage_root=trading_storage_root,
        start_month=start_month,
        end_month=end_month,
    )
    event_feed_row_coverage = _event_feed_row_coverage(event_artifact_paths, start_month=start_month, end_month=end_month)
    if _missing_event_feed_artifacts(event_feed_coverage) or _missing_event_feed_rows(event_feed_row_coverage):
        return (MODEL_SIX_EVENT_FEED_COVERAGE_BLOCKER,)
    return ()


def _model_three_event_observation_blockers(*, start_month: str, end_month: str, trading_storage_root: Path) -> tuple[str, ...]:
    _ = (start_month, end_month, trading_storage_root)
    return (
        "model_01_background_context.feature_or_input_ready",
    )


def _resolve_event_feed_storage_root(storage_root: Path, trading_storage_root: Path | None) -> Path:
    if trading_storage_root is not None:
        return trading_storage_root
    if storage_root == DEFAULT_STORAGE_ROOT:
        return data_storage_root()
    return storage_root


def _next_month(month: str) -> str:
    year, month_number = int(month[:4]), int(month[5:])
    if month_number == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month_number + 1:02d}"


def _add_months(month: str, offset: int) -> str:
    year, month_number = int(month[:4]), int(month[5:])
    month_index = year * 12 + month_number - 1 + offset
    return f"{month_index // 12:04d}-{month_index % 12 + 1:02d}"


def _month_span_count(start_month: str, end_month: str) -> int:
    start_year, start_number = int(start_month[:4]), int(start_month[5:])
    end_year, end_number = int(end_month[:4]), int(end_month[5:])
    return (end_year - start_year) * 12 + (end_number - start_number) + 1


def _month_start_et(month: str) -> str:
    return f"{month}-01T00:00:00-05:00"


def _exclusive_month_start_et(month: str) -> str:
    return f"{_add_months(month, 1)}-01T00:00:00-05:00"


def _rolling_fold_dataset_splits(start_month: str, end_month: str) -> tuple[dict[str, Any], ...]:
    """Return the accepted chronological 4/1/1 split contract for a six-month fold."""

    if _month_span_count(start_month, end_month) != ROLLING_FOLD_SIZE_MONTHS:
        return ()
    splits: list[dict[str, Any]] = []
    offset = 0
    for split_order, (split_name, month_count) in enumerate(ROLLING_FOLD_SPLIT_MONTHS):
        split_start = _add_months(start_month, offset)
        split_end = _add_months(split_start, month_count - 1)
        splits.append(
            {
                "split_name": split_name,
                "split_order": split_order,
                "split_start_month": split_start,
                "split_end_month": split_end,
                "split_months": month_count,
                "split_start_time": _month_start_et(split_start),
                "split_end_time": _exclusive_month_start_et(split_end),
                "split_policy": "chronological_rolling_fold_4_1_1",
            }
        )
        offset += month_count
    return tuple(splits)


def _generation_command_for_dataset_split(command: list[str], split: Mapping[str, Any]) -> list[str]:
    split_name = str(split["split_name"])
    replacements = {
        "${START_MONTH_START_ET}": str(split["split_start_time"]),
        "${END_MONTH_EXCLUSIVE_START_ET}": str(split["split_end_time"]),
        "${START_MONTH}": f"{split['split_start_month']}_{split_name}",
        "${END_MONTH}": str(split["split_end_month"]),
    }
    resolved: list[str] = [f"TRADING_MODEL_DATASET_SPLIT_NAME={split_name}", f"TRADING_MODEL_DATASET_SPLIT_POLICY={split['split_policy']}"]
    for token in command:
        text = token
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        resolved.append(text)
    return resolved


def _model_two_target_local_feed_blockers(
    *,
    start_month: str,
    end_month: str,
    selected_target_symbol: str | None,
    trading_storage_root: Path,
) -> tuple[str, ...]:
    target = _normalize_selected_target_symbol(selected_target_symbol)
    if target is None:
        return ()
    from .layer_three_target_state import discover_layer_two_feed_artifacts

    month = start_month
    while month <= end_month:
        refs = discover_layer_two_feed_artifacts(start_month=month, trading_storage_root=trading_storage_root, symbols=(target,))
        if not refs:
            return (MODEL_TWO_TARGET_LOCAL_FEED_ARTIFACTS_BLOCKER,)
        month = _next_month(month)
    return ()


def _build_layer_workflow(
    meta: dict[str, Any],
    *,
    layer_one_task_key_count: int,
    layer_two_task_key_count: int,
    start_month: str,
    end_month: str,
    selected_target_symbol: str | None,
    foundation_catch_up_only: bool,
    model_three_event_observation_blockers: tuple[str, ...],
    model_two_target_local_feed_blockers: tuple[str, ...],
    target_option_overlay_required: bool,
) -> LayerWorkflow:
    layer = int(meta["layer"])
    slug = str(meta["slug"])
    key = layer_key(layer, slug)
    generate = model_script(layer, slug, "generate")
    evaluate = model_script(layer, slug, "evaluate")
    review = model_script(layer, slug, "review")
    feature = feature_command(meta.get("feature_cli"), selected_target_symbol=selected_target_symbol)
    maintenance = maintenance_command(layer, slug)
    dataset_unit = _dataset_unit_for_layer(
        layer=layer,
        start_month=start_month,
        end_month=end_month,
        selected_target_symbol=selected_target_symbol,
    )
    generate = _target_scoped_generation_command(generate, layer=layer, selected_target_symbol=selected_target_symbol)
    input_dataset_unit = _input_dataset_unit_for_layer(
        layer=layer,
        start_month=start_month,
        end_month=end_month,
        selected_target_symbol=selected_target_symbol,
    )

    if layer == 1:
        acquisition_status, acquisition_blockers, acquisition_gate = _stage_status_for_provider_acquisition(
            task_key_count=layer_one_task_key_count,
            required_count=LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS,
            preparation_blocker="layer_01_task_key_preparation",
        )
    elif layer == 2:
        acquisition_status = "blocked" if model_two_target_local_feed_blockers else "ready"
        acquisition_blockers, acquisition_gate = model_two_target_local_feed_blockers, None
    elif not meta.get("input_stage") and meta.get("feature_cli") is None:
        acquisition_status, acquisition_blockers, acquisition_gate = "not_applicable", (), None
    elif layer == 3:
        acquisition_status = "blocked" if model_three_event_observation_blockers else "ready"
        acquisition_blockers, acquisition_gate = model_three_event_observation_blockers, None
    elif layer == 5:
        acquisition_blockers = (MODEL_FIVE_OPTION_CHAIN_SOURCE_BLOCKER,) if target_option_overlay_required else ()
        acquisition_status = "blocked" if acquisition_blockers else "not_applicable"
        acquisition_gate = None
    else:
        acquisition_status, acquisition_blockers, acquisition_gate = "blocked", _upstream_model_ready_blockers(
            tuple(meta["depends_on_layers"]),
            foundation_catch_up_only=foundation_catch_up_only,
        ), None

    acquisition_command = ["manager", "advance-local-input-stage", key]
    if layer == 1:
        acquisition_command = [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/dispatch_and_reconcile_provider_stage.py",
            "--start-month",
            "${START_MONTH}",
            "--end-month",
            "${END_MONTH}",
            "--model-layer",
            LAYER_ONE_MODEL_LAYER,
            "--skip-registered-failures",
            "--reject-terminal-coverage",
        ]
    elif layer == 2:
        acquisition_command = [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/materialize_layer_three_target_state_inputs.py",
            "--start-month",
            "${START_MONTH}",
            "--end-month",
            "${END_MONTH}",
            "--write",
            "--persist-sql",
        ]
        if selected_target_symbol:
            acquisition_command.extend(["--target-symbol", selected_target_symbol])
    elif layer == 3:
        acquisition_command = [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/materialize_layer_four_event_observation_inputs.py",
            "--start-month",
            "${START_MONTH}",
            "--end-month",
            "${END_MONTH}",
            "--write",
        ]
    elif acquisition_gate:
        acquisition_command = ["manager", "dispatch-approved-component-acquisition", key]

    acquisition_blockers = _with_target_blocker(
        acquisition_blockers,
        layer=layer,
        selected_target_symbol=selected_target_symbol,
        stage_type="data_acquisition",
    )

    stages: list[WorkflowStage] = []
    has_monthly_input_stage = layer in BASE_INPUT_STAGE_LAYERS
    include_input_stage = has_monthly_input_stage and (not foundation_catch_up_only or layer in FOUNDATION_CATCH_UP_LAYERS)
    if layer == 5 and include_input_stage and target_option_overlay_required:
        option_source_command = [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/prepare_option_chain_source_acquisition.py",
            "--start-month",
            "${START_MONTH}",
            "--end-month",
            "${END_MONTH}",
            "--write",
            "--persist-sql",
        ]
        if selected_target_symbol:
            option_source_command.extend(["--target-symbol", selected_target_symbol])
        option_source_blockers = _with_target_blocker(
            _upstream_model_ready_blockers(tuple(meta["depends_on_layers"]), foundation_catch_up_only=foundation_catch_up_only),
            layer=layer,
            selected_target_symbol=selected_target_symbol,
            stage_type="data_acquisition",
        )
        stages.append(
            WorkflowStage(
                stage_id=MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID,
                layer=layer,
                layer_key=key,
                stage_type="data_acquisition",
                description="Prepare shared ThetaData option_chain_state_source rows for M05 option-expression training when options apply.",
                status="blocked",
                command=option_source_command,
                dataset_unit=input_dataset_unit,
                blockers=option_source_blockers,
                safe_without_provider_calls=False,
                provider_calls_allowed=True,
            )
        )
    if include_input_stage and layer != 5:
        stages.append(
            WorkflowStage(
                stage_id=f"{key}.data_acquisition",
                layer=layer,
                layer_key=key,
                stage_type="data_acquisition",
                description=str(meta["data_surface"]),
                status=acquisition_status,
                command=acquisition_command,
                dataset_unit=input_dataset_unit,
                blockers=acquisition_blockers,
                approval_gate_required=acquisition_gate,
                safe_without_provider_calls=not (layer == 1 or acquisition_gate is not None),
                provider_calls_allowed=layer == 1,
            )
        )
        if meta.get("feature_cli") is not None:
            stages.append(
                WorkflowStage(
                    stage_id=f"{key}.feature_generation",
                    layer=layer,
                    layer_key=key,
                    stage_type="feature_generation",
                    description="Generate deterministic feature rows from materialized local inputs.",
                    status="blocked",
                    command=feature,
                    dataset_unit=dataset_unit,
                    blockers=_with_target_blocker(
                        (f"{key}.data_acquisition_complete",),
                        layer=layer,
                        selected_target_symbol=selected_target_symbol,
                        stage_type="feature_generation",
                    ),
                    safe_without_provider_calls=True,
                    provider_calls_allowed=False,
                )
            )
    elif layer == 5 and meta.get("feature_cli") is not None and not foundation_catch_up_only and target_option_overlay_required:
        stages.append(
            WorkflowStage(
                stage_id=f"{key}.feature_generation",
                layer=layer,
                layer_key=key,
                stage_type="feature_generation",
                description="Generate M05 option-expression features from shared option_chain_state_source after M04 intent.",
                status="blocked",
                command=feature,
                dataset_unit=dataset_unit,
                blockers=_with_target_blocker(
                    (
                        MODEL_FIVE_OPTION_CHAIN_SOURCE_BLOCKER,
                        *_upstream_model_ready_blockers(tuple(meta["depends_on_layers"]), foundation_catch_up_only=foundation_catch_up_only),
                    ),
                    layer=layer,
                    selected_target_symbol=selected_target_symbol,
                    stage_type="feature_generation",
                ),
                safe_without_provider_calls=True,
                provider_calls_allowed=False,
            )
        )
    if foundation_catch_up_only:
        return LayerWorkflow(
            layer=layer,
            layer_key=key,
            model_name=str(meta["model_name"]),
            depends_on_layers=tuple(meta["depends_on_layers"]),
            progression_mode=str(meta["progression_mode"]),
            candidate_axis=str(meta["candidate_axis"]),
            candidate_progression_policy=str(meta["candidate_progression_policy"]),
            dataset_unit=dataset_unit,
            data_surface=str(meta["data_surface"]),
            feature_command=feature,
            model_generate_command=generate,
            model_evaluate_command=evaluate,
            promotion_review_command=review,
            maintenance_command=maintenance,
            stages=tuple(stages),
        )

    dataset_splits = _rolling_fold_dataset_splits(start_month, end_month)
    model_generation_blockers = _upstream_model_ready_blockers(
        tuple(meta["depends_on_layers"]),
        foundation_catch_up_only=foundation_catch_up_only,
    ) + ((f"{key}.feature_or_input_ready",) if include_input_stage and layer != 5 else ())
    if layer == 5 and target_option_overlay_required:
        model_generation_blockers = model_generation_blockers + (f"{key}.feature_or_input_ready",)
    model_generation_description = (
        "Generate offline model/state-vector evidence from the accepted chronological rolling-fold split contract."
    )
    if dataset_splits:
        split_blockers = model_generation_blockers
        for split in dataset_splits:
            split_name = str(split["split_name"])
            stages.append(
                WorkflowStage(
                    stage_id=f"{key}.model_generation.{split_name}",
                    layer=layer,
                    layer_key=key,
                    stage_type="model_generation",
                    description=f"{model_generation_description} Split: {split_name}.",
                    status="blocked",
                    command=_generation_command_for_dataset_split(generate, split),
                    dataset_unit=dataset_unit,
                    blockers=_with_target_blocker(
                        split_blockers,
                        layer=layer,
                        selected_target_symbol=selected_target_symbol,
                        stage_type="model_generation",
                    ),
                    dataset_split=dict(split),
                )
            )
            split_blockers = (f"{key}.model_generation.{split_name}_complete",)
    else:
        stages.append(
            WorkflowStage(
                stage_id=f"{key}.model_generation",
                layer=layer,
                layer_key=key,
                stage_type="model_generation",
                description=model_generation_description,
                status="blocked",
                command=generate,
                dataset_unit=dataset_unit,
                blockers=("rolling_fold_4_1_1_split_required",),
            )
        )
    return LayerWorkflow(
        layer=layer,
        layer_key=key,
        model_name=str(meta["model_name"]),
        depends_on_layers=tuple(meta["depends_on_layers"]),
        progression_mode=str(meta["progression_mode"]),
        candidate_axis=str(meta["candidate_axis"]),
        candidate_progression_policy=str(meta["candidate_progression_policy"]),
        dataset_unit=dataset_unit,
        data_surface=str(meta["data_surface"]),
        feature_command=feature,
        model_generate_command=generate,
        model_evaluate_command=evaluate,
        promotion_review_command=review,
        maintenance_command=maintenance,
        stages=tuple(stages),
    )


def build_model_training_workflow_plan(
    *,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    trading_storage_root: Path | None = None,
    selected_target_symbol: str | None = None,
    foundation_catch_up_only: bool = True,
) -> ModelTrainingWorkflowPlan:
    task_key_count = count_layer_one_task_keys(storage_root, start_month=start_month)
    layer_two_task_key_count = count_layer_two_task_keys(storage_root, start_month=start_month)
    normalized_target_symbol = _normalize_selected_target_symbol(selected_target_symbol)
    resolved_trading_storage_root = _resolve_event_feed_storage_root(storage_root, trading_storage_root)
    target_option_overlay_required = _target_option_overlay_required(
        selected_target_symbol=normalized_target_symbol,
        trading_storage_root=resolved_trading_storage_root,
    )
    model_three_event_observation_blockers = _model_three_event_observation_blockers(
        start_month=start_month,
        end_month=end_month,
        trading_storage_root=resolved_trading_storage_root,
    )
    model_two_target_local_feed_blockers = _model_two_target_local_feed_blockers(
        start_month=start_month,
        end_month=end_month,
        selected_target_symbol=normalized_target_symbol,
        trading_storage_root=resolved_trading_storage_root,
    )
    layers = tuple(
        _build_layer_workflow(
            meta,
            layer_one_task_key_count=task_key_count,
            layer_two_task_key_count=layer_two_task_key_count,
            start_month=start_month,
            end_month=end_month,
            selected_target_symbol=normalized_target_symbol,
            foundation_catch_up_only=foundation_catch_up_only,
            model_three_event_observation_blockers=model_three_event_observation_blockers,
            model_two_target_local_feed_blockers=model_two_target_local_feed_blockers,
            target_option_overlay_required=target_option_overlay_required,
        )
        for meta in LAYER_METADATA
    )
    next_stage = None
    for layer in layers:
        for stage in layer.stages:
            if stage.status == "ready":
                next_stage = stage
                break
        if next_stage is not None:
            break
    return ModelTrainingWorkflowPlan(
        contract_type="manager_model_training_workflow_plan",
        start_month=start_month,
        end_month=end_month,
        selected_target_symbol=normalized_target_symbol,
        layer_count=len(layers),
        layer_one_task_key_count=task_key_count,
        layer_two_task_key_count=layer_two_task_key_count,
        layers=layers,
        next_stage=next_stage,
        foundation_catch_up_only=foundation_catch_up_only,
    )


def write_workflow_plan(plan: ModelTrainingWorkflowPlan, *, output: TextIO) -> None:
    json.dump(plan.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan the manager-owned historical six-model workflow.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--trading-storage-root", type=Path)
    parser.add_argument("--target-symbol", help="Required task-scope target symbol for M02+ six-month dataset units.")
    parser.add_argument(
        "--allow-post-foundation-model-stages",
        action="store_true",
        help="Allow model generation/evaluation/promotion stages after the M01/M03 historical substrate catch-up has been explicitly accepted.",
    )
    args = parser.parse_args(argv)
    try:
        plan = build_model_training_workflow_plan(
            start_month=args.start_month,
            end_month=args.end_month,
            storage_root=args.storage_root,
            trading_storage_root=args.trading_storage_root,
            selected_target_symbol=args.target_symbol,
            foundation_catch_up_only=not args.allow_post_foundation_model_stages,
        )
    except ValueError as exc:
        parser.error(str(exc))
    write_workflow_plan(plan, output=sys.stdout)
    return 0


__all__ = [
    "DATASET_UNIT_MONTHS",
    "DatasetUnit",
    "BASE_INPUT_STAGE_LAYERS",
    "BASE_STACK_LAYER_COUNT",
    "FOUNDATION_CATCH_UP_BLOCKER",
    "FOUNDATION_CATCH_UP_LAYERS",
    "FOLD_STACK_PROMOTION_BLOCKER",
    "MODEL_GROUP_REPLAY_COMPLETE_BLOCKER",
    "MULTI_TARGET_SYMBOL_BLOCKER",
    "MONTHLY_SUBSTRATE_LAYERS",
    "FOUNDATION_CATCH_UP_STAGE_TYPES",
    "LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS",
    "LAYER_TWO_REQUIRED_ALPACA_BAR_REQUESTS",
    "MODEL_THREE_EVENT_OBSERVATION_COVERAGE_BLOCKER",
    "MODEL_TWO_TARGET_LOCAL_FEED_ARTIFACTS_BLOCKER",
    "MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID",
    "MODEL_FIVE_OPTION_CHAIN_SOURCE_BLOCKER",
    "MODEL_SIX_EVENT_FEED_COVERAGE_BLOCKER",
    "POST_MODEL_GENERATION_REBUILD_BLOCKER",
    "LayerWorkflow",
    "ModelTrainingWorkflowPlan",
    "WorkflowStage",
    "build_model_training_workflow_plan",
    "count_alpaca_bar_task_keys",
    "count_layer_one_task_keys",
    "count_layer_two_task_keys",
    "write_workflow_plan",
]


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())
