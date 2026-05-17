# Provider

## Meaning

`provider` names external organizations, platforms, or authoritative source surfaces that publish data consumed by active feeds.

## Register Here

Register provider identities useful for source selection, entitlement review, docs, secret alias routing, and capability ownership.

## Do Not Register Here

- endpoint families;
- implemented adapters;
- control-plane sources;
- final saved shapes;
- glossary-only concepts;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.
