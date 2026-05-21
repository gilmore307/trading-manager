-- Complete realtime coverage and EventRiskGovernor score-family registry cleanup.

UPDATE trading_registry
SET applies_to = 'trading-execution;realtime_market_data;model_01_market_regime;model_02_sector_context;model_03_target_state_vector;model_04_event_failure_risk;model_05_alpha_confidence;model_06_dynamic_risk_policy;model_07_position_projection;model_08_underlying_action;model_09_option_expression;model_10_event_risk_governor',
    updated_at = NOW()
WHERE id = 'trm_EXEC_RT002';

UPDATE trading_registry
SET note = replace(note, '9_event_*', '10_event_*'),
    updated_at = NOW()
WHERE id = 'cfg_ECVS001';
