-- Align the manager-side promotion target list with current conceptual layer numbering.
-- Legacy physical evidence component ids remain registered separately until code/SQL/data surfaces are renamed.

UPDATE trading_registry
SET payload = 'model_01_market_regime;model_02_sector_context;model_03_target_state_vector;model_04_alpha_confidence;model_05_position_projection;model_06_underlying_action;model_07_option_expression;model_08_event_risk_governor',
    note = 'Canonical model ids accepted by the unified manager-side promotion review request planner, ordered by current conceptual layer order. Legacy physical evidence ids remain model_05_alpha_confidence, model_06_position_projection, model_07_underlying_action, and model_08_option_expression until dedicated code/SQL/data migration.',
    updated_at = NOW()
WHERE id = 'cfg_UMP002';

UPDATE trading_registry
SET note = 'Unified promotion review entrypoint. Canonical request ids use current conceptual model ids; legacy physical evidence component ids remain accepted aliases while physical code/SQL/data surfaces are migrated.',
    updated_at = NOW()
WHERE id = 'scr_UMPR001';
