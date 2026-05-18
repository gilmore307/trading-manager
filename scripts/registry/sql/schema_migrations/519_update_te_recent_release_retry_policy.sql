-- Update realtime TE due-release retry policy to fixed 10-second attempts plus websearch fallback.

UPDATE trading_registry
SET payload = 'te_recent_release_fetch_retry_10s_three_attempts_then_websearch',
    applies_to = 'trading_economics_calendar_web;realtime_recent_calendar;due_release_refresh;release_actual_update;websearch_public_macro_release;manager_task_system;source_09_event_risk_governor',
    note = 'Realtime TE release maintenance policy: fetch immediately when a scheduled release becomes due; if TE fetch fails or returns no released actual/revised value, retry every 10 seconds for 3 additional attempts. If all attempts fail or the release still appears missing, fall back to public macro websearch to find either the released value or a documented delay/cancellation/no-release reason. Fallback rows preserve provenance and do not authorize model activation, broker execution, order placement, or account mutation.',
    updated_at = NOW()
WHERE id = 'cfg_TECAL002'
  AND kind = 'config'
  AND key = 'TE_RECENT_RELEASE_FETCH_RETRY_POLICY';
