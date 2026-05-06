-- Prefix Layer 3 TargetStateVector value payloads and scope tokens with their
-- owning model layer. The kind classifies semantic tokens inside the vector
-- contract, so the payload carries the model number even when key/id remain
-- stable.

WITH layer_three_values AS (
  SELECT payload AS old_payload,
         '3_' || payload AS new_payload
  FROM trading_registry
  WHERE kind = 'state_vector_value'
    AND applies_to LIKE '%target_state_vector_model%'
    AND payload NOT LIKE '3\_%' ESCAPE '\'
), updated_scopes AS (
  SELECT r.id,
         STRING_AGG(COALESCE(v.new_payload, token.value), ';' ORDER BY token.ordinality) AS applies_to
  FROM trading_registry r
  CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(r.applies_to, ';')) WITH ORDINALITY AS token(value, ordinality)
  LEFT JOIN layer_three_values v ON token.value = v.old_payload
  WHERE r.applies_to IS NOT NULL
  GROUP BY r.id
)
UPDATE trading_registry r
SET applies_to = updated_scopes.applies_to,
    updated_at = CURRENT_TIMESTAMP
FROM updated_scopes
WHERE r.id = updated_scopes.id
  AND r.applies_to IS DISTINCT FROM updated_scopes.applies_to;

UPDATE trading_registry
SET payload = '3_' || payload,
    updated_at = CURRENT_TIMESTAMP
WHERE kind = 'state_vector_value'
  AND applies_to LIKE '%target_state_vector_model%'
  AND payload NOT LIKE '3\_%' ESCAPE '\';
