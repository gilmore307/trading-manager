-- Update realtime TE due-release retry policy to six 10-second retries before websearch fallback.

UPDATE trading_registry
SET payload = 'te_recent_release_fetch_retry_10s_six_attempts_then_websearch',
    note = 'Realtime TE release maintenance policy: fetch immediately when a scheduled release becomes due; if TE fetch fails or returns no released actual/revised value, retry every 10 seconds for 6 additional attempts, roughly 1 minute total retry time. If all attempts fail or the release still appears missing, fall back to public macro websearch to find either the released value or a documented delay/cancellation/no-release reason. Fallback rows preserve provenance and do not authorize model activation, broker execution, order placement, or account mutation.',
    updated_at = NOW()
WHERE id = 'cfg_TECAL002'
  AND kind = 'config'
  AND key = 'TE_RECENT_RELEASE_FETCH_RETRY_POLICY';
