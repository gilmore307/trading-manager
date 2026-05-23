-- Register Layer 4 event-amplified session-gap holding-risk score family.

UPDATE trading_registry
SET payload = '4_event_strategy_failure_risk_score_<horizon>;4_event_entry_block_pressure_score_<horizon>;4_event_exposure_cap_pressure_score_<horizon>;4_event_strategy_disable_pressure_score_<horizon>;4_event_path_risk_amplifier_score_<horizon>;4_event_session_gap_risk_score_<horizon>;4_event_evidence_quality_score_<horizon>;4_event_applicability_confidence_score_<horizon>',
    note = 'Accepted Layer 4 event-failure-risk score-family namespace. These score families require reviewed evidence and are pre-alpha failure-risk conditioning only. Session-gap risk covers reviewed event-amplified overnight, weekend, holiday, halt, or other non-continuous-market holding risk; base calendar/session exposure without a reviewed event belongs to Layer 6 risk policy. These fields do not authorize standalone event alpha, action selection, sizing, execution, or broker/account mutation.',
    updated_at = now()
WHERE kind = 'config'
  AND key = 'EVENT_FAILURE_RISK_VECTOR_SCORE_FAMILIES';

UPDATE trading_registry
SET note = 'Layer 4 EventFailureRiskModel output vector for reviewed event/strategy-failure conditioning before AlphaConfidenceModel. It carries failure-risk, block/cap/disable pressure, path-risk amplification, session-gap holding risk, evidence quality, applicability confidence, and reason refs; it is not standalone directional alpha or an order instruction.',
    updated_at = now()
WHERE kind = 'term'
  AND key = 'EVENT_FAILURE_RISK_VECTOR';

UPDATE trading_registry
SET note = 'Layer 4 boundary policy: EventFailureRiskModel accepts only agent-reviewed event/strategy-failure factors, including event-amplified overnight/weekend/holiday/session-gap holding risk, and outputs conditioning for Layer 5 AlphaConfidenceModel. EventRiskGovernor may propose promotions, but no family enters Layer 4 without evidence packet plus agent review.',
    updated_at = now()
WHERE kind = 'config'
  AND key = 'EVENT_FAILURE_RISK_BOUNDARY_POLICY';
