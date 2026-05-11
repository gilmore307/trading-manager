-- Register manager realtime shadow handoff receipt/control-plane surface.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_MRTD001',
    'term',
    'MANAGER_REALTIME_SHADOW_HANDOFF_VALIDATION',
    'text',
    'manager_realtime_shadow_handoff_validation_v1',
    'trading-manager/src/trading_manager_tasks/realtime_shadow_handoff.py',
    'trading-manager;trading-execution;trading-model;execution_model_decision_input_snapshot_v1;model_realtime_decision_route_plan_v1;validation;no_model_activation;no_broker_calls',
    'sync_artifact',
    'Manager-side validation for paired realtime execution decision-input snapshots and model realtime route plans. It checks ids, timing refs, Layer 1-8 overlap, readiness, and forbidden actions without provider calls, model activation, order construction, persistence, or account mutation.'
  ),
  (
    'trm_MRTD002',
    'term',
    'MANAGER_REALTIME_SHADOW_HANDOFF_RECEIPT',
    'text',
    'manager_realtime_shadow_handoff_receipt_v1',
    'trading-manager/src/trading_manager_tasks/realtime_shadow_handoff.py',
    'trading-manager;component_completion_receipt_v1;run_manifest_v1;artifact_ref_v1;ready_signal_v1;realtime_shadow_decision_handoff;no_provider_calls',
    'sync_artifact',
    'Standard component completion receipt shape for realtime shadow decision handoffs. It records execution input refs, model route-plan refs, validation refs, and zero-call/zero-mutation safety facts before optional control-plane persistence.'
  ),
  (
    'trm_MRTD003',
    'term',
    'MANAGER_REALTIME_SHADOW_HANDOFF_CONTROL_PLANE_BUNDLE',
    'text',
    'manager_realtime_shadow_handoff_control_plane_bundle_v1',
    'trading-manager/src/trading_manager_tasks/realtime_shadow_handoff.py',
    'trading-manager;manager_control_plane;run_manifest_v1;artifact_ref_v1;ready_signal_v1;task_summary;shadow_monitoring;fixture_replay',
    'sync_artifact',
    'Bundle containing a realtime shadow handoff receipt plus normalized manager run/artifact/ready rows. It is side-effect-free by default and makes execution->model shadow progress visible to task-summary consumers once persisted through the generic receipt path.'
  ),
  (
    'scr_MRTD001',
    'script',
    'MANAGER_REALTIME_SHADOW_HANDOFF_RECORD',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/record_realtime_shadow_handoff.py --decision-input ${DECISION_INPUT_JSON} --route-plan ${ROUTE_PLAN_JSON}',
    'trading-manager/scripts/tasks/record_realtime_shadow_handoff.py',
    'trading-manager;manager_realtime_shadow_handoff_control_plane_bundle_v1;execution_model_decision_input_snapshot_v1;model_realtime_decision_route_plan_v1;no_persistence_by_default',
    'sync_artifact',
    'Builds manager-visible realtime shadow handoff validation, receipt, and normalized run/artifact/ready rows without provider calls, model activation, broker calls, order construction, persistence, or account mutation.'
  ),
  (
    'cfg_MRTD001',
    'config',
    'MANAGER_REALTIME_SHADOW_HANDOFF_POLICY',
    'text',
    'execution_input_and_model_route_plan_required;layer_1_8_coverage_required;ready_signal_kind_realtime_shadow_decision_handoff_ready;fixture_or_shadow_only;generic_receipt_persistence_requires_reviewed_receipt_uri;no_provider_calls;no_model_activation;no_order_authority',
    'trading-manager/docs/95_task_system.md',
    'trading-manager;realtime_shadow_decision_handoff;manager_control_plane;approval_gate;task_summary',
    'sync_artifact',
    'Policy that manager may observe realtime execution->model shadow handoffs through receipts and normalized rows, but the handoff does not authorize provider streams, model activation, production decisions, broker orders, persistence, or account mutation by itself.'
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
