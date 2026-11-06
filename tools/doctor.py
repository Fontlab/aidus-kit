#!/usr/bin/env python3
"""Read-only FontLab connection and MCP capability comparison. Never retries."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs/mcp"))
from client import Client


def compare_tools(installed, bundled):
    actual = {tool["name"]: tool for tool in installed}
    expected = {tool["name"]: tool for tool in bundled}
    return {"missing_from_installed": sorted(expected.keys() - actual.keys()),
            "additional_installed": sorted(actual.keys() - expected.keys()),
            "schema_differences": sorted(name for name in expected.keys() & actual.keys()
                                         if expected[name]["inputSchema"] != actual[name]["inputSchema"])}


def diagnose(bridge, timeout=75):
    bundled = json.loads((ROOT/"docs/mcp/fontlab-mcp.json").read_text())["tools"]
    with Client(bridge, timeout=timeout) as client:
        installed = client.tools()
        names = {tool["name"] for tool in installed}
        fonts = client.call("list_fonts") if "list_fonts" in names else None
        return {"connected": True, "mutations_performed": False,
                "installed_tool_count": len(installed), "installed_tools": sorted(names),
                "comparison": compare_tools(installed, bundled), "open_fonts": fonts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=75)
    args = parser.parse_args()
    try:
        result = diagnose(args.bridge, args.timeout)
    except Exception as exc:
        print(json.dumps({"connected": False, "error_type": type(exc).__name__, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
