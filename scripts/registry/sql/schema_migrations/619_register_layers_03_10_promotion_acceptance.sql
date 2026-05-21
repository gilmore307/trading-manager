-- Align the active model promotion acceptance script registry with the current
-- ten-layer trading-model entrypoint. Historical migrations keep their original
-- route names as audit evidence.

UPDATE trading_registry
SET key = 'REVIEW_LAYERS_03_10_PROMOTION_ACCEPTANCE',
    payload = replace(payload, 'review_layers_03_08_promotion_acceptance.py', 'review_layers_03_10_promotion_acceptance.py'),
    path = replace(path, 'review_layers_03_08_promotion_acceptance.py', 'review_layers_03_10_promotion_acceptance.py'),
    applies_to = replace(replace(applies_to, 'layers_3_8', 'layers_3_10'), 'layers_03_08', 'layers_03_10'),
    note = replace(
      replace(note, 'Layers 3-8', 'Layers 3-10'),
      'Layers 3-8.', 'Layers 3-10.'
    ),
    updated_at = NOW()
WHERE key = 'REVIEW_LAYERS_03_08_PROMOTION_ACCEPTANCE';

