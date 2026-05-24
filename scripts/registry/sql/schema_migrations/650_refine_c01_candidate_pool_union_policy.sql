-- Refine C01 candidate pool source union and volume thresholds.

UPDATE trading_registry
SET payload = 'remaining_strong_sector_targets;recent_high_trading_volume_targets;recent_abnormal_volume_targets;recent_news_or_earnings_catalyst_targets;filled_sector_removes_sector_reason_only',
    note = 'C01 maintains the equity/options watch target pool as the union of remaining strong-sector targets, recent high-volume targets, recent abnormal-volume targets, and recent news or earnings catalyst targets. A filled sector removes only the strong-sector opportunity reason; targets from that sector can still enter through high-volume, abnormal-volume, or catalyst evidence. High-volume means a reviewed flag or volume/dollar-volume score or percentile >= 0.80. Abnormal-volume means a reviewed flag, relative/abnormal volume score >= 0.80, relative volume >= 2.0x, or volume z-score >= 2.0.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC004';

UPDATE trading_registry
SET note = 'Execution runtime contract emitted by C01 Intake for account balance state, current holdings, dynamic remaining sector opportunity mix, watch targets from the union of accepted candidate sources, and account-sleeve candidate filtering. A filled sector removes only the sector-opportunity reason; independent high-volume, abnormal-volume, news, or earnings catalyst evidence may still admit the target. C01 does not allocate risk budget, size positions, decide entries, manage exits, construct orders, or mutate broker/account state.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC003';
