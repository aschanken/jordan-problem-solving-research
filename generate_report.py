#!/usr/bin/env python3
"""Generate consolidated research report from per-item JSON files.

Reads outline.yaml, fields.yaml, and all result JSONs.
Produces report.md with TOC + detailed findings by field category.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any

ROOT = Path("/home/ais/workspace/iain/jordan-problem-solving-research")
RESULTS_DIR = ROOT / "results"
FIELDS_PATH = ROOT / "fields.yaml"
OUTLINE_PATH = ROOT / "outline.yaml"
REPORT_PATH = ROOT / "report.md"

# ── Field definitions ──
def load_fields_yaml(path: Path) -> dict[str, dict]:
    """Parse fields.yaml into {field_name: {category, description, detail_level}}.

    Supports both flat 'fields:' structure and nested 'field_categories:' structure
    (the latter is produced by the validate_json.py script).
    """
    import yaml
    with open(path) as f:
        data = yaml.safe_load(f)

    fields = {}

    # Try nested structure first (field_categories -> categories -> fields)
    for cat_block in data.get("field_categories", []):
        category = cat_block.get("category", "Uncategorized")
        for fd in cat_block.get("fields", []):
            fields[fd["name"]] = {
                "category": category,
                "description": fd.get("description", ""),
                "detail_level": fd.get("detail_level", "moderate"),
            }

    # Also try flat structure if nested returned nothing
    if not fields:
        for fd in data.get("fields", []):
            fields[fd["name"]] = {
                "category": fd.get("category", "Uncategorized"),
                "description": fd.get("description", ""),
                "detail_level": fd.get("detail_level", "moderate"),
            }

    return fields

def slugify(name: str) -> str:
    """Generate markdown anchor slug from item name."""
    s = re.sub(r"[^\w\s-]", "", name.lower())
    s = re.sub(r"\s+", "-", s)
    return s

# ── Value formatting ──
def format_value(val: Any, max_inline: int = 100) -> str:
    """Format a JSON value for markdown display."""
    if val is None:
        return ""
    if isinstance(val, bool):
        return "Yes" if val else "No"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        s = val.strip()
        if len(s) > max_inline:
            return "\n\n> " + s.replace("\n", "\n> ") + "\n"
        return s
    if isinstance(val, list):
        if not val:
            return "(none)"
        # list of dicts: compact table
        if all(isinstance(v, dict) for v in val):
            lines = []
            for d in val:
                parts = " | ".join(f"{k}: {str(v)[:120]}" for k, v in d.items())
                lines.append(f"- {parts}")
            return "\n".join(lines)
        # short list: inline
        joined = ", ".join(str(v) for v in val)
        if len(joined) <= max_inline:
            return joined
        return "\n".join(f"- {v}" for v in val)
    if isinstance(val, dict):
        lines = []
        for k, v in val.items():
            lines.append(f"- **{k}**: {str(v)[:200]}")
        return "\n".join(lines)
    return str(val)[:500]

def is_uncertain(data: dict, field_name: str) -> bool:
    """Check if a field value is uncertain."""
    val = data.get(field_name)
    if val is None or val == "":
        return True
    if isinstance(val, str) and "[uncertain]" in val:
        return True
    uncertain_list = data.get("uncertain", [])
    if field_name in uncertain_list:
        return True
    return False

# ── Main ──
def main():
    # Load fields
    field_defs = load_fields_yaml(FIELDS_PATH)
    # Group by category
    categories: dict[str, list[str]] = defaultdict(list)
    for fname, finfo in field_defs.items():
        categories[finfo["category"]].append(fname)

    # Load all results, ordered by item id extracted from JSON
    results = []
    for fpath in sorted(RESULTS_DIR.glob("*.json")):
        with open(fpath) as f:
            data = json.load(f)
        results.append(data)

    # Sort by id field if present, else by name
    def sort_key(d):
        # Try to extract numeric id from name or id field
        n = d.get("name", "")
        return n.lower()

    results.sort(key=sort_key)

    # Determine which fields to show in TOC
    toc_fields = ["analogous_jordan_node"]

    # ── Build report ──
    lines = []
    topic = "Systemized Problem Solving & Task Decomposition — Military-to-Software Analogues for JORDAN Pipeline Optimization"
    lines.append(f"# Research Report: {topic}")
    lines.append("")
    lines.append(f"**Date:** 2026-05-22 | **Items researched:** {len(results)} | **Fields per item:** {len(field_defs)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Table of Contents ──
    lines.append("## Table of Contents")
    lines.append("")
    # Build TOC header
    toc_header = "| # | Item |"
    toc_sep = "|---|------|"
    for tf in toc_fields:
        toc_header += f" Maps to JORDAN |"
        toc_sep += "---|"
    lines.append(toc_header)
    lines.append(toc_sep)

    for i, item in enumerate(results, 1):
        name = item.get("name", f"Item {i}")
        slug = slugify(name)
        row = f"| {i} | [{name}](#{slug}) |"
        for tf in toc_fields:
            val = item.get(tf, "")
            if val and not is_uncertain(item, tf):
                val_str = str(val)[:60].replace("\n", " ").replace("|", "/")
            else:
                val_str = "—"
            row += f" {val_str} |"
        lines.append(row)

    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Detailed Content by Category ──
    # We'll organize per item, grouped by category, showing all fields

    cat_order = [
        "Basic Identity",
        "Core Philosophy",
        "Phase Structure",
        "Decomposition",
        "Risk & Uncertainty",
        "Human Role",
        "Scalability & Cost",
        "Adaptation & Recovery",
        "Communication",
        "Learning & Memory",
        "Performance",
        "SW/LLM Applicability",
        "Empirical Record",
    ]

    # Build a per-item map first, then we can cross-reference
    # For this report we organize by ITEM (each item gets a section),
    # with fields grouped by category inside each item section.
    # This is more readable than listing all 61 items per category.

    lines.append("## Detailed Findings by Item")
    lines.append("")

    for i, item in enumerate(results, 1):
        name = item.get("name", f"Item {i}")
        slug = slugify(name)
        lines.append(f"### {i}. {name} {{#{slug}}}")
        lines.append("")

        # Group item's fields by category
        item_cats: dict[str, list[str]] = defaultdict(list)
        for fname in field_defs:
            cat = field_defs[fname]["category"]
            item_cats[cat].append(fname)

        for cat in cat_order:
            if cat not in item_cats:
                continue
            cat_fields = item_cats[cat]
            # Check if any field in this category has content
            has_content = False
            for fname in cat_fields:
                if not is_uncertain(item, fname):
                    has_content = True
                    break
            if not has_content:
                continue

            lines.append(f"**{cat}**")
            lines.append("")
            for fname in cat_fields:
                if is_uncertain(item, fname):
                    continue
                val = item.get(fname)
                if not val and val != 0 and val is not False:
                    continue
                finfo = field_defs[fname]
                formatted = format_value(val)
                label = fname.replace("_", " ").title()
                if finfo["detail_level"] == "brief":
                    lines.append(f"- **{label}**: {formatted}")
                elif finfo["detail_level"] == "moderate":
                    lines.append(f"- **{label}**: {formatted}")
                else:  # detailed
                    lines.append(f"- **{label}**:")
                    lines.append(f"  {formatted}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # ── Footer ──
    lines.append("## Report Metadata")
    lines.append("")
    lines.append(f"- Items: {len(results)}")
    lines.append(f"- Fields defined: {len(field_defs)}")
    lines.append(f"- Field categories: {len(cat_order)}")
    lines.append(f"- Generated: 2026-05-22")
    lines.append("")

    report = "\n".join(lines)
    REPORT_PATH.write_text(report)
    print(f"Report written to {REPORT_PATH}")
    print(f"  Items: {len(results)}")
    print(f"  Size: {len(report):,} chars")

if __name__ == "__main__":
    main()
