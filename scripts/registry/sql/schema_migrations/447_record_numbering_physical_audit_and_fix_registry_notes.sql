-- Record the physical numbering audit and fix remaining active registry notes whose wording still
-- treated legacy physical numbers as conceptual layer numbers.
-- This migration does not rename code packages, SQL tables, score prefixes, or historical rows.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_LPNA001',
    'config',
    'LAYER_PHYSICAL_NUMBERING_AUDIT',
    'text',
    'physical_numbering_not_clean;sql_tables_and_rows_still_legacy;dedicated_code_sql_data_migration_required',
    'trading-manager/docs/103_numbering_physical_audit.md',
    'model_04_event_overlay;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_08_option_expression;source_04_event_overlay;feature_04_event_overlay;registry_current;openclaw_database',
    'sync_artifact',
    'Audit result: conceptual layer numbering is documented, but physical SQL table names, stored model_layer values, score-prefix families, source/feature run ids, scripts, and some runtime contracts still carry legacy numbering. Do not claim numbering is physically clean until a dedicated code/SQL/data migration completes.'
  )
ON CONFLICT (id) DO UPDATE SET
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();

UPDATE trading_registry
SET note = 'Layer policy for OptionExpressionModel: option expression is conceptual Layer 7, consumes conceptual Layer 6 underlying path assumptions plus option-chain context, and remains offline without broker mutation. The payload still names legacy physical layer_08 tokens until a dedicated migration renames code/SQL/data surfaces.',
    updated_at = NOW()
WHERE id = 'cfg_OEML001';

UPDATE trading_registry
SET note = 'Reviewed legacy 8_* resolved expression field-family tokens for conceptual Layer 7 option-expression. They communicate chosen option expression, selected point-in-time contract reference, fit/confidence, and no-option reason codes; they are not broker order fields.',
    updated_at = NOW()
WHERE id = 'cfg_OEPR001';

UPDATE trading_registry
SET note = 'Legacy physical layer_08_option_expression bucket strikes for conceptual Layer 7 option-expression cover the current-price to target-price listed-strike corridor plus three actual listed strike levels on each side.',
    updated_at = NOW()
WHERE id = 'cfg_L8OPT002';

UPDATE trading_registry
SET note = 'Legacy physical layer_08_option_expression historical model-construction buckets for conceptual Layer 7 intentionally retain extreme/illiquid contracts for robustness instead of filtering them out at acquisition time.',
    updated_at = NOW()
WHERE id = 'cfg_L8OPT003';

UPDATE trading_registry
SET note = 'Accepted conceptual Layer 6 V1 planned direct-underlying action type vocabulary. maintain means an existing state remains aligned or not worth adjusting; no_trade means no new direct-underlying operation should be initiated.',
    updated_at = NOW()
WHERE id = 'cfg_UAPT001';

UPDATE trading_registry
SET note = 'Reviewed legacy 7_* resolved plan/handoff field-family tokens for communicating the conceptual Layer 6 direct-underlying action thesis to conceptual Layer 7 trading guidance and execution-side review. These are not broker order fields.',
    updated_at = NOW()
WHERE id = 'cfg_UAPR001';

UPDATE trading_registry
SET note = 'Accepted UnderlyingActionModel V1 horizons for conceptual Layer 6. 390min means one regular US equity session-equivalent horizon measured in tradable minutes; label builders must document same-session vs next-session-close resolution and use purge/embargo controls.',
    updated_at = NOW()
WHERE id = 'cfg_UAVH001';

UPDATE trading_registry
SET note = 'Conceptual Layer 4 base/unadjusted alpha diagnostic vector built from Layer 1/2/3 state evidence. Used for research, audit, and debugging; not the default Layer 5-facing alpha_confidence_vector output and not an EventRiskGovernor intervention.',
    updated_at = NOW()
WHERE id = 'trm_BAV001';

UPDATE trading_registry
SET note = 'Conceptual Layer 7 point-in-time option-chain snapshot reference used to replay why a selected contract was chosen. This is not a broker order id.',
    updated_at = NOW()
WHERE id = 'trm_OQSR001';

UPDATE trading_registry
SET note = 'Conceptual Layer 6 primary offline direct stock/ETF planned action output. It includes planned action type, effective exposure gap, planned incremental exposure, entry/target/stop/time-stop thesis, risk plan, conceptual Layer 7 trading-guidance handoff, and reason codes; it is not a broker order, final order quantity, option contract, or execution instruction.',
    updated_at = NOW()
WHERE id = 'trm_UAP001';

UPDATE trading_registry
SET note = 'Conceptual Layer 6 score/vector output for direct stock/ETF planned action quality by horizon. It carries eligibility, signed action direction, intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and action confidence; it is not a broker order or option-expression vector.',
    updated_at = NOW()
WHERE id = 'trm_UAV001';

UPDATE trading_registry
SET note = 'Conceptual Layer 4 AlphaConfidence final adjusted score family for model confidence in the alpha judgment by horizon; confidence is not alpha strength and not a trade instruction. Physical value name remains legacy 5_* until dedicated migration.',
    updated_at = NOW()
WHERE id = 'fld_ACMV1004';

UPDATE trading_registry
SET note = 'Conceptual Layer 4 AlphaConfidence signed final adjusted score family for horizon-aware alpha direction; positive is long alpha, negative is short alpha, and this is not a buy/sell/hold action. Physical value name remains legacy 5_* until dedicated migration.',
    updated_at = NOW()
WHERE id = 'fld_ACMV1001';

UPDATE trading_registry
SET note = 'Conceptual Layer 4 AlphaConfidence signed final adjusted score family for standardized residual expected return by horizon after market/sector baseline adjustment and before position projection. Physical value name remains legacy 5_* until dedicated migration.',
    updated_at = NOW()
WHERE id = 'fld_ACMV1003';

UPDATE trading_registry
SET note = replace(note, 'Layer 5 AlphaConfidence', 'Conceptual Layer 4 AlphaConfidence') || CASE WHEN note LIKE '%legacy 5_*%' THEN '' ELSE ' Physical value name remains legacy 5_* until dedicated migration.' END,
    updated_at = NOW()
WHERE id IN ('fld_ACMV1002','fld_ACMV1005','fld_ACMV1006','fld_ACMV1007','fld_ACMV1008','fld_ACMV1009')
  AND note LIKE 'Layer 5 AlphaConfidence%';

UPDATE trading_registry
SET note = replace(replace(note, 'Layer 6 high-is-good', 'Conceptual Layer 5 high-is-good'), 'This is separate from Layer 5 alpha confidence.', 'This is separate from conceptual Layer 4 alpha confidence.') || ' Physical value name remains legacy 6_* until dedicated migration.',
    updated_at = NOW()
WHERE id = 'fld_PPV1010';

UPDATE trading_registry
SET note = replace(note, 'Layer 6 signed', 'Conceptual Layer 5 signed') || ' Physical value name remains legacy 6_* until dedicated migration.',
    updated_at = NOW()
WHERE id IN ('fld_PPV1001','fld_PPV1002')
  AND note LIKE 'Layer 6%';

UPDATE trading_registry
SET note = replace(note, 'Layer 7 ', 'Conceptual Layer 6 ') || ' Physical value name remains legacy 7_* until dedicated migration.',
    updated_at = NOW()
WHERE id LIKE 'fld_UAV%'
  AND note LIKE 'Layer 7%';

UPDATE trading_registry
SET note = replace(note, 'Layer 8 ', 'Conceptual Layer 7 ') || ' Physical value name remains legacy 8_* until dedicated migration.',
    updated_at = NOW()
WHERE id IN ('fld_OEV1004','fld_OEV1005','fld_OEV1006','fld_OEV1007','fld_OEV1008','fld_OEV1009')
  AND note LIKE 'Layer 8%';

UPDATE trading_registry
SET payload = 'layer_1:model_01_market_regime:mdevrun_1d00f2757982bd63:mpcand_b79411e80a774787:mpdec_d743cb5dbc8159f2:deferred;layer_2:model_02_sector_context:mdevrun_00c81e53569941df:mpcand_a6044e72162553f9:mpdec_3ab83ea1f423326d:deferred;layer_3:model_03_target_state_vector:mdevrun_327616bb447ceb5b:mpcand_1b077bca49a18dbf:mpdec_70fef0f31847cc1c:deferred;layer_4:model_05_alpha_confidence:mdevrun_closeout_l05_no_eval_substrate_20260508:mpcand_72289e5cc95ae2d5:mpdec_9c3e19d6559ef55b:deferred;layer_5:model_06_position_projection:mdevrun_closeout_l06_no_eval_substrate_20260508:mpcand_622c6ffa9ffca030:mpdec_b118232e76fae092:deferred;layer_6:model_07_underlying_action:mdevrun_closeout_l07_no_eval_substrate_20260508:mpcand_d4911cef39a14b97:mpdec_fabc9c709149a698:deferred;layer_7:model_08_option_expression:mdevrun_closeout_l08_no_eval_substrate_20260508:mpcand_9de333239d5c3f12:mpdec_e7448aaab1334345:deferred;layer_8:model_08_event_risk_governor:mdevrun_closeout_l04_no_eval_substrate_20260508:mpcand_6ab73401f22ab057:mpdec_76b07ea01a3f525b:deferred',
    note = 'Persisted promotion closeout decision receipts mapped to the current conceptual layer order. Physical receipt ids/model ids remain legacy where noted; deferred decisions leave active config pointers unchanged.',
    updated_at = NOW()
WHERE id = 'cfg_MPC001';

UPDATE trading_registry
SET payload = 'model_01_market_regime;model_02_sector_context;model_03_target_state_vector;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_08_option_expression;model_08_event_risk_governor',
    note = 'Model ids accepted by the unified manager-side promotion review request planner, ordered by current conceptual layer order. Several physical ids remain legacy until dedicated code/SQL/data migration.',
    updated_at = NOW()
WHERE id = 'cfg_UMP002';

UPDATE trading_registry
SET note = 'Manager-safe offline workflow for conceptual Layers 4-7 after upstream Layer 3 completes. Generation/evaluation/review stages may run without provider approval because provider_calls=0, activation=false, broker_execution=false, and promotion review remains deferred unless separately approved. Physical script ids still use legacy L5-L8 names until dedicated migration.',
    updated_at = NOW()
WHERE id = 'term_L5L7DB001';

UPDATE trading_registry
SET note = 'Current gap summary for realtime coverage after the conceptual Layers 1-8 matrix: proxy/native macro-market routes, event adapters, broker/account state, restriction/account state, and ThetaData terminal dependency remain explicit. Payload values may still contain legacy physical layer tokens until execution contracts are migrated.',
    updated_at = NOW()
WHERE id = 'cfg_EXEC_RT003';
