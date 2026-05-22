-- Register the evaluation-side Replay harness that calls execution runtime
-- decision builders directly.

UPDATE trading_registry
SET path = CASE
        WHEN path LIKE '%trading-execution/src/trading_execution/runtime/decisions.py%' THEN path
        ELSE path || ';trading-execution/src/trading_execution/runtime/decisions.py'
    END,
    note = note || ' The implementation now includes side-effect-free builders and validators in runtime/decisions.py.',
    updated_at = NOW()
WHERE key IN (
    'TARGET_ALLOCATION_SNAPSHOT',
    'ENTRY_DECISION',
    'POSITION_LIFECYCLE_DECISION',
    'OPTION_REEXPRESSION_DECISION',
    'FAILURE_EXPLANATION_PACKET',
    'EXECUTION_ORDER_INTENT',
    'SIMULATED_FILL_EVENT'
)
AND note NOT ILIKE '%runtime/decisions.py%';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_EVALRPLY001',
    'artifact_type',
    'EVALUATION_REPLAY_RUNTIME_DRY_RUN',
    'text',
    'evaluation_replay_runtime_dry_run',
    'trading-evaluation/docs/03_contracts.md;trading-evaluation/src/trading_evaluation/execution_runtime.py',
    'trading-evaluation;trading-execution;replay;execution_runtime_component_graph;fold_settlement',
    'sync_artifact',
    'Evaluation-side fixture-safe Replay harness that calls trading-execution runtime builders directly and returns emitted decision records, validations, and side-effect evidence. It does not own trading decisions, train models, call providers, submit broker requests, or mutate accounts.'
  )
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
