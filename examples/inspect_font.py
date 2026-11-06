#!/usr/bin/env python3
"""List fonts; optionally inspect up to ten glyph summaries in an explicit font."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"docs/mcp"))
from client import Client


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", required=True)
    parser.add_argument("--font-id", type=int)
    args = parser.parse_args()
    with Client(args.bridge) as client:
        names = {tool["name"] for tool in client.tools()}
        if "list_fonts" not in names: raise RuntimeError("Installed build has no list_fonts")
        result = {"fonts": client.call("list_fonts")}
        if args.font_id is not None:
            if "list_glyphs" not in names: raise RuntimeError("Installed build has no list_glyphs")
            result["glyphs"] = client.call("list_glyphs", font_id=args.font_id, detail="basic", limit=10)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
