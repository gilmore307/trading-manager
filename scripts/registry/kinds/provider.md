# Provider

## Kind Boundary

Current external data/provider organizations, platforms, or authoritative source surfaces that own or publish source capabilities consumed by active feed interfaces.

A provider names the current source owner or provider surface itself, not an implemented adapter and not a specific endpoint/record family. Historical, fallback, secret-only, or documentation-only source references remain `term` rows until an active feed interface uses them.

## Range

Register providers when the source identity is current and useful for source selection, entitlement review, documentation, secret alias routing, or capability ownership.

Use `payload` for a stable snake_case provider key. Use `path` for public provider documentation or the authoritative source home page. Use `applies_to` for repositories, adapters, or capability scopes that consume the provider.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- feed/provider record families, endpoint families, raw inputs, or entitlement-gated capabilities, which belong in `feed_capability`;
- implemented adapters/interfaces, which belong in `data_source`;
- control-plane-facing sources, which belong in `data_source`;
- final saved data shapes with accepted current storage contracts, which belong in `data_kind`;
- ordinary glossary-only concepts with no provider/feed identity role, which belong in `term`.
