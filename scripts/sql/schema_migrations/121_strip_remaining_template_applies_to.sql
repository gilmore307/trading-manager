UPDATE trading_registry
SET applies_to = cleaned.applies_to,
    updated_at = CURRENT_TIMESTAMP
FROM (
  SELECT id, string_agg(part, ';' ORDER BY ord) AS applies_to
  FROM trading_registry,
       unnest(string_to_array(applies_to, ';')) WITH ORDINALITY AS parts(part, ord)
  WHERE kind IN ('field', 'identity_field', 'path_field', 'temporal_field', 'classification_field', 'text_field', 'parameter_field')
    AND (part LIKE '%_template' OR part IN ('option_template', 'data_kind_template'))
  GROUP BY id
) AS touched
JOIN LATERAL (
  SELECT string_agg(part, ';' ORDER BY ord) AS applies_to
  FROM unnest(string_to_array((SELECT applies_to FROM trading_registry WHERE id = touched.id), ';')) WITH ORDINALITY AS parts(part, ord)
  WHERE part NOT LIKE '%_template'
    AND part NOT IN ('option_template', 'data_kind_template')
) AS cleaned ON true
WHERE trading_registry.id = touched.id
  AND cleaned.applies_to IS NOT NULL;
