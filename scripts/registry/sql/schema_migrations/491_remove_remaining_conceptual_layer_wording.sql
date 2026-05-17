-- Remove remaining unclear conceptual/legacy wording from active current registry rows after physical nine-layer alignment.
-- Historical migration records remain unchanged for auditability.

UPDATE trading_registry
SET note = replace(replace(note,
      'Conceptual Layer 7', 'Layer 7'),
      'conceptual Layer 7', 'Layer 7'),
    updated_at = NOW()
WHERE id IN ('cfg_PPVBP001', 'cfg_PPVHS001', 'trm_TSVEC01');

UPDATE trading_registry
SET note = replace(replace(note,
      'Conceptual Layer 8', 'Layer 8'),
      'conceptual Layer 8', 'Layer 8'),
    updated_at = NOW()
WHERE id IN ('cfg_PPVBP001', 'cfg_UAPB001', 'trm_UAP001')
   OR id LIKE 'cfg_L8OPT%'
   OR id LIKE 'fld_OEV%'
   OR id IN ('scr_L8GATE001', 'term_L8GATE001');
