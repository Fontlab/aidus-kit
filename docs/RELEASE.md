# Release checklist

- Confirm the intended public repository name, owner, description, and version.
- Include the MIT license and copyright notice in every release. Keep application binaries and separately licensed dependencies outside the kit.
- Review the snapshot provenance and capability caveats. Do not claim a source-only feature is present in every released FontLab 9 build.
- Confirm all example configurations contain placeholders only and no credentials or personal paths.
- Run the offline verifier and tests, then the read-only doctor against the intended supported app/bridge pair.
- Test any advertised write workflows on disposable fonts and record the tested platform/build.
- Set the public security/support contact.
- Run `python3 tools/verify.py --refresh-manifest` after reviewed changes, then build the archive with `python3 tools/package.py`. Inspect its manifest and excluded-file policy; do not zip the whole working directory.
- Publish from this standalone kit only. Do not publish the full application source checkout or sibling directories by accident.

Publishing requires explicit authorization and does not change a running FontLab application. The selected repository is https://github.com/Fontlab/aidus-kit.

See [the current release review](RELEASE_REVIEW.md) for technical findings and remaining decisions.
