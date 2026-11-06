#!/usr/bin/env python3
"""Offline, bounded lookup of the kit's API references."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def lookup_class(name, member=None):
    classes = read("Resources/fontlab_python_api.json")["c"]
    if name not in classes:
        raise ValueError("Unknown class: " + name)
    record = classes[name]
    if member is None:
        return {"class": name, **record}
    matches = {kind: record[kind][member] for kind in ("m", "s", "pd", "x")
               if member in record.get(kind, {})}
    if member in record.get("p", []) and "pd" not in matches:
        matches["property"] = "Property; verify access in the installed build."
    if not matches:
        raise ValueError("Member not listed: " + name + "." + member)
    return {"class": name, "member": member, **matches}


def lookup_mcp(name):
    for tool in read("docs/mcp/fontlab-mcp.json")["tools"]:
        if tool["name"] == name:
            return tool
    raise ValueError("Unknown tool: " + name)


def lookup_vfj(topic):
    catalog = read("Resources/vfj_schema.json")
    if topic not in catalog["topics"]:
        raise ValueError("Unknown VFJ topic: " + topic)
    result = {"catalog_version": catalog["catalog_version"], "topic": topic, **catalog["topics"][topic]}
    if topic == "overview":
        result["topics"] = sorted(catalog["topics"])
        return result
    definitions = catalog["$defs"]
    selected = {}

    def visit(value):
        if isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, dict):
            ref = value.get("$ref")
            if ref:
                if not ref.startswith("#/$defs/"):
                    raise ValueError("Unsupported schema reference: " + ref)
                name = ref[8:]
                if name not in selected:
                    selected[name] = definitions[name]
                    visit(selected[name])
            for key, child in value.items():
                if key != "$ref":
                    visit(child)
    root_ref = "#/$defs/" + topic
    visit({"$ref": root_ref})
    result["schema"] = {"$schema": catalog["schema_dialect"], "$ref": root_ref, "$defs": selected}
    return result


def search(query, limit=10):
    if not query.strip() or not 1 <= limit <= 100:
        raise ValueError("Nonempty query and limit 1..100 required")
    needle = query.casefold()
    results = []
    for name, record in read("Resources/fontlab_python_api.json")["c"].items():
        if needle in name.casefold():
            results.append({"kind": "class", "name": name})
        # Some properties have names but no detailed pd record. They are still searchable.
        for member in record.get("p", []):
            label = name + "." + member
            if member not in record.get("pd", {}) and needle in label.casefold():
                results.append({"kind": "property", "name": label})
        for kind in ("m", "s", "pd", "x"):
            for member, value in record.get(kind, {}).items():
                label = name + "." + member
                if needle in label.casefold() or needle in json.dumps(value, ensure_ascii=False).casefold():
                    results.append({"kind": kind, "name": label})
    for tool in read("docs/mcp/fontlab-mcp.json")["tools"]:
        if needle in (tool["name"] + " " + tool["description"]).casefold():
            results.append({"kind": "mcp", "name": tool["name"]})
    return {"total": len(results), "results": results[:limit], "truncated": len(results) > limit}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    classes = commands.add_parser("class"); classes.add_argument("name"); classes.add_argument("--member")
    mcp = commands.add_parser("mcp"); mcp.add_argument("name")
    vfj = commands.add_parser("vfj"); vfj.add_argument("topic")
    searches = commands.add_parser("search"); searches.add_argument("query"); searches.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    try:
        if args.command == "class": result = lookup_class(args.name, args.member)
        elif args.command == "mcp": result = lookup_mcp(args.name)
        elif args.command == "vfj": result = lookup_vfj(args.topic)
        else: result = search(args.query, args.limit)
    except (ValueError, KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
