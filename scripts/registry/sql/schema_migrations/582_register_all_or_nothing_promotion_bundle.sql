-- Make promotion acceptance all-or-nothing for one pinned Layer 1-9 bundle.

UPDATE trading_registry
SET payload = 'candidate_ref_required;evaluation_run_refs_optional;evidence_refs_optional;fold_layers_01_09_model_evaluation_complete_required;pinned_layer_01_09_bundle_required;bundle_acceptance_all_or_nothing;manager_schedules_only;evaluation_owns_benchmark_settlement_eligibility_readiness;execution_owns_shadow_cycle_activation',
    note = 'Manager prepares and schedules model promotion/evaluation/execution-review requests. Promotion review is fold-stack scoped and evaluates one pinned Layer 1-9 version bundle. Acceptance is all-or-nothing for that bundle: layer-local fold evaluation is diagnostic and supports failure attribution, but no single layer or partial substack can be promoted independently. Benchmark judgment and promotion readiness belong to trading-evaluation; live/shadow runtime active selection belongs to trading-execution.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_UNIFIED_REVIEW_POLICY';

UPDATE trading_registry
SET payload = 'pinned_layer_01_09_bundle_all_or_nothing_after_fold_evaluation_complete',
    note = 'Promotion review is not triggered by one model completing one fold. It opens only after Layer 1 through Layer 9 model_evaluation stages have completed for the same fold, then evaluates one pinned Layer 1-9 version bundle. The bundle is accepted or rejected as a whole; layer-local results remain diagnostic and cannot promote a single layer or partial substack independently.',
    updated_at = NOW()
WHERE key = 'FOLD_STACK_PROMOTION_GATE_POLICY';
