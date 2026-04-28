UPDATE trading_registry
SET key = 'SNAPSHOT_TYPE',
    payload = 'snapshot_type',
    note = 'Role/type of an option-chain snapshot in the strategy timeline, such as entry or exit',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SNAPSHOT_ROLE';

UPDATE trading_registry
SET key = 'INFORMATION_ROLE_TYPE',
    payload = 'information_role_type',
    note = 'Event information role type for model use, such as lagging_evidence or prior_signal',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'INFORMATION_ROLE';

UPDATE trading_registry
SET key = 'EVENT_CATEGORY_TYPE',
    payload = 'event_category_type',
    note = 'Event overview category type such as macro_data, macro_news, sector_news, symbol_news, sec_filing, option_abnormal_activity, or equity_abnormal_activity',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'EVENT_CATEGORY';
