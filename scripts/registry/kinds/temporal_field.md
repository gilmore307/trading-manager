# Temporal Field

## Meaning

`temporal_field` names fields whose values are dates, times, datetimes, timestamps, availability times, effective times, or window bounds.

## Register Here

Register date/time field names such as created_at, updated_at, event_time, available_time, as_of_date, expiration, window_start, and window_end.

## Do Not Register Here

- durations as counts;
- numeric windows;
- percentiles;
- status values;
- identity fields;
- path fields;
- free-text timestamp policy notes;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.
