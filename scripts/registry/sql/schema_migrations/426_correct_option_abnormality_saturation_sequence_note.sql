-- Correct itemized-test sequence wording for option-abnormality saturation diagnostic.

UPDATE trading_registry
SET note = 'Sixth itemized earnings/guidance scout: 34 reviewed same-symbol non-earnings windows all emitted complete option-abnormality events, proving the current option-event standard is saturated for no-abnormality control design in this sample.',
    updated_at = NOW()
WHERE id = 'trm_OANS001';
