# Configuration templates

These files are examples, not active configurations. Replace every placeholder before use.

- `mcp.example.json`: generic MCP host command mapping; adapt the wrapper keys to your host.
- `aidus_config.example.json`: merge these MCP settings into a compatible Aidus installation's local configuration.
- `agents.example.yml`: AgentPool-style MCP manifest. Set a supported model and absolute prompt/bridge paths. The installed Aidus Core can require this content in its own `agents.yml`.

Do not copy real keys or the FontLab token into these files. Do not overwrite existing provider settings when merging the MCP section. Keep resolved local configurations untracked.
