-- Clean remaining active registry notes after current physical numbering alignment.
-- Historical migrations intentionally remain unchanged as audit history.

UPDATE trading_registry
SET note = 'Conceptual Layer 7 model boundary that outputs the base offline trading-guidance candidate before event-risk intervention. The current V1 option-expression implementation surface is model_07_option_expression.',
    updated_at = NOW()
WHERE id = 'trm_TGM001';

UPDATE trading_registry
SET note = 'Layer 7 point-in-time underlying quote snapshot reference paired with the option-chain snapshot for moneyness and path replay.',
    updated_at = NOW()
WHERE id = 'trm_UQSR001';
