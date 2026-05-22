-- Register replay freeze receipt and executable evaluation helper scripts.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_EVALRPLFRZ001',
    'artifact_type',
    'REPLAY_DATASET_FREEZE_RECEIPT',
    'text',
    'replay_dataset_freeze_receipt',
    'trading-evaluation/docs/03_contracts.md;trading-evaluation/docs/22_replay_dataset_preparation.md;trading-evaluation/src/trading_evaluation/replay_dataset.py',
    'trading-evaluation;replay_dataset;replay_freeze;storage_snapshot;promotion_replay',
    'sync_artifact',
    'Storage-side receipt proving accepted replay dataset coverage was validated and frozen. The receipt records complete sources, accepted candidate-dependent deferred sources, and safety flags proving no provider calls, SQL mutation, model training, activation, broker execution, or account mutation occurred.'
  ),
  (
    'scr_EVALRPLFRZ001',
    'script',
    'TRADING_EVALUATION_FREEZE_REPLAY_DATASET',
    'command',
    'PYTHONPATH=src python3 scripts/evaluation/freeze_replay_dataset.py --dataset-root $REPLAY_DATASET_ROOT',
    '/root/projects/trading-evaluation/scripts/evaluation/freeze_replay_dataset.py',
    'trading-evaluation;replay_dataset;replay_freeze;storage_snapshot',
    'sync_artifact',
    'Validates accepted replay dataset coverage and freezes the storage-side manifest by writing replay_freeze_receipt.json. It performs no provider calls, SQL mutation, model training, activation, broker execution, or account mutation.'
  ),
  (
    'scr_EVALRPLY001',
    'script',
    'TRADING_EVALUATION_RUN_REPLAY_RUNTIME_DRY_RUN',
    'command',
    'PYTHONPATH=src python3 scripts/evaluation/run_replay_runtime_dry_run.py --account-sleeve-id $ACCOUNT_SLEEVE_ID --target-ref $TARGET_REF --output-path $OUTPUT_PATH',
    '/root/projects/trading-evaluation/scripts/evaluation/run_replay_runtime_dry_run.py',
    'trading-evaluation;trading-execution;replay;execution_runtime_component_graph;dry_run',
    'sync_artifact',
    'Runs one side-effect-free Replay pass through trading-execution runtime components and writes a readiness receipt. It is a smoke test, not the full 60-month replay.'
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
