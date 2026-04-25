-- Register network-framework Internet proxy VPN defaults.
-- Target engine: PostgreSQL.
-- These are small, stable config defaults reviewed for the packaged-client exit-node slice.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, note)
VALUES
  ('cfg_R8N4T2PX', 'config', 'NETWORK_FRAMEWORK_INTERNET_PROXY_PROVIDER', 'text', 'tailscale_exit_node', 'approved Internet proxy provider for the network-framework packaged client: Tailscale exit node'),
  ('cfg_H6Q9L3ZM', 'config', 'NETWORK_FRAMEWORK_INTERNET_PROXY_EXIT_NODE_KEY', 'text', 'exitNode', 'approved local config key for the preferred Tailscale exit-node name'),
  ('cfg_V5C2K8ND', 'config', 'NETWORK_FRAMEWORK_INTERNET_PROXY_ALLOW_LAN_ACCESS_KEY', 'text', 'allowLanAccess', 'approved local config key for allowing LAN access while using a Tailscale exit node'),
  ('cfg_P7W3F9XA', 'config', 'NETWORK_FRAMEWORK_DEFAULT_INTERNET_PROXY_EXIT_NODE', 'text', 'openclaw', 'approved default Tailscale exit-node host name for the personal network-framework deployment')
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  note = EXCLUDED.note;
