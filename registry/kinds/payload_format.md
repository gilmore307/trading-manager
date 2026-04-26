# Payload Format

## Kind Boundary

Registered values allowed in the `trading_registry.payload_format` column.

## Range

Use this kind for payload value-format tokens that describe how consumers should interpret the text stored in a row's `payload` column.

The SQL `trading_registry_payload_format_check` constraint and the registered `payload_format` rows must stay aligned.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- registry fields; use `field`;
- status/outcome values; use the relevant status kind;
- helper methods or source files; use `script` only for stable callable helper/automation exports;
- local parsing helpers or test utilities;
- one-off component-local formats that are not part of the trading-wide registry contract.
