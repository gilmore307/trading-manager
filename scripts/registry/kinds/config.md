# Config

## Kind Boundary

Non-secret configuration keys and secret-alias references. Payloads may contain secret aliases but must never contain secret values.

## Range

Register non-secret defaults and secret aliases only. Never store raw tokens, passwords, API keys, broker credentials, exchange keys, or connection strings.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- raw secrets;
- source-file locators;
- status values;
- field names;
