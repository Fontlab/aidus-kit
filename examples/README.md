# Examples

- `inspect_font.py`: external, read-only font discovery and optional paged glyph inspection. Uses an explicit `--font-id` for glyph reads.
- `preview_construction.py`: external, calls `build_glyph` only when its advertised schema includes boolean `dry_run`. Always passes `dry_run=True` and `replace=False`; there is no commit switch.
- `embedded_inspect.py`: runs inside FontLab's Python 3 environment and reads the current package/master metadata. Do not run it using a system interpreter expecting access to the open application.

Example construction preview:

```sh
python3 examples/preview_construction.py --bridge "/absolute/path/to/fontlab-mcp" --font-id 101 --glyph Aacute.preview --layer Regular --recipe '=A+acutecomb@top[_top]'
```

The example ID, names, layer, and anchors are placeholders. Discover valid values in your own font first. An existing target can fail validation because replacement is deliberately disabled. A failed preview is not permission to enable replacement or fall back to an older unvalidated write path.

No example automatically opens, saves, closes, or modifies a font. The detailed Python agent guide contains clearly labelled editing patterns for separately authorized use.
