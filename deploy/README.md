# Deploy Templates

`deploy/` stores reviewed host-installation templates only. Committing a template does not install or enable it on any host.

- `systemd/trading-manager-historical-scheduler.service` — reviewed always-on daemon service template for the historical modeling scheduler; this is the intended runtime owner once installed/enabled.
- `systemd/trading-manager-historical-scheduler.env` — optional `/etc/default/` override template for month cursor and tick interval settings.
- `logrotate/trading-manager-historical-scheduler` — optional rotation policy for the scheduler decision JSONL log.

Host activation is an operator action: copy the template into the host service manager, review paths/options/gates, then enable/start it explicitly. Committed templates do not mutate host services by themselves.
