-- Correct target position-scaling capacity ownership: C05 evaluates final
-- capacity after C04/expression and risk-cap evidence; C03 does not inspect
-- option contract cost or final target buying-power capacity.

UPDATE trading_registry
SET applies_to = 'component_05_order_intent;execution_order_intent;sizing_plan;target_position_scaling_capacity',
    note = 'Accepted execution policy for target-level position-scaling capacity. C05 compares target-allocated buying power with estimated unit/contract cost after option-expression and risk-cap evidence are available. If the target can afford fewer than the minimum advanced-management units, C05 records single_allocation_no_advanced_scaling and blocks tactical add/reduce order-intent construction. C03 does not inspect option contract cost or final target buying-power capacity. Protective stops, exits, and risk-driven reductions remain allowed.',
    updated_at = NOW()
WHERE key = 'TARGET_POSITION_SCALING_CAPACITY_POLICY';

UPDATE trading_registry
SET applies_to = 'execution_order_intent;sizing_plan;component_05_order_intent',
    note = 'C05 sizing_plan field recording target-allocated buying power, estimated unit cost, affordable unit count, minimum advanced-management units, and whether advanced tranche management is allowed. C03 does not own or emit this field.',
    updated_at = NOW()
WHERE key = 'TARGET_POSITION_SCALING_CAPACITY';

UPDATE trading_registry
SET note = 'C03 Lifecycle manages already-open positions in underlying-thesis terms. It decides hold, add, reduce, stop, exit, or take-profit from model stops, thesis invalidation, alpha, event risk, dynamic policy, position projection, and underlying action. Option contracts are expression translation owned by C04. Fixed option mark-to-market loss percentages are not ordinary lifecycle stops. C03 does not run fee, PDT, day-trade, churn, option-contract-cost, final buying-power-capacity, or final sizing formulas; every non-hold action must carry explicit reason evidence. Add/reduce decisions may include risk-based tranche management and thesis-aware high-sell/low-buy exposure adjustment only when trained M07/M08 evidence supports them. Live submission requires C06 agent final review.',
    updated_at = NOW()
WHERE key = 'C03_LIFECYCLE_UNDERLYING_REVIEW_POLICY';

UPDATE trading_registry
SET note = 'Accepted policy for staged exposure management. For each selected training target, M07/M08 train dense eligible minute sequences, including ordinary no-change, maintain, and no-trade minutes; they must not train only action-triggered minutes. The exclusion is only against all-market every-listed-symbol discovery scans, which belong upstream. M07 trains target exposure and position-gap utility, including price-location and risk evidence. M08 owns tranche planning, risk-based add/reduce, and thesis-aware high-sell/low-buy style exposure adjustment. C03 may use those trained model outputs for underlying lifecycle add/reduce evidence without knowing final option cost. C05 records target position-scaling capacity and constructs or blocks the current tranche order intent. C06 validates/submits and must not change quantity. This is not an ad hoc scalping layer.',
    updated_at = NOW()
WHERE key = 'TRANCHE_EXPOSURE_MANAGEMENT_POLICY';
