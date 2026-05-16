-- Rename active event-risk model/task registry surfaces away from legacy Layer 4 EventOverlay naming.

UPDATE trading_registry
SET payload = REPLACE(payload, 'scripts/models/model_04_event_overlay/generate_model_04_event_overlay.py', 'scripts/models/model_08_event_risk_governor/generate_model_08_event_risk_governor.py'),
    path = REPLACE(path, 'scripts/models/model_04_event_overlay/generate_model_04_event_overlay.py', 'scripts/models/model_08_event_risk_governor/generate_model_08_event_risk_governor.py'),
    note = REPLACE(note, 'scripts/models/model_04_event_overlay/generate_model_04_event_overlay.py', 'scripts/models/model_08_event_risk_governor/generate_model_08_event_risk_governor.py'),
    updated_at = NOW()
WHERE payload LIKE '%scripts/models/model_04_event_overlay/generate_model_04_event_overlay.py%'
   OR path LIKE '%scripts/models/model_04_event_overlay/generate_model_04_event_overlay.py%'
   OR note LIKE '%scripts/models/model_04_event_overlay/generate_model_04_event_overlay.py%';

UPDATE trading_registry
SET payload = REPLACE(payload, 'scripts/models/model_04_event_overlay/evaluate_model_04_event_overlay.py', 'scripts/models/model_08_event_risk_governor/evaluate_model_08_event_risk_governor.py'),
    path = REPLACE(path, 'scripts/models/model_04_event_overlay/evaluate_model_04_event_overlay.py', 'scripts/models/model_08_event_risk_governor/evaluate_model_08_event_risk_governor.py'),
    note = REPLACE(note, 'scripts/models/model_04_event_overlay/evaluate_model_04_event_overlay.py', 'scripts/models/model_08_event_risk_governor/evaluate_model_08_event_risk_governor.py'),
    updated_at = NOW()
WHERE payload LIKE '%scripts/models/model_04_event_overlay/evaluate_model_04_event_overlay.py%'
   OR path LIKE '%scripts/models/model_04_event_overlay/evaluate_model_04_event_overlay.py%'
   OR note LIKE '%scripts/models/model_04_event_overlay/evaluate_model_04_event_overlay.py%';

UPDATE trading_registry
SET payload = REPLACE(payload, 'scripts/models/model_04_event_overlay/review_event_overlay_promotion.py', 'scripts/models/model_08_event_risk_governor/review_event_risk_governor_promotion.py'),
    path = REPLACE(path, 'scripts/models/model_04_event_overlay/review_event_overlay_promotion.py', 'scripts/models/model_08_event_risk_governor/review_event_risk_governor_promotion.py'),
    note = REPLACE(note, 'scripts/models/model_04_event_overlay/review_event_overlay_promotion.py', 'scripts/models/model_08_event_risk_governor/review_event_risk_governor_promotion.py'),
    updated_at = NOW()
WHERE payload LIKE '%scripts/models/model_04_event_overlay/review_event_overlay_promotion.py%'
   OR path LIKE '%scripts/models/model_04_event_overlay/review_event_overlay_promotion.py%'
   OR note LIKE '%scripts/models/model_04_event_overlay/review_event_overlay_promotion.py%';

UPDATE trading_registry
SET payload = REPLACE(payload, 'scripts/tasks/materialize_layer_four_event_overlay_inputs.py', 'scripts/tasks/materialize_layer_eight_event_risk_governor_inputs.py'),
    path = REPLACE(path, 'scripts/tasks/materialize_layer_four_event_overlay_inputs.py', 'scripts/tasks/materialize_layer_eight_event_risk_governor_inputs.py'),
    note = REPLACE(note, 'scripts/tasks/materialize_layer_four_event_overlay_inputs.py', 'scripts/tasks/materialize_layer_eight_event_risk_governor_inputs.py'),
    updated_at = NOW()
WHERE payload LIKE '%scripts/tasks/materialize_layer_four_event_overlay_inputs.py%'
   OR path LIKE '%scripts/tasks/materialize_layer_four_event_overlay_inputs.py%'
   OR note LIKE '%scripts/tasks/materialize_layer_four_event_overlay_inputs.py%';

UPDATE trading_registry
SET payload = REPLACE(payload, 'scripts/tasks/invalidate_layer_four_downstream_outputs.py', 'scripts/tasks/invalidate_layer_eight_event_downstream_outputs.py'),
    path = REPLACE(path, 'scripts/tasks/invalidate_layer_four_downstream_outputs.py', 'scripts/tasks/invalidate_layer_eight_event_downstream_outputs.py'),
    note = REPLACE(note, 'scripts/tasks/invalidate_layer_four_downstream_outputs.py', 'scripts/tasks/invalidate_layer_eight_event_downstream_outputs.py'),
    updated_at = NOW()
WHERE payload LIKE '%scripts/tasks/invalidate_layer_four_downstream_outputs.py%'
   OR path LIKE '%scripts/tasks/invalidate_layer_four_downstream_outputs.py%'
   OR note LIKE '%scripts/tasks/invalidate_layer_four_downstream_outputs.py%';

UPDATE trading_registry
SET payload = REPLACE(payload, 'scripts/tasks/prepare_layer_four_event_feed_backfill.py', 'scripts/tasks/prepare_layer_eight_event_feed_backfill.py'),
    path = REPLACE(path, 'scripts/tasks/prepare_layer_four_event_feed_backfill.py', 'scripts/tasks/prepare_layer_eight_event_feed_backfill.py'),
    note = REPLACE(note, 'scripts/tasks/prepare_layer_four_event_feed_backfill.py', 'scripts/tasks/prepare_layer_eight_event_feed_backfill.py'),
    updated_at = NOW()
WHERE payload LIKE '%scripts/tasks/prepare_layer_four_event_feed_backfill.py%'
   OR path LIKE '%scripts/tasks/prepare_layer_four_event_feed_backfill.py%'
   OR note LIKE '%scripts/tasks/prepare_layer_four_event_feed_backfill.py%';

UPDATE trading_registry
SET payload = REPLACE(REPLACE(REPLACE(REPLACE(payload,
        'model_04_event_overlay', 'model_08_event_risk_governor'),
        'event_overlay_model', 'event_risk_governor'),
        'layer_04_event_overlay', 'layer_08_event_risk_governor'),
        'layer_four_event', 'layer_eight_event'),
    path = REPLACE(REPLACE(REPLACE(REPLACE(path,
        'model_04_event_overlay', 'model_08_event_risk_governor'),
        'event_overlay_model', 'event_risk_governor'),
        'layer_04_event_overlay', 'layer_08_event_risk_governor'),
        'layer_four_event', 'layer_eight_event'),
    applies_to = REPLACE(REPLACE(REPLACE(REPLACE(applies_to,
        'model_04_event_overlay', 'model_08_event_risk_governor'),
        'event_overlay_model', 'event_risk_governor'),
        'layer_04_event_overlay', 'layer_08_event_risk_governor'),
        'layer_four_event', 'layer_eight_event'),
    note = REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(note,
        'Model_04_event_overlay', 'Model_08_event_risk_governor'),
        'EventOverlayModel', 'EventRiskGovernor'),
        'Layer 4 EventOverlayModel', 'Layer 8 EventRiskGovernor'),
        'Layer 4 EventOverlay', 'Layer 8 EventRiskGovernor'),
        'Layer 4 event', 'Layer 8 event-risk'),
        'Layer 4+', 'event-risk-dependent'),
    updated_at = NOW()
WHERE payload LIKE '%model_04_event_overlay%'
   OR payload LIKE '%event_overlay_model%'
   OR payload LIKE '%layer_04_event_overlay%'
   OR payload LIKE '%layer_four_event%'
   OR path LIKE '%model_04_event_overlay%'
   OR path LIKE '%event_overlay_model%'
   OR path LIKE '%layer_04_event_overlay%'
   OR path LIKE '%layer_four_event%'
   OR applies_to LIKE '%model_04_event_overlay%'
   OR applies_to LIKE '%event_overlay_model%'
   OR applies_to LIKE '%layer_04_event_overlay%'
   OR applies_to LIKE '%layer_four_event%'
   OR note LIKE '%EventOverlayModel%'
   OR note LIKE '%Layer 4 EventOverlay%'
   OR note LIKE '%Layer 4 event%'
   OR note LIKE '%Layer 4+%';

UPDATE trading_registry
SET id = 'cfg_L8EVTCOV001',
    key = 'LAYER_EIGHT_REQUIRED_EVENT_FEED_ARTIFACTS',
    updated_at = NOW()
WHERE id = 'cfg_L4EVTCOV001';

UPDATE trading_registry
SET id = 'scr_L8EVTDIS001',
    key = 'MANAGER_DISPATCH_LAYER_EIGHT_EVENT_FEED_BACKFILL',
    updated_at = NOW()
WHERE id = 'scr_L4EVTDIS001';

UPDATE trading_registry
SET id = 'scr_L8EVTINV001',
    key = 'MANAGER_INVALIDATE_LAYER_EIGHT_EVENT_DOWNSTREAM_OUTPUTS',
    updated_at = NOW()
WHERE id = 'scr_L4EVTINV001';

UPDATE trading_registry
SET id = 'scr_L8ERGMAT001',
    key = 'MANAGER_MATERIALIZE_LAYER_EIGHT_EVENT_RISK_INPUTS',
    updated_at = NOW()
WHERE id = 'scr_L4EOM001';

UPDATE trading_registry
SET id = 'scr_L8EVTBF001',
    key = 'MANAGER_PREPARE_LAYER_EIGHT_EVENT_FEED_BACKFILL',
    updated_at = NOW()
WHERE id = 'scr_L4EVTBF001';

UPDATE trading_registry
SET id = 'scr_M8ERGEVAL',
    key = 'MODEL_08_EVENT_RISK_GOVERNOR_EVALUATE_PROMOTION_EVIDENCE',
    updated_at = NOW()
WHERE id = 'scr_M4EOMEVAL';

UPDATE trading_registry
SET id = 'scr_M8ERGGEN',
    key = 'MODEL_08_EVENT_RISK_GOVERNOR_GENERATE',
    updated_at = NOW()
WHERE id = 'scr_M4EOMGEN';

UPDATE trading_registry
SET id = 'scr_M8ERGREV',
    key = 'MODEL_08_EVENT_RISK_GOVERNOR_REVIEW_PROMOTION',
    updated_at = NOW()
WHERE id = 'scr_M4EOMREV';

UPDATE trading_registry
SET id = 'term_L8EVTDIS001',
    key = 'LAYER_EIGHT_EVENT_FEED_BACKFILL_DISPATCH',
    updated_at = NOW()
WHERE id = 'term_L4EVTDIS001';

UPDATE trading_registry
SET id = 'term_L8EVTBF001',
    key = 'LAYER_EIGHT_EVENT_FEED_BACKFILL_PREPARATION',
    updated_at = NOW()
WHERE id = 'term_L4EVTBF001';

UPDATE trading_registry
SET id = 'term_L8EVTCOV002',
    key = 'LAYER_EIGHT_EVENT_FEED_IN_WINDOW_ROW_COVERAGE',
    updated_at = NOW()
WHERE id = 'term_L4EVTCOV002';

UPDATE trading_registry
SET id = 'term_L8EVTCOV001',
    key = 'LAYER_EIGHT_EVENT_SOURCE_COVERAGE_GATE',
    updated_at = NOW()
WHERE id = 'term_L4EVTCOV001';

UPDATE trading_registry
SET id = 'trm_L8ERGMAT001',
    key = 'MANAGER_LAYER_EIGHT_EVENT_RISK_INPUT_MATERIALIZATION',
    payload = 'manager_layer_eight_event_risk_governor_input_materialization',
    updated_at = NOW()
WHERE id = 'trm_L4EOM001';

DELETE FROM trading_registry
WHERE id = 'trm_EOM001'
  AND key = 'EVENT_OVERLAY_MODEL';

UPDATE trading_registry
SET applies_to = 'trading-model;trading-data;source_04_event_overlay;model_08_event_risk_governor;event_context_vector;event_risk_intervention',
    note = 'Accepted conceptual Layer 8 event-risk governor. It consumes point-in-time event evidence after base trading guidance and remains bounded to risk governance unless reviewed evidence unlocks more.',
    updated_at = NOW()
WHERE key = 'EVENT_RISK_GOVERNOR';

UPDATE trading_registry
SET id = 'trm_M8ERG01',
    key = 'MODEL_08_EVENT_RISK_GOVERNOR',
    payload = 'model_08_event_risk_governor',
    path = 'trading-model/docs/09_layer_08_event_risk_governor.md',
    applies_to = 'trading-model;event_risk_governor;event_context_vector;source_04_event_overlay',
    note = 'Accepted EventRiskGovernor implementation surface for bounded event-risk evidence and intervention review. It replaces the legacy model_04_event_overlay surface.',
    updated_at = NOW()
WHERE id = 'trm_M4EOM01';
