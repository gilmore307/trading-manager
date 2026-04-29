# temporal_field

Canonical shared field names whose values are dates, times, datetimes, timestamps, or availability/effective-time markers.

Use this kind for fields such as `created_at`, `updated_at`, `event_time`, `available_time`, `as_of_date`, `expiration`, `window_start`, and `window_end`.

Rules:

- The row payload is the field/column name and should use `payload_format = field_name`.
- Values carried by these fields must use ISO-8601 semantics, not locale-dependent forms such as `YY/MM/DD`, `MM/DD/YY`, or `DD/MM/YY`.
- Date-only values use `YYYY-MM-DD`.
- Datetime/timestamp values must include explicit timezone semantics. Normalized final outputs default to America/New_York; do not encode the default timezone in the field payload/key (for example, use `event_time`, not `event_time_et`).
- Keep non-temporal field names in `field`.
- Keep durations, windows as counts, percentiles, ranks, and textual timestamp policy descriptions out of this kind unless the field value itself is a date/time/datetime.
