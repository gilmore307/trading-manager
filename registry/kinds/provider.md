# Provider

## Kind Boundary

External data/provider organizations, platforms, or authoritative source surfaces that own or publish source capabilities consumed by trading repositories.

A provider names the source owner or provider surface itself, not an implemented adapter and not a specific endpoint/record family.

## Range

Register providers when the source identity is useful for source selection, entitlement review, documentation, secret alias routing, or capability ownership.

Use `payload` for a stable snake_case provider key. Use `path` for public provider documentation or the authoritative source home page. Use `applies_to` for repositories, adapters, or capability scopes that consume the provider.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- source/provider record families, endpoint families, raw inputs, or entitlement-gated capabilities, which belong in `source_capability`;
- implemented adapters/interfaces, which belong in `data_source`;
- manager-facing bundles, which belong in `data_bundle`;
- final saved data shapes with accepted current storage contracts, which belong in `data_kind`;
- ordinary glossary-only concepts with no provider/source identity role, which belong in `term`.
