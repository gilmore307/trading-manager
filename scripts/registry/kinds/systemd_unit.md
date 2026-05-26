# Systemd Unit

## Meaning

`systemd_unit` names reviewed checked-in systemd unit files.

## Register Here

Register durable `.service`, `.timer`, and `.path` unit files that are part of an accepted repository deployment surface.

## Do Not Register Here

- service runtime status;
- environment variable defaults;
- service names consumed as ordinary config values;
- operational policies that only mention systemd;
- scripts called by systemd units;
- host-local installed unit instances;

## Row Rules

- `payload` must hold the unit filename or semicolon-separated unit filenames.
- `path` must point to the checked-in unit file or files.
- `applies_to` should name the owning repository, unit manager, unit type, and first real runtime boundary.
- Host installation, enablement, restart, or daemon reload remains an operator/service action outside registry sync.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.
