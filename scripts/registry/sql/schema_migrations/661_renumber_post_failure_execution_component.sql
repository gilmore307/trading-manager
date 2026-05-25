-- Move post-failure review behind the normal order path.

UPDATE trading_registry
SET applies_to = 'trading-execution;component_05_order_intent;live;replay',
    updated_at = NOW()
WHERE key = 'EXECUTION_ORDER_INTENT';

UPDATE trading_registry
SET applies_to = 'trading-execution;component_07_failure_review;layer_10_event_risk_governor;live;replay',
    note = 'Execution runtime contract produced only after observed model or trade failure. C07 Failure Review calls Layer 10 to link failure evidence to possible unscreened events and emit Layer 4 feedback candidates. The implementation includes side-effect-free builders and validators in runtime/decisions.py.',
    updated_at = NOW()
WHERE key = 'FAILURE_EXPLANATION_PACKET';

UPDATE trading_registry
SET applies_to = 'trading-execution;component_06_execution_gate;replay;fill_simulator',
    updated_at = NOW()
WHERE key = 'SIMULATED_FILL_EVENT';

UPDATE trading_registry
SET applies_to = 'component_02_entry;entry_decision;component_04_option_review;component_05_order_intent',
    note = 'C02 Entry consumes C01 watch targets and decides only whether the underlying has a suitable entry thesis. It emits suitable, deferred, or rejected with entry direction, entry zone, target/take-profit, model invalidation, hard stop, horizon, and suitability score. C02 does not check account balance, choose option versus stock expression, select contracts, size positions, build orders, or directly authorize C05 order intents; suitable entries route to C04 expression review.',
    updated_at = NOW()
WHERE key = 'C02_ENTRY_THESIS_POLICY';

UPDATE trading_registry
SET applies_to = 'component_03_lifecycle;position_lifecycle_decision;component_04_option_review;component_05_order_intent;model_04_event_failure_risk;model_05_alpha_confidence;model_06_dynamic_risk_policy;model_07_position_projection;model_08_underlying_action',
    note = 'C03 Lifecycle manages already-open positions in underlying-thesis terms. It decides hold, add, reduce, stop, exit, or take-profit from model stops, thesis invalidation, alpha, event risk, dynamic policy, position projection, and underlying action. Option contracts are expression translation owned by C04. Fixed option mark-to-market loss percentages are not ordinary lifecycle stops. C03 does not run fee, PDT, day-trade, or churn formulas; every non-hold action must carry explicit reason evidence. Add decisions must respect C01/M07 sector-opportunity and portfolio constraints, and add/reduce churn must be justified by model evidence and thesis state rather than short-term noise. Live submission requires C06 agent final review.',
    updated_at = NOW()
WHERE key = 'C03_LIFECYCLE_UNDERLYING_REVIEW_POLICY';

UPDATE trading_registry
SET applies_to = 'component_04_option_review;option_reexpression_decision;entry_decision;position_lifecycle_decision;component_05_order_intent;model_09_option_expression;option_expression_plan;underlying_only_expression;no_option_expression',
    updated_at = NOW()
WHERE key = 'C04_OPTION_EXPRESSION_REVIEW_POLICY';

UPDATE trading_registry
SET applies_to = 'component_06_execution_gate;execution_order_intent;broker_order_request;agent_final_review;live_submission_gate',
    note = 'C06 Execution Gate requires an approved Codex CLI final review before any live broker submission for open, add, reduce, exit, stop, take-profit, option roll, or stock fallback orders. The review is a missed-event guard: it checks whether current target, sector, macro, regulatory, filing, analyst, halt, earnings, or option-market events are absent from upstream C02/C03/C04/M10 evidence. It does not re-run ordinary sizing, fee, spread, churn, or technical-thesis calculations. Broker/regulatory hard blocks still reject outright.',
    updated_at = NOW()
WHERE key = 'EXECUTION_AGENT_FINAL_REVIEW_POLICY';

UPDATE trading_registry
SET payload = 'C01 Intake=component_01_intake;C02 Entry=component_02_entry;C03 Lifecycle=component_03_lifecycle;C04 Option Review=component_04_option_review;C05 Order Intent=component_05_order_intent;C06 Execution Gate=component_06_execution_gate;C07 Failure Review=component_07_failure_review',
    note = 'Accepted concise numbered intraday execution component sequence. The normal live/replay order path is C01 Intake, C02 Entry, C03 Lifecycle, C04 Option Review, C05 Order Intent, and C06 Execution Gate. C07 Failure Review is a post-failure branch only; it is not a normal pre-order step. component_id values follow the model-aligned physical naming pattern component_01_* through component_07_*.',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_COMPONENT_SEQUENCE';

UPDATE trading_registry
SET applies_to = 'trade_risk_cap;component_03_lifecycle;component_04_option_review;component_06_execution_gate;model_08_underlying_action;model_09_option_expression;high_risk_options_account',
    updated_at = NOW()
WHERE key = 'UNDERLYING_THESIS_STOP_POLICY';
