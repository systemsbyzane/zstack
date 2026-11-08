# Cortex companion (experimental source snapshot)

Minimal loopback status board and macOS launcher. Launcher/reply composer verification is still in progress; this is not a signed or notarized binary release.

Requires Node 20+, pnpm; the Mac installer additionally requires Swift command-line tools. No dependency install is required.

Set CORTEX_STATUS_PATH to your chief's sanitized status.json and CORTEX_SCHEMA_PATH to the included status.schema.json, then run `pnpm start`. Open http://127.0.0.1:65200.

Optional reply configuration: CORTEX_CHIEF_THREAD_ID, CORTEX_ENVIRONMENT_ID, CORTEX_T3_CLI. Keep these local. The reply bridge uses your authenticated local T3 CLI. Inspect before enabling. No credentials or user state are bundled.

`./install-macos.sh` builds a local app and Desktop shortcut. It refuses existing targets. Configure the server environment in its launch context before using it; Finder does not automatically inherit terminal environment variables. This snapshot requires local configuration for the launcher.

Status is last-reported, not proof of live agent activity. Refresh manually. See the root MIT license.
