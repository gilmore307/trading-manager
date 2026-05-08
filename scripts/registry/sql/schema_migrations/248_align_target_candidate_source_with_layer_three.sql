-- Align source_02_target_candidate_holdings with its semantic owner: Layer 3 input preparation.
-- The source_02 prefix is a historical accepted source-contract identifier, not
-- a statement that the source belongs to Layer 2 SectorContextModel.

UPDATE trading_registry
SET applies_to = 'trading-data;trading-model;model_03_target_state_vector;target_state_vector_model;anonymous_target_candidate_builder;source_03_target_state',
    note = '02 historical source-contract identifier for Layer 3 anonymous target candidate input preparation; fetches ETF holdings for Layer 2 selected/prioritized sector baskets and writes trading_data.source_02_target_candidate_holdings before source_03_target_state / feature_03_target_state_vector construction. It is not a Layer 2 SectorContextModel source surface.',
    updated_at = NOW()
WHERE key = 'SOURCE_02_TARGET_CANDIDATE_HOLDINGS';
