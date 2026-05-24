-- Remove PDT/day-trade gating from C03 after accepted launch timing correction.

UPDATE trading_registry
SET payload = 'underlying_first_lifecycle;options_are_expression_translation;model_underlying_stop_required;no_fixed_option_loss_stop;explicit_reason_evidence_required;respect_sector_opportunity_mix;cautious_add_reduce_requires_reason_evidence;agent_final_review_before_live_submission',
    note = 'C03 Lifecycle manages already-open positions in underlying-thesis terms. It decides hold, add, reduce, stop, exit, or take-profit from model stops, thesis invalidation, alpha, event risk, dynamic policy, position projection, and underlying action. Option contracts are expression translation owned by C04. Fixed option mark-to-market loss percentages are not ordinary lifecycle stops. C03 does not run fee, PDT, day-trade, or churn formulas; every non-hold action must carry explicit reason evidence. Add decisions must respect C01/M07 sector-opportunity and portfolio constraints, and add/reduce churn must be justified by model evidence and thesis state rather than short-term noise. Live submission still requires C07 agent final review.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC006';

UPDATE trading_registry
SET note = 'C07 Execution Gate requires an approved agent final review before any live broker submission for open, add, reduce, exit, stop, take-profit, option roll, or stock fallback orders. The review consumes C02/C03/C04 reason evidence, sector/opportunity-mix compliance, broker/regulatory context, fees, spread, and transaction costs. Broker/regulatory hard blocks still reject outright.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC007';

UPDATE trading_registry
SET note = 'Execution runtime contract emitted by C03 Lifecycle for already-open position management. C03 is underlying-first: it decides hold, add, reduce, exit, stop, take-profit, or flatten-review from model-provided underlying thesis state, alpha, event risk, dynamic policy, and position projection. For the high-risk options account it does not use fixed option mark-to-market loss percentages as ordinary stops; C04 owns option expression translation. C03 emits explicit reason evidence, blocks add when C01/M07 sector-opportunity or portfolio constraints are already filled, and keeps add/reduce decisions cautious without a separate PDT/day-trade gate.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'art_EXECRTC005';

UPDATE trading_registry
SET note = 'Accepted concise numbered intraday execution component sequence. C01 Intake owns account/watch-target intake; C02 Entry owns underlying entry-thesis suitability; C03 Lifecycle owns underlying-first open-position lifecycle with model stops, reason evidence, sector/opportunity add constraints, and cautious add/reduce justification; C04 owns option/underlying expression review; C07 owns the agent-reviewed live-submission gate. component_id values follow the model-aligned physical naming pattern component_01_* through component_07_*.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_EXECRTC003';
