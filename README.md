# FontLab Aidus Kit

A portable reference and integration kit for using Aidus and other MCP-capable assistants with FontLab 9. It contains agent instructions, Python API references, exact MCP tool schemas, VFJ definitions, configuration templates, and small Python helpers.

**License:** [MIT](LICENSE.md), covering this kit’s documentation and helper scripts. This repository does not include the FontLab application, the `fontlab-mcp` executable, the Aidus application, model credentials, or font files.

Repository: [Fontlab/aidus-kit](https://github.com/Fontlab/aidus-kit).

## Start here

1. Read [setup](docs/SETUP.md) and enable external MCP access in a compatible running FontLab build.
2. Point the MCP host at the matching `fontlab-mcp` executable.
3. Load [the agent instructions](prompts/AIDUS.md), then retrieve relevant API sections as needed.
4. Run a read-only capability check:

   ```sh
   python3 tools/doctor.py --bridge "/absolute/path/to/fontlab-mcp"
   ```

5. Inspect fonts without modifying them:

   ```sh
   python3 examples/inspect_font.py --bridge "/absolute/path/to/fontlab-mcp"
   ```

Use Python 3.10 or newer for the external helpers. They use the standard library only. FontLab-dependent Python scripts run inside FontLab's embedded Python, not in this external interpreter. The kit does not install or update either runtime.

## Choose the right reference

| Need | File |
|---|---|
| Small starting prompt | [prompts/AIDUS.md](prompts/AIDUS.md) |
| Detailed Python scripting rules | [Python agent guide](Resources/fontlab_python_agent_guide.md) |
| Compact Python and MCP reference | [Chat JSON](Resources/fontlab_python_api_chat.json), [text appendix](Resources/chat_system_prompt_appendix.md) |
| Full Python API | [JSON](Resources/fontlab_python_api.json), [text](Resources/fontlab_python_api.llm.md) |
| Exact MCP parameters and examples | [MCP JSON](docs/mcp/fontlab-mcp.json) |
| MCP workflows and behavior | [human guide](docs/mcp/GUIDE.md), [agent reference](docs/mcp/LLM.md) |
| Full writable VFJ structure | [schema catalog](Resources/vfj_schema.json), [schema reference](docs/mcp/VFJ.md) |
| Native action names | [action catalog](Resources/fontlab_action_catalog.json) |
| Configuration | [templates](config/README.md) |

Retrieve small sections rather than putting every reference into every model request:

```sh
python3 tools/reference.py class flLayer --member addComponent
python3 tools/reference.py mcp set_glyph
python3 tools/reference.py vfj component
python3 tools/reference.py search "notifyChangesApplied" --limit 5
```

## Working rules

- Discover `tools/list` in the actual running application. This snapshot describes source capabilities; it does not promise every FontLab 9 release supports them.
- Resolve the font, glyph, and layer explicitly. Prefer focused native tools when they match the task.
- Distinguish generating Python from executing it. Respect the host's execution policy.
- Read before writing, use supported dry runs, preserve unrelated data, and verify results.
- Full `set_glyph` replaces a glyph. Construction summaries are not writable VFJ.
- Use one mutation stream at a time. Built-in Chat and an external Aidus agent share application state.
- External MCP clients do not inherit FontLab Chat's per-tool confirmation UI. Enabling external MCP access grants real control; implement host-side authorization appropriate to the user's request.

See [architecture and context loading](docs/ARCHITECTURE.md), [verification](docs/VERIFICATION.md), and [security](SECURITY.md).

## Validate this checkout

No FontLab installation or model provider is needed for offline validation:

```sh
python3 tools/verify.py
python3 -m unittest discover -s tests -v
```

The verifier checks required files, file hashes, symlinks, local Markdown links and heading anchors, Python syntax, text/JSON API consistency, MCP argument contracts, and accidental personal paths or credential-like values. The tests exercise the tools and client using fake local transports; they do not modify a live font. Actual installed-build behavior requires the separate read-only doctor and explicit disposable-font testing.

## Build a clean archive

```sh
python3 tools/package.py --output dist/fontlab-aidus-kit-0.1.0.zip
```

The packager verifies the kit first and includes only manifest-listed files plus the manifest. It excludes reports, caches, virtual environments, and Git metadata. Existing archives are not replaced unless `--overwrite` is supplied.

## Maintain and release

[Maintenance](docs/MAINTAINING.md) explains refreshing snapshots from an authorized FontLab source checkout and updating the manifest. [Release checklist](docs/RELEASE.md) covers final review and publishing. [Provenance](docs/PROVENANCE.md), [source snapshot](SOURCE.json), and [license status](LICENSE.md) identify scope and limitations.

The [public release review](docs/RELEASE_REVIEW.md) records findings, fixes, checks, and remaining release decisions.

Installed-build results: [FontLab 9.0.9807 and Aidus environment test](docs/INSTALLED_TEST.md). The opted-in `tools/live_smoke.py` command tests a disposable font; it is separate from read-only examples.
