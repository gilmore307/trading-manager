-- Keep SECTOR_CONTEXT_STATE canonically owned by the Layer 2 contract while
-- preserving its Layer 3 TargetStateVector sector-state feature-group usage.
UPDATE trading_registry
SET path = 'trading-model/src/models/model_02_sector_context/sector_context_state_contract.md',
    note = 'Conceptual Layer 2 SectorContextModel state: market-context-conditioned sector/industry basket state with signed relative direction kept separate from direction-neutral tradability, trend quality, transition risk, handoff bias, and reliability evidence. Also carried as a Layer 3 sector_state_features group inside TargetStateVector rows; it must not become final target/action selection.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SECTOR_CONTEXT_STATE';
