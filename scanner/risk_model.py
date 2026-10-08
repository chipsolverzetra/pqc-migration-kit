#!/usr/bin/env python3
"""PQC risk model: turn a scanner inventory into a prioritized migration backlog.

Implements Mosca's inequality (x + y > z means already late):
  x = data secrecy lifetime in years (from services.yaml)
  y = migration effort in years, mapped from upgrade difficulty
      (low = 1, medium = 3, high = 5)
  z = years until the planning horizon for a cryptographically relevant
      quantum computer (default: 2035 - 2026 = 9)

risk_score = min(100, (x + y) / z * 100 * algorithm_weight)

A score of 100 means the finding is already late by Mosca's rule.

Usage:
    python3 risk_model.py --inventory inventory.json \
        --services services.yaml --qday 2035 --output backlog.json

services.yaml format:
    services:
      ledger:
        data_secrecy_years: 15
        exposure: public        # public or internal
        upgrade_difficulty: high  # low, medium, high
        files:                  # path fragments attributing findings
          - "ledger_service.py"
    default:
      data_secrecy_years: 7
      exposure: internal
      upgrade_difficulty: medium

Standard library only.
"""

import argparse
import fnmatch
import json
import os
import sys

EFFORT_YEARS = {"low": 1, "medium": 3, "high": 5}

# Weight per pattern id. 1.0 = full quantum exposure.
ALGORITHM_WEIGHT = {
    "RSA_KEYGEN": 1.0,
    "RSA_USE": 1.0,
    "ECDSA_USE": 1.0,
    "DSA_DH_USE": 1.0,
    "JWT_ALG": 0.9,
    "TLS_VERSION": 0.7,
    "CIPHER_STRING": 0.7,
    "WEAK_HASH_MD5": 0.4,
    "WEAK_HASH_SHA1": 0.4,
    "CERT_RSA": 0.9,
    "HSM_REF": 0.6,
    "HARDCODED_ALG": 0.3,
    "OPENSSL_LEGACY": 0.5,
    "FNDSA_EXPERIMENTAL": 0.5,
    "PQC_READY": 0.0,
}

ACTION_BY_CATEGORY = {
    "asymmetric": "Replace with NIST standard: ML-KEM for key establishment (FIPS 203), ML-DSA for signatures (FIPS 204).",
    "signatures": "Migrate token and message signing to ML-DSA. Prioritize long-lived tokens.",
    "tls": "Move to TLS 1.3 with hybrid post-quantum key exchange (RFC 10024). Remove version pins.",
    "hash": "Hygiene fix: move to SHA-256 or SHA-384 during crypto-agility work.",
    "certificates": "Add to certificate inventory with expiry. Plan for hybrid or post-quantum certificates as CAs offer them.",
    "hsm": "Confirm PQC firmware roadmap with the vendor now. Vendor lag is a top reported blocker.",
    "config": "Refactor algorithm selection behind an abstraction. Crypto-agility is a funded workstream, not an afterthought.",
    "experimental": "DO NOT DEPLOY. FN-DSA is still in draft with known side-channel concerns. Track for future evaluation.",
    "pq_ready": "Already on the quantum-safe path. Verify it is exercised in production and record as migrated.",
}


def _scalar(text):
    """Convert a YAML scalar: strip quotes, convert ints."""
    text = text.strip().strip("'\"")
    try:
        return int(text)
    except ValueError:
        return text


def parse_simple_yaml(path):
    """Parse the small subset of YAML used by services.yaml.

    Supports nested maps with consistent indentation and simple lists.
    """
    with open(path, "r", encoding="utf-8") as handle:
        raw_lines = [line.rstrip("\n") for line in handle]

    lines = []
    for raw in raw_lines:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))

    pos = [0]

    def parse_block(min_indent):
        kind = None
        result_dict = {}
        result_list = []
        while pos[0] < len(lines):
            indent, text = lines[pos[0]]
            if indent < min_indent:
                break
            if text.startswith("- "):
                if kind is None:
                    kind = "list"
                if kind != "list":
                    raise ValueError("mixed list and map entries: %s" % text)
                result_list.append(_scalar(text[2:]))
                pos[0] += 1
            elif text.endswith(":"):
                if kind is None:
                    kind = "dict"
                key = text[:-1].strip()
                pos[0] += 1
                if pos[0] < len(lines) and lines[pos[0]][0] > indent:
                    result_dict[key] = parse_block(lines[pos[0]][0])
                else:
                    result_dict[key] = None
            else:
                if kind is None:
                    kind = "dict"
                if kind != "dict":
                    raise ValueError("mixed list and map entries: %s" % text)
                key, _, value = text.partition(":")
                result_dict[key.strip()] = _scalar(value)
                pos[0] += 1
        return result_list if kind == "list" else result_dict

    return parse_block(0)


def load_services(path):
    """Load services.yaml into (services dict, default dict)."""
    data = parse_simple_yaml(path) or {}
    services = data.get("services", {}) or {}
    default = data.get("default", {}) or {}
    return services, default


def attribute_service(finding, services, default):
    """Attribute a finding to a service by matching path fragments."""
    filepath = finding["file"]
    for name, spec in services.items():
        if not isinstance(spec, dict):
            continue
        for fragment in spec.get("files", []) or []:
            if fnmatch.fnmatch(filepath, "*" + fragment + "*") or fragment in filepath:
                return name, spec
    return "unassigned", default


def score_finding(finding, service_name, spec, z_years):
    """Compute the Mosca-based risk score for one finding."""
    secrecy = int(spec.get("data_secrecy_years", 7))
    difficulty = str(spec.get("upgrade_difficulty", "medium")).lower()
    effort = EFFORT_YEARS.get(difficulty, 3)
    exposure = str(spec.get("exposure", "internal")).lower()
    weight = ALGORITHM_WEIGHT.get(finding["pattern_id"], 0.5)

    mosca_value = (secrecy + effort) / z_years if z_years > 0 else 99.0
    raw = mosca_value * 100.0 * weight
    # Public exposure raises urgency; internal lowers it slightly.
    if exposure == "public":
        raw *= 1.1
    elif exposure == "internal":
        raw *= 0.95
    risk_score = round(min(100.0, raw), 1)
    already_late = (secrecy + effort) > z_years and weight > 0

    if weight == 0.0:
        phase = "monitoring"
    elif risk_score >= 60:
        phase = 2
    else:
        phase = 1

    return {
        "file": finding["file"],
        "line": finding["line"],
        "pattern_id": finding["pattern_id"],
        "name": finding["name"],
        "algorithm": finding["algorithm"],
        "category": finding["category"],
        "severity": finding["severity"],
        "service": service_name,
        "secrecy_years_x": secrecy,
        "effort_years_y": effort,
        "horizon_years_z": z_years,
        "mosca_late": already_late,
        "risk_score": risk_score,
        "recommended_phase": phase,
        "action": ACTION_BY_CATEGORY.get(finding["category"], "Review and remediate."),
        "excerpt": finding.get("excerpt", ""),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Prioritize a PQC scanner inventory into a migration backlog.")
    parser.add_argument("--inventory", required=True, help="inventory.json from pqc_scanner.py")
    parser.add_argument("--services", required=True, help="services.yaml with secrecy and difficulty data")
    parser.add_argument("--qday", type=int, default=2035,
                        help="planning horizon year for a cryptographically relevant quantum computer")
    parser.add_argument("--output", required=True, help="backlog JSON output path")
    args = parser.parse_args()

    with open(args.inventory, "r", encoding="utf-8") as handle:
        findings = json.load(handle)
    services, default = load_services(args.services)
    z_years = max(1, args.qday - 2026)

    backlog = []
    for finding in findings:
        service_name, spec = attribute_service(finding, services, default)
        if not isinstance(spec, dict):
            spec = default if isinstance(default, dict) else {}
        backlog.append(score_finding(finding, service_name, spec, z_years))

    backlog.sort(key=lambda item: item["risk_score"], reverse=True)

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(backlog, handle, indent=2)

    late = sum(1 for item in backlog if item["mosca_late"])
    avg = round(sum(item["risk_score"] for item in backlog) / len(backlog), 1) if backlog else 0.0
    print("PQC risk model results")
    print("  findings scored: %d" % len(backlog))
    print("  planning horizon: Q-Day %d (%d years)" % (args.qday, z_years))
    print("  already late by Mosca's rule (x + y > z): %d" % late)
    print("  average risk score: %s" % avg)
    print("  top 5:")
    for item in backlog[:5]:
        print("    [%s] %s:%d %s (%s)" % (
            item["risk_score"], item["file"], item["line"],
            item["name"], item["service"]))
    print("  backlog written to: %s" % args.output)


if __name__ == "__main__":
    main()
