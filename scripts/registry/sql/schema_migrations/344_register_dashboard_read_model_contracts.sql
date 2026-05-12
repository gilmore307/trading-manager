-- Register dashboard read-model contract names and storage placement policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_DASHRM001',
    'config',
    'DASHBOARD_READ_MODEL_STORAGE_LAYOUT_POLICY',
    'text',
    'storage/dashboard/read_models/<contract_type>/latest.json;storage/dashboard/read_models/<contract_type>/snapshots/YYYY/MM/DD/<generated_at_utc_compact>.json;storage/dashboard/schemas/<contract_type>.schema.json;storage/dashboard/index/dashboard_read_model_index.jsonl',
    'trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;trading-storage;dashboard_read_models;storage_layout;read_only_presentation',
    'sync_artifact',
    'Storage-owned physical layout policy for dashboard summaries. Dashboard reads latest/snapshot documents from storage and must not query raw component internals as primary UI inputs.'
  ),
  (
    'cfg_DASHRM002',
    'config',
    'DASHBOARD_READ_MODEL_COMMON_ENVELOPE',
    'text',
    'contract_type;contract_version;generated_at_utc;source_system;status;severity;summary;chart_payload;profile_refs;issue_refs;diagnostic_refs;lineage_refs;freshness;schema_ref',
    'trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;trading-storage;dashboard_read_models;schema_validation;owner_facing_summary',
    'sync_artifact',
    'Common envelope fields for storage-hosted dashboard summaries. Diagnostic refs are issue-focused only; raw evidence is not primary dashboard content.'
  ),
  (
    'art_DASHRM001',
    'artifact_type',
    'CURRENT_SYSTEM_STATUS_SUMMARY_V1',
    'text',
    'current_system_status_summary_v1',
    'trading-dashboard/docs/09_dashboard_read_models.md;trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;current_status;dashboard_read_model;trading-storage;latest_snapshot',
    'sync_artifact',
    'Owner-facing current status dashboard summary covering system/service/provider/scheduler/realtime/storage posture and unresolved alert counts.'
  ),
  (
    'art_DASHRM002',
    'artifact_type',
    'ALERT_EXCEPTION_SUMMARY_V1',
    'text',
    'alert_exception_summary_v1',
    'trading-dashboard/docs/09_dashboard_read_models.md;trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;alerts;exceptions;dashboard_read_model;owner_actionable_issue_queue',
    'sync_artifact',
    'Owner-facing alert and exception summary for actionable issues, severity, blocking scope, suggested next action, and issue-focused diagnostics.'
  ),
  (
    'art_DASHRM003',
    'artifact_type',
    'HISTORICAL_TASK_PROGRESS_SUMMARY_V1',
    'text',
    'historical_task_progress_summary_v1',
    'trading-dashboard/docs/09_dashboard_read_models.md;trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;historical_modeling;task_progress;dashboard_read_model;manager_summary',
    'sync_artifact',
    'Owner-facing historical modeling task progress summary over active month/window, layer/stage, ready/pending/failed counts, blockers, and next system action.'
  ),
  (
    'art_DASHRM004',
    'artifact_type',
    'REALTIME_TASK_PROGRESS_SUMMARY_V1',
    'text',
    'realtime_task_progress_summary_v1',
    'trading-dashboard/docs/09_dashboard_read_models.md;trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;realtime_trading;task_progress;dashboard_read_model;parked_shadow_paper_live_states',
    'sync_artifact',
    'Owner-facing realtime task progress summary. It must plainly distinguish parked, shadow, paper, and live states without fabricating signal/performance metrics.'
  ),
  (
    'art_DASHRM005',
    'artifact_type',
    'MODEL_LAYER_READINESS_SUMMARY_V1',
    'text',
    'model_layer_readiness_summary_v1',
    'trading-dashboard/docs/09_dashboard_read_models.md;trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;model_layers;readiness;dashboard_read_model;layers_1_8',
    'sync_artifact',
    'Owner-facing model layer readiness summary for the accepted eight-layer map, parameters, versions, metrics, blockers, and promotion posture.'
  ),
  (
    'art_DASHRM006',
    'artifact_type',
    'MODEL_PROMOTION_POSTURE_SUMMARY_V1',
    'text',
    'model_promotion_posture_summary_v1',
    'trading-dashboard/docs/09_dashboard_read_models.md;trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;model_promotion;activation_posture;dashboard_read_model;agent_decision_evidence',
    'sync_artifact',
    'Owner-facing model promotion posture summary. Dashboard reports blocked/deferred/eligible/approved/rejected/revoked/superseded posture and never activates models.'
  ),
  (
    'art_DASHRM007',
    'artifact_type',
    'REGISTRY_DICTIONARY_PROFILE_V1',
    'text',
    'registry_dictionary_profile_v1',
    'trading-dashboard/docs/09_dashboard_read_models.md;trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;registry_dictionary;field_profiles;hover_profiles;read_only_explanation',
    'sync_artifact',
    'Read-only registry dictionary and field-profile summary for dashboard explanations. It is not a registry editor or governance replacement.'
  ),
  (
    'art_DASHRM008',
    'artifact_type',
    'REALTIME_SIGNAL_SUMMARY_V1',
    'text',
    'realtime_signal_summary_v1',
    'trading-dashboard/docs/09_dashboard_read_models.md;trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;realtime_signals;dashboard_read_model;future_parked',
    'sync_artifact',
    'Parked future owner-facing realtime signal summary. Use only after realtime evidence is mature enough to avoid fabricated signal metrics.'
  ),
  (
    'art_DASHRM009',
    'artifact_type',
    'RUNTIME_DECISION_QUALITY_SUMMARY_V1',
    'text',
    'runtime_decision_quality_summary_v1',
    'trading-dashboard/docs/09_dashboard_read_models.md;trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;runtime_decision_quality;shadow_outcomes;dashboard_read_model;future_parked',
    'sync_artifact',
    'Parked future owner-facing runtime decision quality summary for matured realtime/shadow outcome labels.'
  ),
  (
    'art_DASHRM010',
    'artifact_type',
    'TRADING_PERFORMANCE_SUMMARY_V1',
    'text',
    'trading_performance_summary_v1',
    'trading-dashboard/docs/09_dashboard_read_models.md;trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;trading_performance;shadow_paper_live;dashboard_read_model;future_parked',
    'sync_artifact',
    'Parked future owner-facing trading performance summary. Shadow, paper, and live performance must remain distinct.'
  ),
  (
    'art_DASHRM011',
    'artifact_type',
    'STORAGE_LIFECYCLE_STATUS_SUMMARY_V1',
    'text',
    'storage_lifecycle_status_summary_v1',
    'trading-dashboard/docs/09_dashboard_read_models.md;trading-storage/docs/96_dashboard_read_models.md;trading-storage/docs/97_dashboard_summary_layout.md',
    'trading-dashboard;trading-storage;storage_lifecycle;dashboard_read_model;future_parked',
    'sync_artifact',
    'Parked future owner-facing storage lifecycle posture summary for disk pressure, protected-set status, latest scan, archive/delete receipts, restore status, and lifecycle alerts.'
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
