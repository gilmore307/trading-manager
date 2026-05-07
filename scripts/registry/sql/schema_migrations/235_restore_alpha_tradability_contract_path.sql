-- Keep the Layer 5 alpha-tradability field's canonical contract path on the
-- Layer 5 document while preserving its downstream Layer 6/7 applicability.

UPDATE trading_registry
SET
  path = 'trading-model/docs/06_layer_05_alpha_confidence.md',
  note = 'Layer 5 AlphaConfidence final adjusted alpha-level suitability score for Layer 6 position projection and Layer 7 underlying-action planning by horizon; this is not target exposure, planned quantity, an order instruction, option expression, or final action.',
  updated_at = NOW()
WHERE key = 'ALPHA_TRADABILITY_SCORE_BY_HORIZON';
