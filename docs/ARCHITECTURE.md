# Architecture and context loading

```text
Aidus or another MCP host -> stdio bridge -> running FontLab desktop
Built-in Chat / embedded Python fontpr -> the same native tool registry
```

This kit is reference material plus a small external client. It is neither the Aidus application nor a headless FontLab runtime.

Use three context levels:

1. Load `prompts/AIDUS.md` as the operating instructions appropriate to your host.
2. Retrieve selected lines from the compact Python/Chat references and the detailed Python agent guide.
3. Retrieve exact full MCP schemas, full Python members, or VFJ definitions when the task needs them.

Do not send every API catalog on every request. `tools/reference.py` provides bounded lookup without model/provider dependencies. `class` lookup includes the property's read/write information and the class's source provenance. `mcp` returns the recorded tool contract. `vfj` includes the topic's referenced definitions so JSON Schema references remain resolvable. `search` returns bounded name matches.

An MCP tool schema describes tool arguments; it is different from the VFJ glyph schema. Construction summaries are read-only projections; they are different from writable VFJ. Native Python editor wrappers and FontGate data objects also have distinct methods and ownership.

The application can serialize tool calls, but concurrent assistants can still make decisions from stale reads. Coordinate one mutation stream and re-read after changes. This kit does not add distributed transactions or automatic rollback.
