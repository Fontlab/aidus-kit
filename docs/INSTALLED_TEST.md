# Installed compatibility test

Test date: 2026-11-06. Platform: macOS arm64.

The user-selected `build/qt_release/FontLab 9.app` reported version **9.0.9807**, bundle build **9807**. The running executable path was checked against that selected build. Its `Contents/MacOS` directory did not contain `fontlab-mcp`; testing used the separately built matching bridge. A bridge argument must point to an actual executable, not an assumed bundle location.

The installed Aidus Core environment used Python **3.13.7**, AgentPool **2.8.8**, and MCP SDK **1.26.0**. Its actual `boot.load_manifest` accepted the kit's manifest after replacing the bridge, model, and prompt placeholders with local configuration values. No credentials or private configuration were copied into this kit.

## Results

All **49 installed MCP input schemas** matched the bundled reference, with no missing or additional tools.

The reusable `tools/live_smoke.py` test passed these eight checks:

1. Writable VFJ schema discovery.
2. Dry-run preservation of the actual initial glyph inventory.
3. Embedded Python inspection using `fontlab`, `contour.nodes()`, and `fontpr.available()`.
4. Creation, width editing, and readback of a synthetic rectangle glyph.
5. Native construction recipe preview.
6. VFJ save, close, reopen, and verification of the edited width.
7. Reading the reopened glyph through the MCP SDK installed in Aidus's environment.
8. Cleanup and restoration of the original font inventory and active-font state.

Only uniquely named disposable test fonts were edited. Temporary saved font files were removed. Existing fonts were not edited. The test made **zero model-provider calls**.

## Compatibility corrections

The initial test harness assumed a new font had zero glyphs. This build supplies default glyphs, so the reusable test compares the actual before/after inventory instead.

The initial harness also assumed `open_font` returned a `font` summary. Its documented result is status/path/errors. The test now finds the reopened font by its unique disposable family name and enrolls it for cleanup. A disposable font left by the initial harness error was identified and closed; the final test confirmed inventory restoration.

These were test-harness assumptions, not failures of the advertised native API. No native tool-signature changes were needed. The kit now includes an explicitly opted-in live-test command and documents the separate development bridge layout.

## Reproduce

Use the Python executable from the intended Aidus Core environment when testing its SDK:

```sh
python3 tools/live_smoke.py --bridge /absolute/path/to/fontlab-mcp --allow-disposable-edits --aidus-sdk
```

Omit `--aidus-sdk` for a standard-library-only external-client test. FontLab must be running with external MCP access enabled. The command refuses to run mutations without `--allow-disposable-edits`. It uses a random family name and closes only its own fonts.

Run without simultaneous editing from another assistant or the user. A timeout can leave an unknown operation outcome; inspect application state before retrying.

## Limits of this qualification

The Aidus configuration loader and its installed MCP transport stack were exercised. The Aidus dock UI and an LLM-driven conversational round trip were **not** tested: the computer-use service was unavailable, and no model provider was invoked. Undo/Redo and platform builds other than this macOS build were not tested in this installed-session run. Earlier isolated source regression results are separate evidence.

This qualifies the listed deterministic workflows on the identified build; it is not blanket qualification of every tool or every Aidus release. The kit is licensed under MIT; publication remains a separate action.
