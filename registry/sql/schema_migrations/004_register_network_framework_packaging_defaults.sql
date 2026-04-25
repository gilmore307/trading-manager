-- Register network-framework packaged-client and companion defaults.
-- Target engine: PostgreSQL.
-- These are small, stable config defaults reviewed for cross-project reuse.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, note)
VALUES
  ('cfg_E2L9H6QW', 'config', 'NETWORK_FRAMEWORK_DESKTOP_RUNTIME', 'text', 'electron', 'approved desktop runtime for the network-framework packaged Windows client'),
  ('cfg_M8R4V1TZ', 'config', 'NETWORK_FRAMEWORK_CLIENT_RUNTIME_BUNDLE_POLICY', 'text', 'bundled_electron_runtime', 'approved packaged-client runtime policy: bundle the Electron runtime so the user does not need to install Node.js'),
  ('cfg_K5P7N2XC', 'config', 'NETWORK_FRAMEWORK_LOCAL_CONFIG_PATH', 'text', '%LOCALAPPDATA%\\NetworkFramework\\config\\packaged-client.json', 'approved local config file path for the network-framework packaged Windows client'),
  ('cfg_Y3D8F6LA', 'config', 'NETWORK_FRAMEWORK_PREREQUISITE_SETUP_POLICY', 'text', 'detect_first_reuse_first_install_assist', 'approved prerequisite setup policy: detect valid installs first, reuse them, and install or guide only missing prerequisites'),
  ('cfg_Q9T2B5RM', 'config', 'NETWORK_FRAMEWORK_SERVICE_PRIVILEGE_POLICY', 'text', 'installer_elevates_runtime_prompts_as_needed', 'approved privilege policy: installer may request elevation for setup while runtime prompts only when privileged service actions are needed'),
  ('cfg_C6V1K9NP', 'config', 'NETWORK_FRAMEWORK_COMPANION_SERVICE_MANAGER', 'text', 'systemd', 'approved service manager for the server-side network-framework companion process'),
  ('cfg_F4X8M2QD', 'config', 'NETWORK_FRAMEWORK_COMPANION_TLS_PROVIDER', 'text', 'tailscale_cert', 'approved TLS certificate source for the tailnet-scoped network-framework companion'),
  ('cfg_N7L3R6VK', 'config', 'NETWORK_FRAMEWORK_COMPANION_PORT', 'text', '18790', 'approved default server-side port for the network-framework read-only companion endpoint'),
  ('cfg_B2W5C8HX', 'config', 'NETWORK_FRAMEWORK_SERVER_TAILSCALE_LOGIN_MODE', 'text', 'operator_browser_login', 'approved server-side Tailscale login mode: operator completes browser or identity-provider login')
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  note = EXCLUDED.note;
