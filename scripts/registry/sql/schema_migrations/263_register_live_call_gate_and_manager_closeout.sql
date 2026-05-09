-- Register live-call approval gate and manager control-plane closeout status.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_LCA001',
    'artifact_type',
    'LIVE_CALL_APPROVAL_V1',
    'text',
    'live_call_approval_v1',
    'trading-manager/docs/95_task_system.md',
    'live_call_approval_gate_v1;manager_request_v1;provider_calls;trading-data;control_plane',
    'sync_artifact',
    'Reviewed artifact that permits a bounded non-dry-run provider acquisition request. It is data-acquisition-only and does not approve broker execution, model activation, or component dispatch by itself.'
  ),
  (
    'cfg_LCA001',
    'config',
    'LIVE_CALL_APPROVAL_GATE_V1',
    'text',
    'explicit_live_call_approval_v1_required;request_must_be_non_dry_run;live_call_policy_required;provider_allowlist_required;max_requests_required;max_window_days_required;approval_expiry_required;provider_data_acquisition_only;broker_execution_forbidden;no_provider_dispatch_in_validator',
    'trading-manager/docs/95_task_system.md',
    'live_call_approval_gate_v1;provider_calls;monthly_backfill;control_plane;trading-data',
    'sync_artifact',
    'Manager-side approval gate for converting reviewed dry-run provider acquisition planning into bounded non-dry-run handoff eligibility. The validator performs no provider calls or dispatch.'
  ),
  (
    'cfg_MCO001',
    'config',
    'TRADING_MANAGER_CONTROL_PLANE_CLOSEOUT_STATUS',
    'text',
    'current_manager_control_plane_phase_closed;task_system_mvp_implemented;global_task_summary_implemented;monthly_backfill_planning_implemented;request_payload_materialization_implemented;dry_run_handoff_validation_implemented;unified_model_promotion_route_implemented;review_decision_activation_artifacts_implemented;live_call_gate_defined;no_live_provider_dispatch_enabled;no_broker_execution_enabled;no_production_activation_implied',
    'trading-manager/docs/97_manager_control_plane_closeout.md',
    'trading-manager;control_plane;closeout;task_system;model_promotion;live_call_approval_gate_v1',
    'sync_artifact',
    'Closeout status for the current trading-manager manager/control-plane design-and-MVP phase. Deferred production/component work remains outside this closeout.'
  ),
  (
    'scr_LCA001',
    'script',
    'MANAGER_LIVE_CALL_APPROVAL_VALIDATE',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/validate_live_call_approval.py',
    '/root/projects/trading-manager/scripts/tasks/validate_live_call_approval.py',
    'live_call_approval_gate_v1;live_call_approval_v1;manager_request_v1;provider_calls;control_plane',
    'sync_artifact',
    'Validate reviewed live_call_approval_v1 artifacts for non-dry-run provider acquisition eligibility without dispatching components or calling providers.'
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
