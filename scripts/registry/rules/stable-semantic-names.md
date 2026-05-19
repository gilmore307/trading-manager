# Stable Semantic Name Rule

Registry-backed semantic names are interfaces. They must stay stable unless a reviewed migration deliberately replaces the interface.

## Forbidden Drift Suffixes

Do not add drift/version suffixes to active semantic or business names:

```text
_v1 _v2 _old _new _legacy _temp _final
```

This applies to registry `key`, `payload` values when they are contract ids, `applies_to` semantic tokens, task ids, public artifact names, SQL table names, storage folder names, script keys, and contract-type strings emitted by scripts.

## Where Versions Belong

Put version information in explicit metadata or immutable evidence context instead:

```text
schema_version
schema_ref
contract_version
migration number
generated_at / snapshot date
immutable run artifact path
```

Compatibility aliases may exist only when a reviewed migration states the compatibility boundary and active docs identify the stable unversioned name.

## Review Checklist

Before adding a registry row or script-emitted contract type, verify:

- the public semantic name is unversioned;
- any schema or compatibility version lives in metadata;
- the row is not preserving an old route only for convenience;
- active docs and tests assert the stable name.
