# Contributing

Contributions to this kit are provided under its MIT license. Coordinate public hosting and releases with the maintainers. Do not submit proprietary fonts, secrets, personal paths, application binaries, or copied third-party code without established rights.

Keep reference snapshots reproducible. For source-derived API changes, update the generator/binding in the authorized source checkout, regenerate there, and refresh the kit as described in `docs/MAINTAINING.md`. Do not edit generated signatures to make an unverified script appear supported.

For helper changes, run the offline verifier and tests. Keep dependencies limited to Python's standard library unless a new dependency has a clear purpose and license review. Label live-app tests separately from fake-transport tests.
