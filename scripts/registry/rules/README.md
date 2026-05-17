# Registry Rules

This directory owns cross-kind rules for the trading registry.

## Files

- `kind-routing.md` — tie-breakers when a proposed row could fit multiple kinds.
- `data-kind-contract.md` — when a concept may become a final saved `data_kind`.
- `model-layer-naming.md` — naming rules for model-layer source, feature, and model surfaces.

## Boundary

Per-kind meanings live in `../kinds/`. Concrete rows live in SQL migrations. This directory should contain durable rules only, not dated investigation notes or migration history.
