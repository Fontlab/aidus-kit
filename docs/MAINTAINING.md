# Maintaining the kit

## Refresh reference snapshots

A maintainer with authorized access to the FontLab source tree should first regenerate its references and run its reference tests:

```sh
python3 scripts/build_python_api_spec.py --full-only
python3 scripts/build_python_api_spec.py --chat-only
python3 scripts/build_python_api_spec.py --check
python3 scripts/build_mcp_spec.py
python3 tests/test_python_api_spec.py
```

These commands run in the source checkout, not in this standalone kit. The Python generator also requires the matching historical introspection source directory. That private build dependency is not needed to read or validate this kit.

Then run, from the kit root:

```sh
python3 tools/sync_references.py --source /absolute/path/to/authorized-source-checkout
python3 tools/verify.py
python3 -m unittest discover -s tests -v
```

The sync command stages an explicit allowlist of references and the reference client, rewrites private source-tree links to portable provenance links, removes internal source-file checksum entries from the public MCP contract, removes internal issue references and source-only maintenance instructions, and records the source revision/dirty state. It validates the complete staged kit before replacing reference files and refreshing the manifest. A validation failure leaves the existing kit unchanged. It does not copy application source, install binaries, publish a repository, or run a model.

## Edit authored files

Edit the README, prompts, helper scripts, examples and setup documents directly. Preserve the intended runtime distinction: external helpers use system Python; embedded scripts run inside FontLab. Keep templates free of local paths and secrets.

After reviewed changes:

```sh
python3 tools/verify.py --refresh-manifest
python3 -m unittest discover -s tests -v
```

Refreshing a manifest records file contents; it does not certify that they are correct or approved for public distribution. Review failures and the release checklist before publishing. Keep source snapshot provenance accurate and record installed-build test results separately.

## Build the release artifact

Run `python3 tools/package.py --output dist/fontlab-aidus-kit-0.1.0.zip` after verification.
The command refuses symlinks and invalid references, includes only manifest entries,
and uses a fixed top-level `fontlab-aidus-kit` directory. Add `--overwrite` only when
intentionally replacing a reviewed archive. Do not zip the entire working directory:
local reports, environment files and caches do not belong in a public artifact.
