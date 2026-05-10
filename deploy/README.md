# Deploy Templates

`deploy/` stores reviewed host-installation templates only. Committing a template does not install or enable it on any host.

- `systemd/trading-manager-historical-scheduler.service` — optional always-on daemon service for the historical-training scheduler.
- `logrotate/trading-manager-historical-scheduler` — optional rotation policy for the scheduler decision JSONL log.

Host activation is an operator action: copy the template into the host service manager, review paths/options, then enable/start it explicitly.
