-- Finish active registry cleanup found by the final Codex 5.5 manager re-review.

UPDATE trading_registry
SET payload = replace(payload, 'layer_1_8_', 'layer_1_10_'),
    updated_at = NOW()
WHERE id IN ('cfg_MRTD001', 'cfg_MODEL_RTD001');

UPDATE trading_registry
SET note = replace(note, 'Layers 1-8', 'Layers 1-10'),
    updated_at = NOW()
WHERE id = 'trm_EXEC_RT002'
  AND note LIKE '%Layers 1-8%';

UPDATE trading_registry
SET key = replace(key, 'MODEL_09_', 'MODEL_10_'),
    note = replace(replace(note, 'Layers 1-8', 'Layers 1-10'), 'current MODEL_09 physical namespace', 'current MODEL_10 EventRiskGovernor surface'),
    updated_at = NOW()
WHERE kind = 'script'
  AND path LIKE '%model_10_event_risk_governor%'
  AND key LIKE 'MODEL_09_%';

UPDATE trading_registry
SET note = 'Builds the accepted event-model acceptance report: EventRiskGovernor / EventIntelligenceOverlay is Layer 10 on the current stack. Broad event alpha and signed earnings/guidance alpha remain blocked, diagnostic artifacts are preserved, and storage deletion stays on hold until reviewed regeneration completes.',
    updated_at = NOW()
WHERE id = 'scr_M9ERGCLS001';

UPDATE trading_registry
SET applies_to = replace(
        applies_to,
        'trading_model.model_05_alpha_confidence;trading_model.model_07_position_projection',
        'trading_model.model_05_alpha_confidence;trading_model.model_06_dynamic_risk_policy;trading_model.model_07_position_projection'
    ),
    note = replace(note, 'all nine model output table families', 'all ten model output table families'),
    updated_at = NOW()
WHERE id IN ('scr_MOTQG001', 'scr_MOTQA001');
