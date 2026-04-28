# temporal_field

Canonical shared field names whose values are dates, times, datetimes, timestamps, or availability/effective-time markers.

Use this kind for fields such as `created_at`, `updated_at`, `event_time_et`, `available_time_et`, `as_of_date`, `expiration`, `window_start_et`, and `window_end_et`.

Rules:

- The row payload is the field/column name and should use `payload_format = field_name`.
- Values carried by these fields must use ISO-8601 semantics, not locale-dependent forms such as `YY/MM/DD`, `MM/DD/YY`, or `DD/MM/YY`.
- Date-only values use `YYYY-MM-DD`.
- Datetime/timestamp values must include explicit timezone semantics. Fields ending in `_et` are America/New_York timestamps and should be serialized consistently by the producing template or pipeline.
- Keep non-temporal field names in `field`.
- Keep durations, windows as counts, percentiles, ranks, and textual timestamp policy descriptions out of this kind unless the field value itself is a date/time/datetime.
