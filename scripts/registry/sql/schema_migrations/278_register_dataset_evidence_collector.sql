-- Register manager dataset evidence collector.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MDSE002',
    'artifact_type',
    'MANAGER_DATASET_EVIDENCE_V1',
    'text',
    'manager_dataset_evidence_v1',
    'trading-manager/src/trading_manager_tasks/dataset_evidence.py',
    'trading-manager;dataset_expansion;model_dataset_snapshot;model_dataset_split;model_eval_label;model_eval_run;artifact_ref_v1;ready_signal_v1',
    'sync_artifact',
    'Manager-visible dataset evidence contract summarizing per-layer dataset role coverage, sample counts, snapshot/split references, label/eval coverage, control-plane artifact/ready-signal counts, and promotion gaps for expansion planning.'
  ),
  (
    'scr_MDSE002',
    'script',
    'MANAGER_DATASET_EVIDENCE_COLLECTOR',
    'text',
    'PYTHONPATH=src python3 scripts/tasks/collect_dataset_evidence.py',
    'trading-manager/scripts/tasks/collect_dataset_evidence.py',
    'trading-manager;manager_dataset_evidence_v1;manager_dataset_expansion_plan_v1;historical_training;dataset_expansion',
    'sync_artifact',
    'Collects current SQL/control-plane dataset evidence for the expansion planner without provider calls, model activation, or broker execution.'
  ),
  (
    'cfg_MDSE002',
    'config',
    'MANAGER_DATASET_EVIDENCE_POLICY',
    'text',
    'collect_existing_snapshot_split_label_eval_artifact_ready_signal_evidence;feed_planner_without_adding_decision_rule_system;no_provider_calls;no_model_activation;no_broker_execution',
    'trading-manager/docs/100_dataset_expansion.md',
    'trading-manager;dataset_expansion;historical_training;manager_dataset_evidence_v1',
    'sync_artifact',
    'Dataset evidence collection policy: manager inventories existing evidence and feeds the existing expansion planner rather than creating a second decision-rule system.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();
