# Config

## Kind Boundary

Non-secret configuration keys and secret-alias references. Payloads may contain secret aliases but must never contain secret values.

## Range

Use for non-secret defaults and secret aliases only. Never store raw tokens, passwords, or connection strings.

## Entries

| id | key | payload_format | payload | note | source_migration |
|---|---|---|---|---|---|
| `cfg_J7D1K5RP` | `DEFAULT_TIMEZONE` | `text` | `America/New_York` | default shared timezone for this server | `002_bootstrap_universal_catalog.sql` |
| `cfg_M8R4V1TZ` | `NETWORK_FRAMEWORK_CLIENT_RUNTIME_BUNDLE_POLICY` | `text` | `bundled_electron_runtime` | approved packaged-client runtime policy: bundle the Electron runtime so the user does not need to install Node.js | `004_register_network_framework_packaging_defaults.sql` |
| `cfg_L2Q8M5TX` | `NETWORK_FRAMEWORK_COMMAND_CONSOLE_POLICY` | `text` | `hide_command_consoles_show_gui` | approved packaged-client policy: hide command-line console windows while preserving GUI/tray surfaces | `002_bootstrap_universal_catalog.sql` |
| `cfg_N7L3R6VK` | `NETWORK_FRAMEWORK_COMPANION_PORT` | `text` | `18790` | approved default server-side port for the network-framework read-only companion endpoint | `004_register_network_framework_packaging_defaults.sql` |
| `cfg_C6V1K9NP` | `NETWORK_FRAMEWORK_COMPANION_SERVICE_MANAGER` | `text` | `systemd` | approved service manager for the server-side network-framework companion process | `004_register_network_framework_packaging_defaults.sql` |
| `cfg_X6M1R9PW` | `NETWORK_FRAMEWORK_COMPANION_STATUS_URL_KEY` | `text` | `companionStatusUrl` | approved local config key for the network-framework read-only companion status URL | `002_bootstrap_universal_catalog.sql` |
| `cfg_F4X8M2QD` | `NETWORK_FRAMEWORK_COMPANION_TLS_PROVIDER` | `text` | `tailscale_cert` | approved TLS certificate source for the tailnet-scoped network-framework companion | `004_register_network_framework_packaging_defaults.sql` |
| `cfg_P4R8T2LM` | `NETWORK_FRAMEWORK_COMPANION_TOKEN_SECRET_ALIAS` | `text` | `network-framework/companion-token` | approved config key for the phase-1 network-framework companion bearer token secret alias; the catalog stores the alias reference, not the secret value or file contents | `002_bootstrap_universal_catalog.sql` |
| `cfg_B4L8T2XC` | `NETWORK_FRAMEWORK_DASHBOARD_URL_KEY` | `text` | `dashboardUrl` | approved local config key for the network-framework dashboard URL | `002_bootstrap_universal_catalog.sql` |
| `cfg_P7W3F9XA` | `NETWORK_FRAMEWORK_DEFAULT_INTERNET_PROXY_EXIT_NODE` | `text` | `openclaw` | approved default Tailscale exit-node host name for the personal network-framework deployment | `005_register_network_framework_internet_proxy_defaults.sql` |
| `cfg_E2L9H6QW` | `NETWORK_FRAMEWORK_DESKTOP_RUNTIME` | `text` | `electron` | approved desktop runtime for the network-framework packaged Windows client | `004_register_network_framework_packaging_defaults.sql` |
| `cfg_V7R3N9SK` | `NETWORK_FRAMEWORK_INSTALLER_KIND` | `text` | `nsis` | approved installer technology for the network-framework packaged Windows client | `002_bootstrap_universal_catalog.sql` |
| `cfg_H5N1K8VD` | `NETWORK_FRAMEWORK_INSTALL_PATH_KEY` | `text` | `installPath` | approved local config key for the network-framework installed app path | `002_bootstrap_universal_catalog.sql` |
| `cfg_V5C2K8ND` | `NETWORK_FRAMEWORK_INTERNET_PROXY_ALLOW_LAN_ACCESS_KEY` | `text` | `allowLanAccess` | approved local config key for allowing LAN access while using a Tailscale exit node | `005_register_network_framework_internet_proxy_defaults.sql` |
| `cfg_H6Q9L3ZM` | `NETWORK_FRAMEWORK_INTERNET_PROXY_EXIT_NODE_KEY` | `text` | `exitNode` | approved local config key for the preferred Tailscale exit-node name | `005_register_network_framework_internet_proxy_defaults.sql` |
| `cfg_R8N4T2PX` | `NETWORK_FRAMEWORK_INTERNET_PROXY_PROVIDER` | `text` | `tailscale_exit_node` | approved Internet proxy provider for the network-framework packaged client: Tailscale exit node | `005_register_network_framework_internet_proxy_defaults.sql` |
| `cfg_K5P7N2XC` | `NETWORK_FRAMEWORK_LOCAL_CONFIG_PATH` | `text` | `%LOCALAPPDATA%\NetworkFramework\config\packaged-client.json` | approved local config file path for the network-framework packaged Windows client | `004_register_network_framework_packaging_defaults.sql` |
| `cfg_C9W4P7RA` | `NETWORK_FRAMEWORK_LOCAL_CONFIG_STORE` | `text` | `project_config_boundary` | approved packaged-client local settings boundary; do not introduce Windows Registry-backed settings in this slice | `002_bootstrap_universal_catalog.sql` |
| `cfg_T6Y2B9LM` | `NETWORK_FRAMEWORK_NODE_NAME_KEY` | `text` | `nodeName` | approved local config key for the network-framework OpenClaw node name | `002_bootstrap_universal_catalog.sql` |
| `cfg_R8D4M2NZ` | `NETWORK_FRAMEWORK_OPENCLAW_NODE_SERVICE_NAME` | `text` | `OpenClawNode` | approved default OpenClaw Node service name for the network-framework packaged client | `002_bootstrap_universal_catalog.sql` |
| `cfg_Y3D8F6LA` | `NETWORK_FRAMEWORK_PREREQUISITE_SETUP_POLICY` | `text` | `detect_first_reuse_first_install_assist` | approved prerequisite setup policy: detect valid installs first, reuse them, and install or guide only missing prerequisites | `004_register_network_framework_packaging_defaults.sql` |
| `cfg_B2W5C8HX` | `NETWORK_FRAMEWORK_SERVER_TAILSCALE_LOGIN_MODE` | `text` | `operator_browser_login` | approved server-side Tailscale login mode: operator completes browser or identity-provider login | `004_register_network_framework_packaging_defaults.sql` |
| `cfg_Q9T2B5RM` | `NETWORK_FRAMEWORK_SERVICE_PRIVILEGE_POLICY` | `text` | `installer_elevates_runtime_prompts_as_needed` | approved privilege policy: installer may request elevation for setup while runtime prompts only when privileged service actions are needed | `004_register_network_framework_packaging_defaults.sql` |
| `cfg_W1J6C8LP` | `NETWORK_FRAMEWORK_SMB_DRIVE_LETTER_KEY` | `text` | `smbDriveLetter` | approved local config key for the network-framework SMB drive letter | `002_bootstrap_universal_catalog.sql` |
| `cfg_N9K3V5QA` | `NETWORK_FRAMEWORK_SMB_REMOTE_PATH_KEY` | `text` | `smbRemotePath` | approved local config key for the network-framework SMB UNC path | `002_bootstrap_universal_catalog.sql` |
| `cfg_P3F7X1QK` | `NETWORK_FRAMEWORK_VPN_SERVICE_NAME` | `text` | `Tailscale` | approved default VPN service name for the network-framework packaged client | `002_bootstrap_universal_catalog.sql` |
| `cfg_U8C2D6YA` | `OPENCLAW_DATABASE_URL_SECRET_ALIAS` | `text` | `openclaw/database-url` | approved config key for the active OpenClaw PostgreSQL database URL secret alias; the catalog stores the alias reference, not connection secret material | `002_bootstrap_universal_catalog.sql` |
