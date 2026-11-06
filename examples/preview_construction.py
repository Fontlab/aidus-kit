#!/usr/bin/env python3
"""Validate an explicit construction recipe using advertised native dry_run only."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"docs/mcp"))
from client import Client


def preview(client, font_id, glyph_name, layer_name, recipe):
    tools = {tool["name"]: tool for tool in client.tools()}
    tool = tools.get("build_glyph", {})
    dry_schema = tool.get("inputSchema", {}).get("properties", {}).get("dry_run", {})
    if dry_schema.get("type") != "boolean":
        raise RuntimeError("Installed build does not advertise build_glyph dry_run; refusing to call it")
    return client.call("build_glyph", font_id=font_id, glyph_name=glyph_name,
                       layer_name=layer_name, recipe=recipe, dry_run=True, replace=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", required=True)
    parser.add_argument("--font-id", required=True, type=int)
    parser.add_argument("--glyph", required=True)
    parser.add_argument("--layer", required=True)
    parser.add_argument("--recipe", required=True)
    args = parser.parse_args()
    try:
        with Client(args.bridge) as client:
            print(json.dumps(preview(client, args.font_id, args.glyph, args.layer, args.recipe), ensure_ascii=False, indent=2))
    except (OSError, RuntimeError, ValueError, EOFError) as exc:
        parser.exit(1, f"Preview failed: {exc}\nCheck the bridge, font ID, layer, source glyphs and recipe. No commit was requested.\n")


if __name__ == "__main__":
    main()
