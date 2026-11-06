# Public release review

Review date: 2026-11-06.

The current source-derived API snapshots match the available FontLab source references. No personal filesystem paths, email addresses, model credentials, authentication tokens, application binaries, or private font files were found in the release contents. Placeholder executable paths and the documented loopback endpoint are intentional.

## Findings and fixes

| Finding | Resolution |
|---|---|
| Public MCP guide told readers to edit/run source-only files absent from the kit | Replaced those instructions with the kit's maintenance and verification workflow; source-only commands remain explicitly scoped in the maintainer guide |
| Guide claimed that the public JSON included private source-file hashes, although those hashes had been removed | Corrected provenance to point to SOURCE.json and the shipped-file manifest |
| Compatibility notes included internal issue-tracker references | Replaced them with public capability/version guidance in both structured and text MCP references |
| Verifier checked file links but not heading anchors or links escaping the kit | Added heading/fragment checks, reference-style link support, and path containment checks |
| Directory and dangling symlinks could evade the old inventory | Added non-following traversal and rejection before hashing or reading their contents |
| Refreshing a manifest could hide missing release files or text/schema drift | Added an independent required-file list, text/JSON member checks, and MCP argument/description/effect comparisons |
| Reference refresh wrote into the kit before validating the incoming snapshot | Added candidate staging and content validation; invalid incoming references leave the kit unchanged |
| No supported clean-archive command was included | Added manifest-only ZIP packaging after verification, with an explicit overwrite option and reproducible entry metadata |

## Verification scope

- Compared the full and compact Python references, VFJ schema, and action catalog with the available source snapshots.
- Compared the bundled MCP tool names and input schemas with the current native registry.
- Checked every shipped text file for common personal-path and credential patterns, including decoded JSON values.
- Checked required files, local Markdown targets and heading anchors, and all local VFJ definition references.
- Exercised the offline reference helpers, fake bridge, preview guard, mutation-detection fixtures, staged sync, and clean ZIP packaging.
- Verified the final release manifest and archive contents.

There are no external Markdown links in the kit to probe. JSON Schema dialect identifiers and other literal URLs in reference data are not bundled file dependencies. Static scanning is not a guarantee against every possible secret format.

The final checks passed: 19 kit regression tests, seven source-reference tests, all 49 MCP input-schema comparisons, and the six API/action/schema snapshot comparisons. The release archive was checked against the manifest.

## Remaining release decisions

1. Licensing is resolved: the owner selected MIT for this kit on 2026-11-06. The license covers the kit, not the separately distributed FontLab or Aidus applications.
2. The repository destination is Fontlab/aidus-kit. A dedicated security/support contact remains unset.
3. Subsequent deterministic testing on FontLab 9.0.9807 and the installed Aidus environment passed; see [INSTALLED_TEST.md](INSTALLED_TEST.md). The Aidus dock and model-driven conversation still need qualification before broader end-to-end support claims.

The review fixes technical packaging and documentation issues. It does not publish the project, change a running FontLab application, or convert historical API fallback data into verified runtime capabilities.
