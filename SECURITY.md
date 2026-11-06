# Security

Do not commit FontLab MCP tokens, provider API keys, real local configuration files, private fonts, or diagnostic reports containing private metadata.

The matching bridge reads FontLab's per-user token automatically. External MCP access controls a real desktop process and can expose Python execution, file writes, font mutation, and closing documents. It does not inherit built-in Chat's confirmation dialogs. Authorize host-side actions within the user's request.

Keep reports of suspected vulnerabilities free of credentials and private font data. A public security contact has not been configured for this kit; the rights holder must provide one before release.

Read-only examples do not grant permission to run arbitrary downloaded scripts. Inspect scripts and use trusted application/bridge builds. On a timeout, the mutation outcome may be unknown; do not replay it automatically.
