-- Move the anonymous target candidate builder path/ownership under Layer 3.
-- The term remains stable, but its source contract now lives inside the
-- StrategySelectionModel package as a candidate-preparation sub-boundary rather
-- than a peer model package.
UPDATE trading_registry
SET
  path = 'trading-model/src/models/model_03_strategy_selection/anonymous_target_candidate_builder/target_candidate_builder_contract.md',
  applies_to = 'trading-model;trading-data;sector_context_model;model_03_strategy_selection;strategy_selection_model',
  note = 'Layer 3 candidate-preparation sub-boundary inside the StrategySelectionModel package. It expands selected/prioritized sector or industry baskets from SectorContextModel into anonymous target candidates while keeping real ticker/company identity in audit/routing metadata outside model-facing fitting vectors.',
  updated_at = CURRENT_TIMESTAMP
WHERE id = 'trm_ATCB001';

UPDATE trading_registry
SET
  applies_to = 'trading-model;model_03_strategy_selection;strategy_selection_model;anonymous_target_candidate_builder',
  updated_at = CURRENT_TIMESTAMP
WHERE id IN ('trm_ATF001', 'trm_TCI001');

UPDATE trading_registry
SET
  applies_to = 'trading-data;trading-model;model_03_strategy_selection;anonymous_target_candidate_builder',
  updated_at = CURRENT_TIMESTAMP
WHERE id = 'dbu_SECINPUT';
