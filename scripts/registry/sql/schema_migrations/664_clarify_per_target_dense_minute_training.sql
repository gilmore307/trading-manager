-- Clarify that M07/M08 train dense minute rows per selected target, not only trigger minutes.

UPDATE trading_registry
SET payload = 'per_selected_target_dense_minute_training;train_staged_entry_exit;train_risk_based_add_reduce;train_thesis_aware_high_sell_low_buy;no_ad_hoc_execution_scalping;model_07_projects_target_exposure_gap;model_08_owns_tranche_plan;component_03_uses_model_evidence_for_add_reduce;component_05_executes_current_tranche_quantity;component_06_must_not_change_quantity',
    note = 'Accepted policy for staged exposure management. For each selected training target, M07/M08 train dense eligible minute sequences, including ordinary no-change, maintain, and no-trade minutes; they must not train only action-triggered minutes. The exclusion is only against all-market every-listed-symbol discovery scans, which belong upstream. M07 trains target exposure and position-gap utility, including price-location and risk evidence. M08 owns tranche planning, risk-based add/reduce, and thesis-aware high-sell/low-buy style exposure adjustment. C03 may use those trained model outputs for lifecycle add/reduce decisions. C05 executes the current tranche as final order quantity. C06 validates/submits and must not change quantity. This is not an ad hoc scalping layer.',
    updated_at = NOW()
WHERE key = 'TRANCHE_EXPOSURE_MANAGEMENT_POLICY';
