# Verification

## Offline checks

Run `python3 tools/verify.py` and `python3 -m unittest discover -s tests -v` from the kit root. These require Python 3.10+ and no network or running FontLab.

The checks cover tool-name and argument-schema consistency across MCP and Python catalogs, the current component/history contracts, selected property access modes, valid local VFJ schema references, readable examples, required release files, Markdown file/heading links, symlink rejection, artifact integrity, text/JSON reference consistency, and absence of common accidental personal paths or credential-like values (including decoded JSON strings). The privacy check is a technical guard, not a substitute for human release review.

The client tests use a local fake bridge and cover request sequencing, tool-error propagation, and timeout behavior. They do not claim to exercise a live FontLab release.

## Installed build checks

Run the read-only doctor against the matching bridge. Confirm that required tools and argument schemas match the intended workflow. The doctor's report contains local tool/font metadata; keep saved reports out of a public repository.

For write testing, use a disposable font copy and an explicit, reviewed request. Validate one operation first, inspect the result, exercise Undo/Redo if promised, and reopen any saved copy. Never use a production font to test destructive behavior or blindly replay a timeout.

The preparation work validated generated references, native VFJ/Chat regressions in the source workspace, and packaging there. This standalone kit must still be checked against the installed app and Aidus version used by a recipient.

No live FontLab or Aidus session is exercised by the offline release verifier. A separate opted-in live test is documented in [INSTALLED_TEST.md](INSTALLED_TEST.md). A passing offline review does not qualify a particular application build for public support.

The installed-session test passed eight deterministic checks on FontLab 9.0.9807 and Aidus’s installed MCP SDK. See the installed-test report for scope and the untested conversational/UI path.
