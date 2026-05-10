-- Register formal chronological-forward historical backfill policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MBF005',
    'config',
    'MONTHLY_BACKFILL_CHRONOLOGICAL_FORWARD_POLICY',
    'text',
    'chronological_forward_backfill_policy_v1;accepted_common_start=2016-01;clamp_earlier_requests_to_common_start;month_major_order;older_eligible_months_before_newer_months;reviewed_operator_exception_required_for_leapfrog',
    'trading-manager/docs/94_monthly_backfill.md',
    'monthly_backfill_v1;historical_data_backfill;manager_request_v1;scheduler;formal_operation',
    'sync_artifact',
    'Formal historical operation starts at the accepted common start month 2016-01 and advances old-to-new month by month. The planner clamps earlier requested months to 2016-01 and emits requests in month-major chronological order; skipping ahead requires a reviewed operator exception.'
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
