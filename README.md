# Aidus Kit

API references, agent instructions, and connection templates for using Aidus or another MCP assistant with FontLab 9.

## Get the kit

Clone the repository, then run the terminal commands below from its root folder:

```sh
git clone https://github.com/Fontlab/aidus-kit.git
cd aidus-kit
```

Alternatively, download and extract the repository ZIP and open a terminal in the extracted folder. No `pip install` is required. This is a reference kit, not an installer for FontLab or Aidus.

## Setup

You need FontLab 9, its matching `fontlab-mcp` bridge, and an MCP-capable Aidus installation or other MCP host. The external Python helpers require Python 3.10+ and no additional packages. Configure your chosen model/provider in Aidus separately. On Windows, you can use `py -3` instead of `python3`; quote paths containing spaces.

1. Start FontLab and enable **Preferences → Aidus → Allow external MCP clients to control FontLab**.
2. Set the bridge executable path in your host. Use [mcp.example.json](config/mcp.example.json) for a generic host, or merge [aidus_config.example.json](config/aidus_config.example.json) into your Aidus configuration. Preserve your existing provider settings.
3. For Aidus, adapt [agents.example.yml](config/agents.example.yml): replace the model, bridge path, and prompt path. Apply it to the `agents.yml` used by your Aidus Core. The Core can also read the bridge path from `FONTLAB_MCP_PATH`.
4. Load [AIDUS.md](prompts/AIDUS.md) as the agent instructions. Give the host file/retrieval access to this kit, or attach the scripting guide and relevant reference excerpts to your conversation. Connecting the FontLab MCP bridge alone does **not** give an agent access to these local files. If the host cannot execute local commands, run `tools/reference.py` yourself and paste its output.
5. Ask the assistant to list the open fonts without changing them.

The kit does not include the native bridge executable. Obtain it with the matching FontLab distribution; if it is absent, ask the distributor for a compatible bridge. On macOS, the bridge may be inside `FontLab 9.app/Contents/MacOS`. If it is supplied separately, use that executable instead. A bridge command is an executable path, not a shell command. The bridge reads its authentication token automatically; do not put tokens or provider keys into these templates.

You can check the connection without editing a font:

```sh
python3 docs/mcp/client.py "/absolute/path/to/fontlab-mcp"
```

A successful check prints JSON containing `tools` and `open_fonts`. An empty font list is normal when no font is open. This discovers the installed tools and lists open fonts. Tool availability and argument schemas from the running application take precedence over bundled references. Updating reference files does not add capabilities to an older application.

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

- [embedded_inspect.py](examples/embedded_inspect.py): open and run this file with FontLab’s script runner to inspect the current font and masters. It prints `package_id`, the active `master`, and available `masters`; it also works with no font open. Do not run it in a system terminal expecting the `fontlab` module to be available.
- [preview_construction.py](examples/preview_construction.py): validate a construction recipe through the bridge. It requires advertised dry-run support and never commits the result.

```sh
python3 examples/preview_construction.py --bridge "/absolute/path/to/fontlab-mcp" --font-id 101 --glyph A.preview --layer "Regular" --recipe "=A"
```

Open a font containing glyph `A` before trying this example. Obtain its current ID from the connection check’s `open_fonts` result or the embedded script’s `package_id`; use an exact master name from `masters`. Replace `101` and `Regular` accordingly. Font IDs belong to the current session and can change after reopening.

Choose a destination glyph name that does not already exist, such as `A.preview`. The example validates `=A` without creating that destination; success returns `status: "validated"`. The destination must be new or empty because replacement is disabled. There is no commit switch.

For an accent preview, use `"=A+acutecomb@top[_top]"` only after confirming that both source glyphs and the named anchors exist. A missing glyph, master, or anchor should produce an error rather than trigger a fallback edit.

## Working safely

Resolve the intended font, glyphs, and layers before editing. Use supported previews, preserve unrelated data, and verify readback. `set_glyph` replaces the whole glyph; it is not a partial patch. Its input must be full writable VFJ, not a construction summary or truncated output.

External MCP clients have real access to fonts, files, preferences, and Python execution. They do not inherit built-in Chat's per-tool confirmation dialogs. Keep actions within the user's request and use one mutation stream at a time. After a timeout, inspect state before retrying.

## Troubleshooting

| Problem | Check |
|---|---|
| `fontlab` cannot be imported | Run embedded scripts in FontLab; terminal helpers use the MCP bridge |
| Bridge executable missing | Install the matching bridge and replace the placeholder path |
| Cannot connect | FontLab is running; external MCP access is enabled; bridge path is correct |
| Authentication failure | App and bridge match and run under the intended user |
| Missing tool or Python member | Inspect installed capabilities and the exact object type |
| Aidus ignores the prompt | Check its active manifest and prompt path, then reload |
| Built-in Chat uses an old appendix | Check for a user-data override masking the bundled file |

The text appendix is reference material, not a replacement for FontLab's entire system prompt. Use the application's supported override mechanism if you install a custom appendix.

## License

[MIT](LICENSE.md), copyright 2026 Fontlab Ltd. The license covers this kit. FontLab, Aidus, and separately distributed software retain their own licenses.
