-- Register the first dashboard website/runtime slice.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_DASHRM005',
    'script',
    'DASHBOARD_WEB_DEV_SERVER',
    'command',
    'npm run dev',
    '/root/projects/trading-dashboard/package.json',
    'trading-dashboard;vite;react;typescript;historical_task_progress_summary_v1;read_only_ui',
    'sync_artifact',
    'Start the first dashboard website slice. The page reads storage-hosted dashboard read-model latest.json summaries through the local dev API and performs no provider calls, manager dispatch, model activation, broker execution, account mutation, or storage writes.'
  ),
  (
    'cfg_DASHRM007',
    'config',
    'DASHBOARD_WEB_RUNTIME_STACK',
    'text',
    'Vite + React + TypeScript',
    '/root/projects/trading-dashboard/package.json',
    'trading-dashboard;website_runtime;first_slice;read_only_presentation',
    'sync_artifact',
    'Accepted first dashboard website/runtime stack for read-only storage-hosted dashboard summaries.'
  ),
  (
    'cfg_DASHRM008',
    'config',
    'DASHBOARD_HISTORICAL_TASK_PROGRESS_PAGE',
    'text',
    'web/App.tsx renders historical_task_progress_summary_v1',
    '/root/projects/trading-dashboard/web/App.tsx',
    'trading-dashboard;tasks;historical_modeling;historical_task_progress_summary_v1;chart_first_ui',
    'sync_artifact',
    'First visible dashboard page: chart-first Historical Task Progress view over historical_task_progress_summary_v1.'
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
