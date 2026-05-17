-- Align current live PostgreSQL table names, column names, and stored numbering values
-- with the accepted nine-layer order after inserting EventFailureRiskModel as Layer 4.
--
-- Historical registry migrations and historical artifact paths are intentionally not edited.
-- Apply only to current/live tables after a backup.

BEGIN;

-- Current table names. These are intentionally one-way current-state aliases;
-- historical artifact files and applied migration records keep their original names.
ALTER TABLE IF EXISTS trading_model.model_04_event_overlay RENAME TO model_09_event_risk_governor;
ALTER TABLE IF EXISTS trading_model.model_08_event_risk_governor RENAME TO model_09_event_risk_governor;
ALTER TABLE IF EXISTS trading_model.model_04_alpha_confidence RENAME TO model_05_alpha_confidence;
ALTER TABLE IF EXISTS trading_model.model_05_position_projection RENAME TO model_06_position_projection;
ALTER TABLE IF EXISTS trading_model.model_06_underlying_action RENAME TO model_07_underlying_action;
ALTER TABLE IF EXISTS trading_model.model_07_option_expression RENAME TO model_08_option_expression;
ALTER TABLE IF EXISTS trading_data.source_04_event_overlay RENAME TO source_09_event_risk_governor;
ALTER TABLE IF EXISTS trading_data.source_08_event_risk_governor RENAME TO source_09_event_risk_governor;
ALTER TABLE IF EXISTS trading_data.feature_04_event_overlay RENAME TO feature_09_event_risk_governor;
ALTER TABLE IF EXISTS trading_data.feature_08_event_risk_governor RENAME TO feature_09_event_risk_governor;
ALTER TABLE IF EXISTS trading_data.feature_07_option_expression RENAME TO feature_08_option_expression;

-- Primary-key index / constraint names.
ALTER INDEX IF EXISTS trading_model.model_04_event_overlay_pkey RENAME TO model_09_event_risk_governor_pkey;
ALTER INDEX IF EXISTS trading_model.model_08_event_risk_governor_pkey RENAME TO model_09_event_risk_governor_pkey;
ALTER INDEX IF EXISTS trading_model.model_04_alpha_confidence_pkey RENAME TO model_05_alpha_confidence_pkey;
ALTER INDEX IF EXISTS trading_model.model_05_position_projection_pkey RENAME TO model_06_position_projection_pkey;
ALTER INDEX IF EXISTS trading_model.model_06_underlying_action_pkey RENAME TO model_07_underlying_action_pkey;
ALTER INDEX IF EXISTS trading_model.model_07_option_expression_pkey RENAME TO model_08_option_expression_pkey;
ALTER INDEX IF EXISTS trading_data.source_04_event_overlay_pkey RENAME TO source_09_event_risk_governor_pkey;
ALTER INDEX IF EXISTS trading_data.source_08_event_risk_governor_pkey RENAME TO source_09_event_risk_governor_pkey;
ALTER INDEX IF EXISTS trading_data.feature_04_event_overlay_pkey RENAME TO feature_09_event_risk_governor_pkey;
ALTER INDEX IF EXISTS trading_data.feature_08_event_risk_governor_pkey RENAME TO feature_09_event_risk_governor_pkey;
ALTER INDEX IF EXISTS trading_data.feature_07_option_expression_pkey RENAME TO feature_08_option_expression_pkey;

-- Numeric score/field column prefixes.
DO $$
DECLARE
  item record;
  col record;
  old_name text;
  new_name text;
BEGIN
  FOR item IN
    SELECT * FROM (VALUES
      ('trading_model','model_09_event_risk_governor','4_event_','9_event_'),
      ('trading_model','model_09_event_risk_governor','8_event_','9_event_'),
      ('trading_model','model_05_alpha_confidence','4_','5_'),
      ('trading_model','model_06_position_projection','5_','6_'),
      ('trading_model','model_07_underlying_action','6_','7_'),
      ('trading_model','model_08_option_expression','7_','8_'),
      ('trading_data','feature_09_event_risk_governor','4_event_','9_event_'),
      ('trading_data','feature_09_event_risk_governor','8_event_','9_event_'),
      ('trading_data','feature_08_option_expression','7_','8_')
    ) AS v(schema_name, table_name, old_prefix, new_prefix)
  LOOP
    FOR col IN
      SELECT column_name
      FROM information_schema.columns
      WHERE table_schema = item.schema_name
        AND table_name = item.table_name
        AND column_name LIKE item.old_prefix || '%'
      ORDER BY ordinal_position
    LOOP
      old_name := col.column_name;
      new_name := item.new_prefix || substring(old_name FROM length(item.old_prefix) + 1);
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = item.schema_name AND table_name = item.table_name AND column_name = new_name
      ) THEN
        EXECUTE format('ALTER TABLE %I.%I RENAME COLUMN %I TO %I', item.schema_name, item.table_name, old_name, new_name);
      END IF;
    END LOOP;
  END LOOP;
END $$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'trading_model'
      AND table_name = 'model_09_event_risk_governor'
      AND column_name = 'event_overlay_diagnostics'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'trading_model'
      AND table_name = 'model_09_event_risk_governor'
      AND column_name = 'event_risk_governor_diagnostics'
  ) THEN
    ALTER TABLE trading_model.model_09_event_risk_governor
      RENAME COLUMN event_overlay_diagnostics TO event_risk_governor_diagnostics;
  END IF;
END $$;

-- Stored current row values.
UPDATE trading_model.model_09_event_risk_governor
SET model_id = CASE WHEN model_id IN ('event_overlay_model', 'model_08_event_risk_governor') THEN 'event_risk_governor' ELSE model_id END,
    model_layer = replace(replace(model_layer, 'layer_04_event_overlay', 'layer_09_event_risk_governor'), 'layer_08_event_risk_governor', 'layer_09_event_risk_governor'),
    event_context_vector_ref = replace(replace(replace(replace(event_context_vector_ref, 'model_04_event_overlay', 'model_09_event_risk_governor'), 'model_08_event_risk_governor', 'model_09_event_risk_governor'), 'event_overlay', 'event_risk_governor'), 'layer_08_event_risk_governor', 'layer_09_event_risk_governor'),
    event_context_vector = replace(replace(replace(replace(replace(event_context_vector::text, '"4_event_', '"9_event_'), '"8_event_', '"9_event_'), 'layer_04_event_overlay', 'layer_09_event_risk_governor'), 'model_08_event_risk_governor', 'model_09_event_risk_governor'), 'event_overlay', 'event_risk_governor')::jsonb,
    event_risk_governor_diagnostics = replace(replace(replace(replace(replace(event_risk_governor_diagnostics::text, '"4_event_', '"9_event_'), '"8_event_', '"9_event_'), 'layer_04_event_overlay', 'layer_09_event_risk_governor'), 'model_08_event_risk_governor', 'model_09_event_risk_governor'), 'event_overlay', 'event_risk_governor')::jsonb
WHERE model_layer LIKE '%layer_04_event_overlay%'
   OR model_layer LIKE '%layer_08_event_risk_governor%'
   OR model_id = 'event_overlay_model'
   OR event_context_vector_ref LIKE '%event_overlay%'
   OR event_context_vector_ref LIKE '%model_08_event_risk_governor%'
   OR event_context_vector::text LIKE '%4\_event\_%' ESCAPE '\'
   OR event_context_vector::text LIKE '%8\_event\_%' ESCAPE '\'
   OR event_risk_governor_diagnostics::text LIKE '%event_overlay%'
   OR event_risk_governor_diagnostics::text LIKE '%8\_event\_%' ESCAPE '\';

UPDATE trading_model.model_05_alpha_confidence
SET model_layer = replace(model_layer, 'layer_04_alpha_confidence', 'layer_05_alpha_confidence'),
    alpha_confidence_vector_ref = replace(replace(alpha_confidence_vector_ref, 'model_04_alpha_confidence', 'model_05_alpha_confidence'), 'layer_04_alpha_confidence', 'layer_05_alpha_confidence'),
    event_context_vector_ref = replace(replace(replace(event_context_vector_ref, 'model_04_event_overlay', 'model_09_event_risk_governor'), 'model_08_event_risk_governor', 'model_09_event_risk_governor'), 'event_overlay', 'event_risk_governor'),
    alpha_confidence_vector = replace(replace(alpha_confidence_vector::text, '"4_', '"5_'), 'layer_04_alpha_confidence', 'layer_05_alpha_confidence')::jsonb,
    base_alpha_vector = replace(replace(base_alpha_vector::text, '"4_', '"5_'), 'layer_04_alpha_confidence', 'layer_05_alpha_confidence')::jsonb,
    alpha_confidence_diagnostics = replace(replace(replace(replace(alpha_confidence_diagnostics::text, '"4_', '"5_'), 'layer_04_alpha_confidence', 'layer_05_alpha_confidence'), 'model_04_alpha_confidence', 'model_05_alpha_confidence'), 'model_04_event_overlay', 'model_09_event_risk_governor')::jsonb
WHERE model_layer LIKE '%layer_04_alpha_confidence%'
   OR alpha_confidence_vector_ref LIKE '%model_04_alpha_confidence%'
   OR event_context_vector_ref LIKE '%event_overlay%'
   OR alpha_confidence_vector::text LIKE '%4\_%' ESCAPE '\'
   OR base_alpha_vector::text LIKE '%4\_%' ESCAPE '\'
   OR alpha_confidence_diagnostics::text LIKE '%4\_%' ESCAPE '\'
   OR alpha_confidence_diagnostics::text LIKE '%model_04_alpha_confidence%';

UPDATE trading_model.model_06_position_projection
SET model_layer = replace(model_layer, 'layer_05_position_projection', 'layer_06_position_projection'),
    alpha_confidence_vector_ref = replace(replace(alpha_confidence_vector_ref, 'model_04_alpha_confidence', 'model_05_alpha_confidence'), 'layer_04_alpha_confidence', 'layer_05_alpha_confidence'),
    position_projection_vector_ref = replace(replace(position_projection_vector_ref, 'model_05_position_projection', 'model_06_position_projection'), 'layer_05_position_projection', 'layer_06_position_projection'),
    position_projection_vector = replace(replace(position_projection_vector::text, '"5_', '"6_'), 'layer_05_position_projection', 'layer_06_position_projection')::jsonb,
    position_projection_diagnostics = replace(replace(replace(position_projection_diagnostics::text, '"5_', '"6_'), 'layer_05_position_projection', 'layer_06_position_projection'), 'model_05_position_projection', 'model_06_position_projection')::jsonb
WHERE model_layer LIKE '%layer_05_position_projection%'
   OR alpha_confidence_vector_ref LIKE '%model_04_alpha_confidence%'
   OR position_projection_vector_ref LIKE '%model_05_position_projection%'
   OR position_projection_vector::text LIKE '%5\_%' ESCAPE '\'
   OR position_projection_diagnostics::text LIKE '%5\_%' ESCAPE '\'
   OR position_projection_diagnostics::text LIKE '%model_05_position_projection%';

UPDATE trading_model.model_07_underlying_action
SET model_layer = replace(model_layer, 'layer_06_underlying_action', 'layer_07_underlying_action'),
    alpha_confidence_vector_ref = replace(replace(alpha_confidence_vector_ref, 'model_04_alpha_confidence', 'model_05_alpha_confidence'), 'layer_04_alpha_confidence', 'layer_05_alpha_confidence'),
    position_projection_vector_ref = replace(replace(position_projection_vector_ref, 'model_05_position_projection', 'model_06_position_projection'), 'layer_05_position_projection', 'layer_06_position_projection'),
    underlying_action_plan_ref = replace(replace(underlying_action_plan_ref, 'model_06_underlying_action', 'model_07_underlying_action'), 'layer_06_underlying_action', 'layer_07_underlying_action'),
    underlying_action_plan = replace(replace(underlying_action_plan::text, '"6_', '"7_'), 'layer_06_underlying_action', 'layer_07_underlying_action')::jsonb,
    underlying_action_vector = replace(replace(underlying_action_vector::text, '"6_', '"7_'), 'layer_06_underlying_action', 'layer_07_underlying_action')::jsonb
WHERE model_layer LIKE '%layer_06_underlying_action%'
   OR position_projection_vector_ref LIKE '%model_05_position_projection%'
   OR underlying_action_plan_ref LIKE '%model_06_underlying_action%'
   OR underlying_action_plan::text LIKE '%6\_%' ESCAPE '\'
   OR underlying_action_vector::text LIKE '%6\_%' ESCAPE '\';

UPDATE trading_model.model_08_option_expression
SET model_layer = replace(model_layer, 'layer_07_option_expression', 'layer_08_option_expression'),
    underlying_action_plan_ref = replace(replace(underlying_action_plan_ref, 'model_06_underlying_action', 'model_07_underlying_action'), 'layer_06_underlying_action', 'layer_07_underlying_action'),
    option_expression_plan_ref = replace(replace(option_expression_plan_ref, 'model_07_option_expression', 'model_08_option_expression'), 'layer_07_option_expression', 'layer_08_option_expression'),
    option_expression_plan = replace(replace(replace(option_expression_plan::text, '"7_', '"8_'), 'layer_07_option_expression', 'layer_08_option_expression'), 'model_07_option_expression', 'model_08_option_expression')::jsonb,
    expression_vector = replace(replace(replace(expression_vector::text, '"7_', '"8_'), 'layer_07_option_expression', 'layer_08_option_expression'), 'model_07_option_expression', 'model_08_option_expression')::jsonb
WHERE model_layer LIKE '%layer_07_option_expression%'
   OR underlying_action_plan_ref LIKE '%model_06_underlying_action%'
   OR option_expression_plan_ref LIKE '%model_07_option_expression%'
   OR option_expression_plan::text LIKE '%7\_%' ESCAPE '\'
   OR expression_vector::text LIKE '%7\_%' ESCAPE '\';

UPDATE trading_data.source_09_event_risk_governor
SET source_name = replace(replace(replace(source_name, 'source_04_event_overlay', 'source_09_event_risk_governor'), 'source_08_event_risk_governor', 'source_09_event_risk_governor'), 'event_overlay', 'event_risk_governor'),
    reference = replace(replace(replace(replace(reference, 'source_04_event_overlay', 'source_09_event_risk_governor'), 'source_08_event_risk_governor', 'source_09_event_risk_governor'), 'layer_04_event_overlay', 'layer_09_event_risk_governor'), 'event_overlay', 'event_risk_governor')
WHERE source_name LIKE '%source_04_event_overlay%'
   OR source_name LIKE '%source_08_event_risk_governor%'
   OR source_name LIKE '%event_overlay%'
   OR reference LIKE '%source_04_event_overlay%'
   OR reference LIKE '%source_08_event_risk_governor%'
   OR reference LIKE '%layer_04_event_overlay%'
   OR reference LIKE '%event_overlay%';

UPDATE trading_data.feature_09_event_risk_governor
SET run_id = replace(replace(replace(run_id, 'feature_04_event_overlay', 'feature_09_event_risk_governor'), 'feature_08_event_risk_governor', 'feature_09_event_risk_governor'), 'layer_04_event_overlay', 'layer_09_event_risk_governor'),
    source_run_ref = replace(replace(replace(source_run_ref, 'source_04_event_overlay', 'source_09_event_risk_governor'), 'source_08_event_risk_governor', 'source_09_event_risk_governor'), 'layer_04_event_overlay', 'layer_09_event_risk_governor'),
    feature_payload_json = replace(replace(replace(replace(replace(feature_payload_json::text, '"4_event_', '"9_event_'), '"8_event_', '"9_event_'), 'feature_04_event_overlay', 'feature_09_event_risk_governor'), 'source_04_event_overlay', 'source_09_event_risk_governor'), 'event_overlay', 'event_risk_governor')::jsonb,
    feature_quality_diagnostics = replace(replace(replace(replace(replace(feature_quality_diagnostics::text, '"4_event_', '"9_event_'), '"8_event_', '"9_event_'), 'feature_04_event_overlay', 'feature_09_event_risk_governor'), 'source_04_event_overlay', 'source_09_event_risk_governor'), 'event_overlay', 'event_risk_governor')::jsonb
WHERE run_id LIKE '%feature_04_event_overlay%'
   OR run_id LIKE '%feature_08_event_risk_governor%'
   OR source_run_ref LIKE '%source_04_event_overlay%'
   OR source_run_ref LIKE '%source_08_event_risk_governor%'
   OR feature_payload_json::text LIKE '%4\_event\_%' ESCAPE '\'
   OR feature_payload_json::text LIKE '%8\_event\_%' ESCAPE '\'
   OR feature_payload_json::text LIKE '%event_overlay%'
   OR feature_quality_diagnostics::text LIKE '%4\_event\_%' ESCAPE '\'
   OR feature_quality_diagnostics::text LIKE '%8\_event\_%' ESCAPE '\'
   OR feature_quality_diagnostics::text LIKE '%event_overlay%';

COMMIT;
