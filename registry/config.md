# Config

## Kind Boundary

Non-secret configuration keys and secret-alias references. Payloads may contain secret aliases but must never contain secret values.

## Range

Register non-secret defaults and secret aliases only. Never store raw tokens, passwords, API keys, broker credentials, exchange keys, or connection strings.

## Concrete Entries

Concrete registry entries for this kind live in the SQL-backed registry, not in this Markdown file.

Use this file to define what the kind means, what belongs here, and what must be rejected or re-scoped. Do not duplicate active item rows here.
