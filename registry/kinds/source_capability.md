# Source Capability

## Kind Boundary

Provider/source capability identifiers for source-level record families, endpoint families, raw inputs, transient evidence, or entitlement-gated source categories that may inform implemented data sources but are not accepted final saved data shapes.

A source capability is narrower than a `data_source` adapter and broader than a runtime field. It records what a source can expose or what an adapter may use internally, without granting `data_kind` status.

## Range

Register source capabilities when the concept is useful for source availability, entitlement review, adapter planning, or documenting transient/raw inputs.

Use `payload` for the stable snake_case capability key. Use `path` for public provider documentation when that is the best locator. Use `applies_to` for the owning data source, provider, or source-interface scope.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- final saved data shapes with accepted templates, which belong in `data_kind`;
- implemented source adapters, which belong in `data_source`;
- manager-facing bundles, which belong in `data_bundle`;
- provider/company names, which belong in `term`;
- ordinary glossary-only concepts with no source/interface role, which belong in `term`;
- runtime fields, which belong in `field`.
