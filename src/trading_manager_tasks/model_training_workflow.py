"""Historical base-stack workflow graph.

The manager owns orchestration across the historical-modeling service. This
module defines the base trading stack progression. Layer 8 composes optional
trading-guidance/option-expression context from the Layer 7 direct-underlying
thesis. Layer 9 EventRiskGovernor governs the Layer 7 thesis directly and may
attach Layer 8 context when available.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, TextIO

from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER, load_market_regime_universe
from .request_payloads import DEFAULT_STORAGE_ROOT

StageStatus = Literal["ready", "blocked", "complete", "not_applicable"]

BASE_STACK_LAYER_COUNT = 9
BASE_INPUT_STAGE_LAYERS = (1, 2, 3, 8, 9)
LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS = 19
LAYER_TWO_REQUIRED_ALPACA_BAR_REQUESTS = 25
DATASET_UNIT_MONTHS = 6
FOUNDATION_CATCH_UP_LAYERS = (1, 2)
MONTHLY_SUBSTRATE_LAYERS = (1, 2, 3)
FOUNDATION_CATCH_UP_STAGE_TYPES = ("data_acquisition", "feature_generation")
FOUNDATION_CATCH_UP_BLOCKER = "layer_01_02_historical_catch_up_to_current_required"
POST_MODEL_GENERATION_REBUILD_BLOCKER = "post_model_generation_rebuild_required_after_layer_01_02_catch_up"
ROLLING_FOLD_TRAIN_MONTHS = 4
ROLLING_FOLD_VALIDATION_MONTHS = 1
ROLLING_FOLD_TEST_MONTHS = 1
ROLLING_FOLD_SIZE_MONTHS = ROLLING_FOLD_TRAIN_MONTHS + ROLLING_FOLD_VALIDATION_MONTHS + ROLLING_FOLD_TEST_MONTHS
PROMOTION_STAGE_TYPE = "promotion_review"


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
    foundation_catch_up_layers: tuple[int, ...] = MONTHLY_SUBSTRATE_LAYERS
    reusable_substrate_stage_types: tuple[str, ...] = FOUNDATION_CATCH_UP_STAGE_TYPES
    post_model_generation_artifacts_policy: str = "supersede_and_rebuild_after_layer_01_02_historical_catch_up"

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


LAYER_METADATA: tuple[dict[str, Any], ...] = (
    {
        "layer": 1,
        "slug": "market_regime",
        "model_name": "MarketRegimeModel",
        "depends_on_layers": (),
        "progression_mode": "background_panel_continuous",
        "candidate_axis": "six_month_window",
        "candidate_progression_policy": "complete fixed Layer 1 market/cross-asset panel for each six-month chronological unit, then continue to the next six-month unit without waiting for downstream layers",
        "data_surface": "autonomous Alpaca ETF bars acquisition plus feature_01_market_regime",
        "feature_cli": "trading-data-feature-01-market-regime",
    },
    {
        "layer": 2,
        "slug": "sector_context",
        "model_name": "SectorContextModel",
        "depends_on_layers": (1,),
        "progression_mode": "sector_panel_continuous",
        "candidate_axis": "six_month_window;sector_or_industry_symbol",
        "candidate_progression_policy": "complete fixed Layer 2 sector/industry panel for each six-month chronological unit once Layer 1 context exists, then continue forward without waiting for target-chain layers",
        "data_surface": "autonomous Alpaca sector/industry ETF bars acquisition plus feature_02_sector_context over materialized market/sector inputs",
        "feature_cli": "trading-data-feature-02-sector-context",
    },
    {
        "layer": 3,
        "slug": "target_state_vector",
        "model_name": "TargetStateVectorModel",
        "depends_on_layers": (1, 2),
        "progression_mode": "target_major_serial_chain",
        "candidate_axis": "target_symbol;six_month_window;target_candidate_id",
        "candidate_progression_policy": "for one selected target symbol and one six-month unit, complete the downstream target chain in order before admitting the next target unless a reviewed coverage exception is recorded",
        "data_surface": "target candidate/source_03 inputs plus feature_03_target_state_vector",
        "feature_cli": "trading-data-feature-03-target-state-vector",
    },
    {
        "layer": 4,
        "slug": "event_failure_risk",
        "model_name": "EventFailureRiskModel",
        "depends_on_layers": (3,),
        "progression_mode": "target_major_serial_chain",
        "candidate_axis": "target_symbol;six_month_window;target_candidate_id;event_failure_context_id",
        "candidate_progression_policy": "continue the active target candidate chain after Layer 3 target state is ready; only reviewed event/strategy-failure evidence can condition this layer",
        "data_surface": "agent-reviewed event/strategy-failure evidence plus target state; no dedicated trading-data source and no raw event alpha requirement",
        "feature_cli": None,
    },
    {
        "layer": 5,
        "slug": "alpha_confidence",
        "model_name": "AlphaConfidenceModel",
        "depends_on_layers": (4,),
        "progression_mode": "target_major_serial_chain",
        "candidate_axis": "target_symbol;six_month_window;target_candidate_id;alpha_context_id",
        "candidate_progression_policy": "continue the active target candidate chain after Layer 4 event failure risk is ready; event discovery remains separate from base alpha confidence",
        "data_surface": "target context state, event_failure_risk_vector, and labels; no dedicated trading-data source and no raw event-feed requirement",
        "feature_cli": None,
    },
    {
        "layer": 6,
        "slug": "position_projection",
        "model_name": "PositionProjectionModel",
        "depends_on_layers": (5,),
        "progression_mode": "target_major_serial_chain",
        "candidate_axis": "target_symbol;six_month_window;target_candidate_id;position_context_id",
        "candidate_progression_policy": "continue the active target candidate chain after Layer 5 alpha confidence is ready",
        "data_surface": "alpha confidence plus position/risk/cost context; no dedicated trading-data source",
        "feature_cli": None,
    },
    {
        "layer": 7,
        "slug": "underlying_action",
        "model_name": "UnderlyingActionModel",
        "depends_on_layers": (6,),
        "progression_mode": "target_major_serial_chain",
        "candidate_axis": "target_symbol;six_month_window;target_candidate_id;underlying_action_context_id",
        "candidate_progression_policy": "continue the active target candidate chain after Layer 6 position projection is ready",
        "data_surface": "model/control-plane underlying-action context; no dedicated trading-data source",
        "feature_cli": None,
    },
    {
        "layer": 8,
        "slug": "option_expression",
        "model_name": "TradingGuidanceModel / OptionExpressionModel",
        "depends_on_layers": (7,),
        "progression_mode": "optional_trading_guidance_after_underlying_action",
        "candidate_axis": "target_symbol;six_month_window;target_candidate_id;option_contract_bucket",
        "candidate_progression_policy": "finish the active base target chain through optional Layer 8 trading guidance / option expression; crypto/direct-underlying-only routes do not require option refs",
        "data_surface": "agent-reviewed option-expression gate review; provider-backed option-expression sources only when active base Layer 7 target chains require them plus feature_08_option_expression",
        "feature_cli": "trading-data-feature-08-option-expression",
    },
    {
        "layer": 9,
        "slug": "event_risk_governor",
        "model_name": "EventRiskGovernor",
        "depends_on_layers": (7,),
        "progression_mode": "event_risk_governance_over_underlying_thesis",
        "candidate_axis": "target_symbol;six_month_window;target_candidate_id;event_risk_context_id",
        "candidate_progression_policy": "review the Layer 7 direct-underlying/spot thesis against accepted event-risk evidence; Layer 8 guidance/expression context is optional when available",
        "data_surface": "source_09_event_risk_governor plus feature_09_event_risk_governor from reviewed local event/feed evidence; no broker/account mutation",
        "feature_cli": "trading-data-feature-09-event-risk-governor",
    },
)

def layer_key(layer: int, slug: str) -> str:
    return f"layer_{layer:02d}_{slug}"


REVIEW_SCRIPT_NAMES: dict[int, str] = {
    1: "review_market_regime_promotion.py",
    2: "review_sector_context_promotion.py",
    3: "review_target_state_vector_promotion.py",
    4: "review_event_failure_risk_promotion.py",
    5: "review_alpha_confidence_promotion.py",
    6: "review_position_projection_promotion.py",
    7: "review_underlying_action_promotion.py",
    8: "review_option_expression_promotion.py",
    9: "review_event_risk_governor_promotion.py",
}


def model_script(layer: int, slug: str, verb: str, *, physical_layer: int | None = None, physical_slug: str | None = None) -> list[str]:
    physical_layer = physical_layer or layer
    physical_slug = physical_slug or slug
    script_name = REVIEW_SCRIPT_NAMES[physical_layer] if verb == "review" else f"{verb}_model_{physical_layer:02d}_{physical_slug}.py"
    physical_model_key = f"model_{physical_layer:02d}_{physical_slug}"
    command = [
        "PYTHONPATH=/root/projects/trading-model/src",
        "python3",
        f"/root/projects/trading-model/scripts/models/{physical_model_key}/{script_name}",
    ]
    if layer in {1, 2} and verb == "generate":
        command.extend([
            "--source-start",
            "${START_MONTH_START_ET}",
            "--source-end",
            "${END_MONTH_EXCLUSIVE_START_ET}",
        ])
    if layer in {3, 4, 5, 6, 7, 8, 9} and verb == "generate":
        command.extend([
            "--from-database",
            "--source-start",
            "${START_MONTH_START_ET}",
            "--source-end",
            "${END_MONTH_EXCLUSIVE_START_ET}",
            "--output-jsonl" if layer in {4, 5, 6, 7, 8, 9} else "--output",
            f"/root/projects/trading-model/storage/runtime/{physical_model_key}/model_rows_${{START_MONTH}}.jsonl",
        ])
    if layer in {1, 2} and verb == "evaluate":
        command.extend([
            "--from-database",
            "--output-json",
            f"/root/projects/trading-model/storage/runtime/{physical_model_key}/evaluation_summary_${{START_MONTH}}.json",
        ])
    if layer in {3, 4, 5, 6, 7, 8, 9} and verb == "evaluate":
        command.extend([
            "--from-database",
            "--source-start",
            "${START_MONTH_START_ET}",
            "--source-end",
            "${END_MONTH_EXCLUSIVE_START_ET}",
            "--output-json",
            f"/root/projects/trading-model/storage/runtime/{physical_model_key}/evaluation_summary_${{START_MONTH}}.json",
        ])
        if layer in {4, 5, 6, 7, 8, 9}:
            command.extend(["--evidence-source", "database_rows_fixture_outcomes"])
    if layer in {1, 2} and verb == "review":
        command.extend([
            "--evaluation-summary-json",
            f"/root/projects/trading-model/storage/runtime/{physical_model_key}/evaluation_summary_${{START_MONTH}}.json",
            "--local-fallback-review",
        ])
    if layer == 3 and verb == "review":
        command.extend([
            "--evaluation-summary-json",
            f"/root/projects/trading-model/storage/runtime/{physical_model_key}/evaluation_summary_${{START_MONTH}}.json",
            "--evidence-source",
            "real_database_evaluation",
            "--local-fallback-review",
        ])
    if layer in {4, 5, 6, 7, 8, 9} and verb == "review":
        command.extend([
            "--evaluation-summary-json",
            f"/root/projects/trading-model/storage/runtime/{physical_model_key}/evaluation_summary_${{START_MONTH}}.json",
            "--output-json",
            f"/root/projects/trading-model/storage/runtime/{physical_model_key}/promotion_review_${{START_MONTH}}.json",
        ])
    return command


FEATURE_MODULES: dict[str, str] = {
    "trading-data-feature-01-market-regime": "data_feature.feature_01_market_regime.from_feed_artifacts",
    "trading-data-feature-02-sector-context": "data_feature.feature_02_sector_context.from_feed_artifacts",
    "trading-data-feature-03-target-state-vector": "data_feature.feature_03_target_state_vector",
    "trading-data-feature-09-event-risk-governor": "data_feature.feature_09_event_risk_governor",
    "trading-data-feature-08-option-expression": "data_feature.feature_08_option_expression",
}


def feature_command(feature_cli: str | None) -> list[str]:
    if feature_cli is None:
        return ["manager-internal", "no-dedicated-trading-data-feature-stage"]
    if feature_cli == "trading-data-feature-08-option-expression":
        return [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/execute_layer_eight_option_feature_generation.py",
            "--start-month",
            "${START_MONTH}",
            "--end-month",
            "${END_MONTH}",
        ]
    command = ["PYTHONPATH=/root/projects/trading-data/src", "python3", "-m", FEATURE_MODULES[feature_cli]]
    if feature_cli in {"trading-data-feature-01-market-regime", "trading-data-feature-02-sector-context"}:
        command.extend(["--month", "${START_MONTH}"])
    if feature_cli in {"trading-data-feature-03-target-state-vector", "trading-data-feature-09-event-risk-governor"}:
        command.extend([
            "--source-start",
            "${START_MONTH_START_ET}",
            "--source-end",
            "${END_MONTH_EXCLUSIVE_START_ET}",
            "--run-id",
            f"{FEATURE_MODULES[feature_cli].split('.')[-1]}_${{START_MONTH}}",
        ])
    return command


def maintenance_command(layer: int, slug: str, *, physical_layer: int | None = None, physical_slug: str | None = None) -> list[str]:
    physical_layer = physical_layer or layer
    physical_slug = physical_slug or slug
    physical_model_key = f"model_{physical_layer:02d}_{physical_slug}"
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
    if layer in {1, 2}:
        return DatasetUnit(
            unit_kind="six_month_panel",
            unit_months=DATASET_UNIT_MONTHS,
            start_month=start_month,
            end_month=end_month,
            target_symbol=None,
            target_required=False,
            description=f"Layer {layer} dataset unit: fixed panel over one six-month window; no single target symbol applies.",
        )
    target = selected_target_symbol.strip().upper() if selected_target_symbol else None
    target_text = target if target else "UNSELECTED_TARGET"
    return DatasetUnit(
        unit_kind="target_symbol_six_month",
        unit_months=DATASET_UNIT_MONTHS,
        start_month=start_month,
        end_month=end_month,
        target_symbol=target,
        target_required=True,
        description=f"Layer {layer} dataset unit: target {target_text} over one six-month window.",
    )


def _with_target_blocker(blockers: tuple[str, ...], *, layer: int, selected_target_symbol: str | None) -> tuple[str, ...]:
    if layer >= 3 and not (selected_target_symbol and selected_target_symbol.strip()):
        return ("selected_target_symbol_required",) + blockers
    return blockers


def _build_layer_workflow(
    meta: dict[str, Any],
    *,
    layer_one_task_key_count: int,
    layer_two_task_key_count: int,
    start_month: str,
    end_month: str,
    selected_target_symbol: str | None,
    foundation_catch_up_only: bool,
) -> LayerWorkflow:
    layer = int(meta["layer"])
    slug = str(meta["slug"])
    key = layer_key(layer, slug)
    physical_layer = int(meta.get("physical_layer", layer))
    physical_slug = str(meta.get("physical_slug", slug))
    generate = model_script(layer, slug, "generate", physical_layer=physical_layer, physical_slug=physical_slug)
    evaluate = model_script(layer, slug, "evaluate", physical_layer=physical_layer, physical_slug=physical_slug)
    review = model_script(layer, slug, "review", physical_layer=physical_layer, physical_slug=physical_slug)
    feature = feature_command(meta.get("feature_cli"))
    maintenance = maintenance_command(layer, slug, physical_layer=physical_layer, physical_slug=physical_slug)
    dataset_unit = _dataset_unit_for_layer(
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
        acquisition_status, acquisition_blockers, acquisition_gate = _stage_status_for_provider_acquisition(
            task_key_count=layer_two_task_key_count,
            required_count=LAYER_TWO_REQUIRED_ALPACA_BAR_REQUESTS,
            preparation_blocker="layer_02_task_key_preparation",
        )
    elif meta.get("feature_cli") is None:
        acquisition_status, acquisition_blockers, acquisition_gate = "not_applicable", (), None
    else:
        acquisition_status, acquisition_blockers, acquisition_gate = "blocked", tuple(
            f"upstream_layer_{dep:02d}_complete" for dep in meta["depends_on_layers"]
        ), None

    acquisition_command = ["manager", "advance-local-input-stage", key]
    if layer in {1, 2}:
        acquisition_command = [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/dispatch_and_reconcile_provider_stage.py",
            "--start-month",
            "${START_MONTH}",
            "--end-month",
            "${END_MONTH}",
            "--model-layer",
            key,
            "--skip-registered-failures",
            "--reject-terminal-coverage",
        ]
    elif layer == 3:
        acquisition_command = [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/materialize_layer_three_target_state_inputs.py",
            "--start-month",
            "${START_MONTH}",
            "--end-month",
            "${END_MONTH}",
            "--write",
        ]
    elif layer == 8:
        acquisition_command = [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/review_layer_eight_option_expression_gate.py",
            "--start-month",
            "${START_MONTH}",
            "--end-month",
            "${END_MONTH}",
            "--write",
        ]
    elif layer == 9:
        acquisition_command = [
            "PYTHONPATH=src",
            "python3",
            "scripts/tasks/materialize_layer_nine_event_risk_governor_inputs.py",
            "--start-month",
            "${START_MONTH}",
            "--end-month",
            "${END_MONTH}",
            "--write",
        ]
    elif acquisition_gate:
        acquisition_command = ["manager", "dispatch-approved-component-acquisition", key]

    acquisition_blockers = _with_target_blocker(acquisition_blockers, layer=layer, selected_target_symbol=selected_target_symbol)

    stages: list[WorkflowStage] = []
    has_monthly_input_stage = layer in BASE_INPUT_STAGE_LAYERS
    include_input_stage = has_monthly_input_stage and (not foundation_catch_up_only or layer in MONTHLY_SUBSTRATE_LAYERS)
    if include_input_stage:
        stages.append(
            WorkflowStage(
                stage_id=f"{key}.data_acquisition",
                layer=layer,
                layer_key=key,
                stage_type="data_acquisition",
                description=str(meta["data_surface"]),
                status=acquisition_status,
                command=acquisition_command,
                dataset_unit=dataset_unit,
                blockers=acquisition_blockers,
                approval_gate_required=acquisition_gate,
                safe_without_provider_calls=not (layer in {1, 2} or acquisition_gate is not None),
                provider_calls_allowed=layer in {1, 2},
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
                    ),
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

    for stage_type, command, description, blockers in (
        (
            "model_generation",
            generate,
            "Generate offline model/state-vector rows from a complete frozen rolling-fold train manifest, never from one month alone.",
            tuple(f"upstream_layer_{dep:02d}_complete" for dep in meta["depends_on_layers"])
            + ((f"{key}.feature_or_input_ready",) if include_input_stage else ()),
        ),
        (
            "model_evaluation",
            evaluate,
            "Evaluate generated model rows against rolling-fold validation/test labels and baselines without activation.",
            (f"{key}.model_generation_complete",),
        ),
        (
            PROMOTION_STAGE_TYPE,
            review,
            "Run the complete Promotion Review task: evidence packet, gates, baseline comparison, split stability, leakage/calibration/test report, agent decision, and durable decision write.",
            (f"{key}.model_evaluation_complete",),
        ),
        (
            "maintenance",
            maintenance,
            "Refresh manager review/maintenance surfaces and receipts for this layer.",
            (f"{key}.{PROMOTION_STAGE_TYPE}_complete",),
        ),
    ):
        stage_blockers = blockers
        if foundation_catch_up_only:
            if layer in FOUNDATION_CATCH_UP_LAYERS:
                stage_blockers = (POST_MODEL_GENERATION_REBUILD_BLOCKER,) + stage_blockers
            elif layer >= 3:
                stage_blockers = (FOUNDATION_CATCH_UP_BLOCKER,) + stage_blockers
        stages.append(
            WorkflowStage(
                stage_id=f"{key}.{stage_type}",
                layer=layer,
                layer_key=key,
                stage_type=stage_type,
                description=description,
                status="blocked",
                command=command,
                dataset_unit=dataset_unit,
                blockers=_with_target_blocker(stage_blockers, layer=layer, selected_target_symbol=selected_target_symbol),
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
    selected_target_symbol: str | None = None,
    foundation_catch_up_only: bool = True,
) -> ModelTrainingWorkflowPlan:
    task_key_count = count_layer_one_task_keys(storage_root, start_month=start_month)
    layer_two_task_key_count = count_layer_two_task_keys(storage_root, start_month=start_month)
    layers = tuple(
        _build_layer_workflow(
            meta,
            layer_one_task_key_count=task_key_count,
            layer_two_task_key_count=layer_two_task_key_count,
            start_month=start_month,
            end_month=end_month,
            selected_target_symbol=selected_target_symbol,
            foundation_catch_up_only=foundation_catch_up_only,
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
        selected_target_symbol=selected_target_symbol.strip().upper() if selected_target_symbol else None,
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
    parser = argparse.ArgumentParser(description="Plan the manager-owned historical base-stack workflow.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--target-symbol", help="Required task-scope target symbol for Layer 3+ six-month dataset units.")
    parser.add_argument(
        "--allow-post-foundation-model-stages",
        action="store_true",
        help="Allow model generation/evaluation/promotion stages after the Layer 1/2 historical substrate catch-up has been explicitly accepted.",
    )
    args = parser.parse_args(argv)
    write_workflow_plan(
        build_model_training_workflow_plan(
            start_month=args.start_month,
            end_month=args.end_month,
            storage_root=args.storage_root,
            selected_target_symbol=args.target_symbol,
            foundation_catch_up_only=not args.allow_post_foundation_model_stages,
        ),
        output=sys.stdout,
    )
    return 0


__all__ = [
    "DATASET_UNIT_MONTHS",
    "DatasetUnit",
    "BASE_INPUT_STAGE_LAYERS",
    "BASE_STACK_LAYER_COUNT",
    "FOUNDATION_CATCH_UP_BLOCKER",
    "FOUNDATION_CATCH_UP_LAYERS",
    "MONTHLY_SUBSTRATE_LAYERS",
    "FOUNDATION_CATCH_UP_STAGE_TYPES",
    "LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS",
    "LAYER_TWO_REQUIRED_ALPACA_BAR_REQUESTS",
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
