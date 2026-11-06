# Provenance

`SOURCE.json` records the FontLab source revision and snapshot status. `manifest.json` records the files actually shipped and their SHA-256 hashes. The snapshot includes local source changes and is not a declaration that those changes shipped in a public release.

The Python catalogs combine current `pygate` registrations with a marked historical introspection baseline. Current registrations override method signatures, static/instance classification, and property access information. FontGate entries and unoverridden members retain historical provenance and require installed-runtime verification.

The MCP reference is generated from FontLab's native tool registry and reviewed usage notes. The VFJ catalog documents native serialization, including advanced and legacy cases. Native parsing is not a font-wide semantic validator.

The compact Chat references and full references are kept consistent by their source generator. Internal issue-tracker references and source-only maintenance commands are omitted from the public MCP guide; native tool contracts remain unchanged. The script client is a snapshot of the FontLab MCP reference client. Aidus configuration templates were authored for the MCP-backed configuration shape inspected during preparation; older releases can differ.

## Source references

Binding source identifiers inside the references, such as `pygate/pyfllayer.cpp`, are provenance labels. They do not imply that the application source is included here. Source links in the detailed agent guide have been redirected to this section for portable distribution. Maintainers with authorized source access can inspect the corresponding bindings and native regressions in that checkout.

Application source, model-provider implementations, proprietary font outlines, application binaries, and authentication tokens are excluded. The kit’s documentation and helper scripts are licensed under MIT; FontLab, Aidus, and separately distributed third-party software retain their own licenses. See `LICENSE.md` and `docs/RELEASE.md`.
