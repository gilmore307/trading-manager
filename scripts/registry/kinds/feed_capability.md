# Feed Capability

## Meaning

`feed_capability` names record families, endpoint families, entitlement-gated capabilities, or raw inputs exposed by a provider/feed.

## Register Here

Register capabilities useful for entitlement review, feed planning, and adapter documentation before they become saved contracts.

## Do Not Register Here

- final data shapes;
- implemented feed connectors;
- control-plane source outputs;
- provider organizations;
- ordinary glossary terms;
- runtime fields;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.
