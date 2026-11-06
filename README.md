# Aidus Kit

API references, agent instructions, and connection templates for using Aidus or another MCP assistant with FontLab 9.

## Setup

You need FontLab 9, its matching `fontlab-mcp` bridge, and an MCP-capable Aidus installation or other MCP host. The external Python helpers require Python 3.10+ and no additional packages.

1. Start FontLab and enable **Preferences → Aidus → Allow external MCP clients to control FontLab**.
2. Set the bridge executable path in your host. Use [mcp.example.json](config/mcp.example.json) for a generic host, or merge [aidus_config.example.json](config/aidus_config.example.json) into your Aidus configuration. Preserve your existing provider settings.
3. For Aidus, adapt [agents.example.yml](config/agents.example.yml): replace the model, bridge path, and prompt path. Apply it to the `agents.yml` used by your Aidus Core. The Core can also read the bridge path from `FONTLAB_MCP_PATH`.
4. Load [AIDUS.md](prompts/AIDUS.md) as the agent instructions and make this kit's reference files available to the agent.
5. Ask the assistant to list the open fonts without changing them.

On macOS, the bridge may be inside `FontLab 9.app/Contents/MacOS`. If it is supplied separately, use that executable instead. A bridge command is an executable path, not a shell command. The bridge reads its authentication token automatically; do not put tokens or provider keys into these templates.

You can check the connection without editing a font:

```sh
python3 docs/mcp/client.py "/absolute/path/to/fontlab-mcp"
```

This discovers the installed tools and lists open fonts. Tool availability and argument schemas from the running application take precedence over bundled references. Updating reference files does not add capabilities to an older application.

## References

| Task | Reference |
|---|---|
| Write FontLab Python scripts | [Scripting guide](Resources/fontlab_python_agent_guide.md) |
| Small Python/MCP context | [Chat JSON](Resources/fontlab_python_api_chat.json) or [text appendix](Resources/chat_system_prompt_appendix.md) |
| Full Python API | [JSON](Resources/fontlab_python_api.json) or [text](Resources/fontlab_python_api.llm.md) |
| MCP tools, exact arguments, results, and examples | [MCP reference](docs/mcp/fontlab-mcp.json) |
| Writable glyph JSON | [VFJ schema](Resources/vfj_schema.json) |
| Native action names | [Action catalog](Resources/fontlab_action_catalog.json) |

Retrieve the relevant definition rather than loading every catalog into each request:

```sh
python3 tools/reference.py class flLayer --member addComponent
python3 tools/reference.py mcp set_glyph
python3 tools/reference.py vfj component
python3 tools/reference.py search "notifyChangesApplied" --limit 5
```

In the Python catalogs, `m` contains instance methods, `s` static methods, `p` property names, and `pd` property descriptions and access modes.

## Examples

- [embedded_inspect.py](examples/embedded_inspect.py): run inside FontLab's Python environment to inspect the current font and masters.
- [preview_construction.py](examples/preview_construction.py): validate a construction recipe through the bridge. It requires advertised dry-run support and never commits the result.

```sh
python3 examples/preview_construction.py --bridge "/absolute/path/to/fontlab-mcp" --font-id 101 --glyph Aacute.preview --layer Regular --recipe '=A+acutecomb@top[_top]'
```

Replace the sample font ID, glyph names, layer, and anchors with values discovered in your font.

## Working safely

Resolve the intended font, glyphs, and layers before editing. Use supported previews, preserve unrelated data, and verify readback. `set_glyph` replaces the whole glyph; it is not a partial patch. Its input must be full writable VFJ, not a construction summary or truncated output.

External MCP clients have real access to fonts, files, preferences, and Python execution. They do not inherit built-in Chat's per-tool confirmation dialogs. Keep actions within the user's request and use one mutation stream at a time. After a timeout, inspect state before retrying.

## Troubleshooting

| Problem | Check |
|---|---|
| Cannot connect | FontLab is running; external MCP access is enabled; bridge path is correct |
| Authentication failure | App and bridge match and run under the intended user |
| Missing tool or Python member | Inspect installed capabilities and the exact object type |
| Aidus ignores the prompt | Check its active manifest and prompt path, then reload |
| Built-in Chat uses an old appendix | Check for a user-data override masking the bundled file |

The text appendix is reference material, not a replacement for FontLab's entire system prompt. Use the application's supported override mechanism if you install a custom appendix.

## License

[MIT](LICENSE.md), copyright 2026 Fontlab Ltd. The license covers this kit. FontLab, Aidus, and separately distributed software retain their own licenses.
