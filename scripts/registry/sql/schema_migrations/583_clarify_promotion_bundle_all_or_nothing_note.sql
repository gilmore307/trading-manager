-- Preserve explicit all-or-nothing wording in the active promotion bundle policy note.

UPDATE trading_registry
SET note = 'Promotion review is not triggered by one model completing one fold. It opens only after Layer 1 through Layer 9 model_evaluation stages have completed for the same fold, then evaluates one pinned Layer 1-9 version bundle. Acceptance is all-or-nothing: the bundle is accepted or rejected as a whole; layer-local results remain diagnostic and cannot promote a single layer or partial substack independently.',
    updated_at = NOW()
WHERE key = 'FOLD_STACK_PROMOTION_GATE_POLICY';
