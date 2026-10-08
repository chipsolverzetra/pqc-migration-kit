#!/usr/bin/env python3
"""PQC migration scanner: find quantum-vulnerable cryptography in a codebase.

Walks a target directory, applies the detection rules from patterns.py to
each file, and emits a JSON inventory of findings (a starter CBOM, or
cryptographic bill of materials).

Usage:
    python3 pqc_scanner.py --target <directory> --output inventory.json

Standard library only. Binary and unreadable files are skipped gracefully.
"""

import argparse
import json
import os
import re
import sys

from patterns import PATTERNS

# Extensions scanned with their matching rule file types.
TEXT_EXTENSIONS = {
    ".py", ".yaml", ".yml", ".json", ".toml", ".cfg", ".ini",
    ".sh", ".tf", ".txt", ".pem", ".crt", ".key", ".pub",
}
NAME_MARKERS = ("Dockerfile", ".env")


def file_matches_rule(filename, rule):
    """Check whether a rule applies to a file by extension or name marker."""
    base = os.path.basename(filename)
    for marker in NAME_MARKERS:
        if marker in rule["file_types"] and marker in base:
            return True
    _, ext = os.path.splitext(base)
    return ext in rule["file_types"]


def is_probably_binary(path):
    """Heuristic: skip files containing null bytes in the first chunk."""
    try:
        with open(path, "rb") as handle:
            return b"\x00" in handle.read(8192)
    except OSError:
        return True


def scan_file(path, compiled):
    """Scan one file, return a list of finding dicts."""
    findings = []
    if is_probably_binary(path):
        return findings
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()
    except OSError:
        return findings
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#!"):
            continue
        for pattern_id, rule, regex_list in compiled:
            if not file_matches_rule(path, rule):
                continue
            for regex in regex_list:
                if regex.search(line):
                    findings.append({
                        "file": path,
                        "line": lineno,
                        "pattern_id": pattern_id,
                        "name": rule["name"],
                        "algorithm": rule["algorithm"],
                        "category": rule["category"],
                        "severity": rule["severity"],
                        "excerpt": stripped[:160],
                    })
                    break
    return findings


def scan_tree(target, compiled):
    """Walk the target directory and scan every candidate file."""
    findings = []
    files_scanned = 0
    for root, _dirs, files in os.walk(target):
        # Skip common noise directories.
        _dirs[:] = [d for d in _dirs if d not in {".git", "__pycache__", ".venv", "node_modules"}]
        for name in sorted(files):
            path = os.path.join(root, name)
            base = os.path.basename(path)
            _, ext = os.path.splitext(base)
            if ext not in TEXT_EXTENSIONS and not any(m in base for m in NAME_MARKERS):
                continue
            files_scanned += 1
            findings.extend(scan_file(path, compiled))
    return findings, files_scanned


def print_summary(findings, files_scanned):
    """Print a human readable summary to stdout."""
    by_category = {}
    by_severity = {}
    for finding in findings:
        by_category[finding["category"]] = by_category.get(finding["category"], 0) + 1
        by_severity[finding["severity"]] = by_severity.get(finding["severity"], 0) + 1
    print("PQC scanner results")
    print("  files scanned: %d" % files_scanned)
    print("  total findings: %d" % len(findings))
    print("  by severity:")
    for severity in ("critical", "high", "medium", "low", "info"):
        if severity in by_severity:
            print("    %-8s %d" % (severity, by_severity[severity]))
    print("  by category:")
    for category in sorted(by_category):
        print("    %-14s %d" % (category, by_category[category]))
    if findings:
        print("  top findings:")
        for finding in findings[:10]:
            print("    %s:%d [%s] %s" % (
                finding["file"], finding["line"],
                finding["severity"], finding["name"]))


def main():
    parser = argparse.ArgumentParser(
        description="Scan a codebase for quantum-vulnerable cryptography.")
    parser.add_argument("--target", required=True, help="directory to scan")
    parser.add_argument("--output", required=True, help="JSON inventory output path")
    args = parser.parse_args()

    if not os.path.isdir(args.target):
        print("error: target is not a directory: %s" % args.target, file=sys.stderr)
        sys.exit(1)

    compiled = [
        (rule["id"], rule, [re.compile(rx) for rx in rule["regexes"]])
        for rule in PATTERNS
    ]
    findings, files_scanned = scan_tree(args.target, compiled)

    # Make paths relative to the target for a portable inventory.
    for finding in findings:
        finding["file"] = os.path.relpath(finding["file"], args.target)

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(findings, handle, indent=2)

    print_summary(findings, files_scanned)
    print("  inventory written to: %s" % args.output)


if __name__ == "__main__":
    main()
