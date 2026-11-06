# Setup

## FontLab and the bridge

Use a FontLab 9 build that supplies the matching `fontlab-mcp` bridge. Start FontLab, then enable **Preferences → Aidus → Allow external MCP clients to control FontLab**. This setting is separate from built-in Chat and is off by default in the source implementation described here.

On macOS a packaged bridge may be located at `/Applications/FontLab 9.app/Contents/MacOS/fontlab-mcp`. Verify the actual location for your installation. On other platforms use the matching executable supplied for that build. This kit contains no native bridge binary and cannot build FontLab. Development app bundles can omit the bridge; in that case supply the matching separately built `mcpbridge/fontlab-mcp` executable. The tested release-build bundle used this layout.

Copy [the generic MCP template](../config/mcp.example.json) into your MCP host's configuration, replacing its placeholder command with the actual executable path. A host-specific configuration layout may differ. The executable path is a JSON string, not a shell command with embedded quotes.

The bridge communicates over stdio and reaches the running desktop application on loopback. It reads the per-user authentication token automatically. Do not copy tokens into configuration, prompts, environment templates, or this repository. An old bridge may fail to authenticate with a newer FontLab build; update the application and bridge together.

Run:

```sh
python3 tools/doctor.py --bridge "/absolute/path/to/fontlab-mcp"
```

The doctor initializes the bridge, discovers tool schemas, and calls `list_fonts` if supported. It does not edit fonts, execute embedded Python, or call a save operation. It reports missing or changed capabilities separately from connection failures. A schema difference is a compatibility signal, not proof of a runtime bug.

## Aidus integration

Use an Aidus release that supports MCP-backed FontLab tools. The verified configuration shape includes `mcp_enabled`, `fontlab_mcp_path`, and an AgentPool-style manifest with `mcp_servers` and `agents`. Older Aidus releases can use a separate legacy tool executor; those tool names and contracts are not interchangeable with this MCP catalog.

1. Install Aidus using its distribution's instructions. Its Core runs outside FontLab; do not install Core dependencies into FontLab's embedded interpreter.
2. Merge [aidus_config.example.json](../config/aidus_config.example.json) into your local Aidus configuration. Preserve existing provider settings. Replace the bridge path.
3. Adapt [agents.example.yml](../config/agents.example.yml) to your installed Aidus/AgentPool version. Replace the model and all path placeholders. Use your configured model provider; the kit makes no provider choice.
4. Point the agent's file prompt at [AIDUS.md](../prompts/AIDUS.md). Give the agent read access or retrieval access to the relevant kit references.
5. Discover tools and begin with an inspection request, such as “List the open fonts without changing them.”

The inspected Aidus Core loads `agents.yml` next to its `boot.py`; it can override the bridge command through `FONTLAB_MCP_PATH`. Do not assume that dropping this kit's YAML into an arbitrary font directory automatically changes that manifest. Prompt file paths must be resolved according to the installed host; use absolute paths when adapting the template.

The templates do not include credentials. Configure provider credentials through the installed Aidus release's supported secret mechanism. Do not commit a local `aidus_config.json` or a resolved manifest containing secrets.

## Built-in FontLab Chat

The updated `Resources/fontlab_python_api_chat.json` and `Resources/chat_system_prompt_appendix.md` are reference snapshots. This kit does not automatically install them into a running application.

For a FontLab source build, regenerate and package the matching Resources files. For an installed application, use its supported user-data override mechanism if available, then reload the relevant context. A user override can mask a newer bundled appendix. Verify the installed behavior; replacing documentation does not add native capabilities to an older binary.

Do not replace FontLab's entire system prompt with the API appendix. The appendix is selected reference material. Keep authorization and host controls in the host's instructions.

## Troubleshooting

| Symptom | Check |
|---|---|
| Bridge executable missing | Use the actual path from the matching installation; the kit does not ship it |
| Connection refused | FontLab running, external MCP access enabled, matching bridge |
| Authentication failure | Matching app/bridge and same authorized user; do not print the token |
| Tool missing | Installed `tools/list`; update the app or choose a supported workflow |
| Python method missing | Exact object type, installed binding, optional module availability |
| Prompt unchanged | Correct Aidus manifest or FontLab user override, then reload |
| Timeout | Outcome may be unknown; inspect state before retrying a mutation |
