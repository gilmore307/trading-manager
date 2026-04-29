# Feed Capability

## Kind Boundary

Provider/feed capability identifiers for feed-level record families, endpoint families, raw inputs, transient evidence, or entitlement-gated provider categories that may inform implemented data feeds but are not accepted final saved data shapes.

A feed capability is narrower than a `data_feed` connector and broader than a runtime field. It records what a feed can expose or what a feed adapter may use internally, without granting `data_kind` status.

## Range

Register feed capabilities when the concept is useful for feed availability, entitlement review, adapter planning, or documenting transient/raw inputs.

Use `payload` for the stable snake_case capability key. Use `path` for public provider documentation when that is the best locator. Use `applies_to` for the owning data feed, provider, or feed-interface scope.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- final saved data shapes with accepted current storage contracts, which belong in `data_kind`;
- implemented feed connectors, which belong in `data_feed`;
- manager-facing source outputs, which belong in `data_source`;
- provider/company/feed-owner names, which belong in `provider`;
- ordinary glossary-only concepts with no feed/interface role, which belong in `term`;
- runtime fields, which belong in `field`.
