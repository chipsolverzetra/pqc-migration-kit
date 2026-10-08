#!/usr/bin/env python3
"""Generate a static HTML PQC migration report from scanner inventory and backlog.

Usage:
    python3 generate_report.py --inventory inventory.json \
        --backlog backlog.json --output report.html \
        [--title "Rea Pay: Post-Quantum Migration Report"]

Static HTML with inline CSS, no JavaScript dependencies.
Standard library only.
"""

import argparse
import html
import json
import os

PHASE_LABELS = {
    0: "Phase 0: Inventory",
    1: "Phase 1: Crypto-agility",
    2: "Phase 2: Hybrid deployment",
    3: "Phase 3: PQC cutover",
    4: "Phase 4: Decommission",
    "monitoring": "Monitoring",
}

SEVERITY_COLORS = {
    "critical": "#c0392b",
    "high": "#e67e22",
    "medium": "#d4a017",
    "low": "#2980b9",
    "info": "#27ae60",
}

CSS = """
body { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
       margin: 0; padding: 0; color: #1f2937; background: #f8fafc; }
.wrap { max-width: 1080px; margin: 0 auto; padding: 32px 24px 64px; }
header { background: #0f2a44; color: #fff; padding: 36px 24px; }
header .wrap { padding-top: 0; padding-bottom: 0; }
header h1 { margin: 0 0 8px; font-size: 28px; }
header p { margin: 4px 0; color: #cbd5e1; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
         gap: 16px; margin: 28px 0; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 18px 20px; }
.card .num { font-size: 32px; font-weight: 700; margin: 0; }
.card .lbl { font-size: 13px; color: #64748b; margin: 6px 0 0; }
h2 { font-size: 20px; margin: 40px 0 12px; border-bottom: 2px solid #0f2a44;
     padding-bottom: 6px; }
table { width: 100%; border-collapse: collapse; background: #fff;
        border: 1px solid #e2e8f0; font-size: 14px; }
th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #eef2f7; }
th { background: #0f2a44; color: #fff; font-weight: 600; }
tr:nth-child(even) td { background: #f8fafc; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 999px;
         color: #fff; font-size: 12px; font-weight: 600; }
.bar-row { display: flex; align-items: center; gap: 12px; margin: 10px 0; }
.bar-label { width: 260px; font-size: 14px; }
.bar-track { flex: 1; background: #e2e8f0; border-radius: 6px; height: 22px; }
.bar-fill { height: 22px; border-radius: 6px; background: #0f2a44; }
.bar-count { width: 48px; text-align: right; font-size: 14px; font-weight: 600; }
.rec { background: #fff; border-left: 4px solid #0f2a44; padding: 12px 16px;
       margin: 10px 0; border-radius: 0 8px 8px 0; }
.rec strong { display: block; margin-bottom: 4px; }
footer { margin-top: 48px; color: #64748b; font-size: 12px; }
code { background: #eef2f7; padding: 1px 6px; border-radius: 4px; font-size: 13px; }
"""


def esc(value):
    return html.escape(str(value))


def build_html(inventory, backlog, title):
    total = len(backlog)
    avg = round(sum(b["risk_score"] for b in backlog) / total, 1) if total else 0.0
    high = sum(1 for b in backlog if b["risk_score"] >= 60)
    late = sum(1 for b in backlog if b["mosca_late"])
    high_pct = round(high / total * 100, 1) if total else 0.0

    phase_counts = {}
    for item in backlog:
        phase = item["recommended_phase"]
        phase_counts[phase] = phase_counts.get(phase, 0) + 1

    parts = []
    parts.append("<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">")
    parts.append("<title>%s</title><style>%s</style></head><body>" % (esc(title), CSS))
    parts.append("<header><div class=\"wrap\">")
    parts.append("<h1>%s</h1>" % esc(title))
    parts.append("<p>Findings: %d &nbsp;|&nbsp; Services covered: %d &nbsp;|&nbsp; "
                 "Planning horizon: Q-Day 2035</p>" % (
                     len(inventory),
                     len({b["service"] for b in backlog})))
    parts.append("</div></header><div class=\"wrap\">")

    parts.append("<div class=\"cards\">")
    parts.append("<div class=\"card\"><p class=\"num\">%d</p>"
                 "<p class=\"lbl\">total findings scored</p></div>" % total)
    parts.append("<div class=\"card\"><p class=\"num\">%s</p>"
                 "<p class=\"lbl\">average risk score</p></div>" % avg)
    parts.append("<div class=\"card\"><p class=\"num\">%s%%</p>"
                 "<p class=\"lbl\">high risk findings (score 60+)</p></div>" % high_pct)
    parts.append("<div class=\"card\"><p class=\"num\">%d</p>"
                 "<p class=\"lbl\">already late by Mosca's rule (x + y &gt; z)</p></div>" % late)
    parts.append("</div>")

    parts.append("<h2>Recommended phase distribution</h2>")
    max_count = max(phase_counts.values()) if phase_counts else 1
    for phase in (1, 2, "monitoring"):
        count = phase_counts.get(phase, 0)
        width = round(count / max_count * 100) if max_count else 0
        label = PHASE_LABELS.get(phase, str(phase))
        parts.append("<div class=\"bar-row\"><div class=\"bar-label\">%s</div>"
                     "<div class=\"bar-track\"><div class=\"bar-fill\" style=\"width:%d%%\">"
                     "</div></div><div class=\"bar-count\">%d</div></div>"
                     % (esc(label), width, count))

    parts.append("<h2>Top 5 recommendations</h2>")
    for item in backlog[:5]:
        parts.append("<div class=\"rec\"><strong>%s "
                     "(risk %s, %s)</strong>%s<br><code>%s:%s</code></div>" % (
                         esc(item["name"]), esc(item["risk_score"]),
                         esc(item["service"]), esc(item["action"]),
                         esc(item["file"]), esc(item["line"])))

    parts.append("<h2>Prioritized backlog</h2>")
    parts.append("<table><tr><th>Risk</th><th>Finding</th><th>Service</th>"
                 "<th>File</th><th>Phase</th><th>Mosca</th></tr>")
    for item in backlog:
        color = SEVERITY_COLORS.get(item["severity"], "#64748b")
        phase = item["recommended_phase"]
        phase_label = PHASE_LABELS.get(phase, str(phase))
        mosca = "LATE" if item["mosca_late"] else "ok"
        parts.append("<tr><td><span class=\"badge\" style=\"background:%s\">%s</span></td>"
                     "<td>%s<br><small>%s</small></td><td>%s</td>"
                     "<td><code>%s:%s</code></td><td>%s</td><td>%s</td></tr>" % (
                         color, esc(item["risk_score"]), esc(item["name"]),
                         esc(item["algorithm"]), esc(item["service"]),
                         esc(item["file"]), esc(item["line"]),
                         esc(phase_label), mosca))
    parts.append("</table>")

    parts.append("<footer><p>Generated by pqc-migration-kit. Risk scores implement "
                 "Mosca's inequality: x (secrecy years) + y (migration effort) &gt; z "
                 "(years to Q-Day) means already late. Scores are planning aids, "
                 "not security guarantees.</p></footer>")
    parts.append("</div></body></html>")
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a static HTML PQC migration report.")
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--backlog", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="Rea Pay: Post-Quantum Migration Report")
    args = parser.parse_args()

    with open(args.inventory, "r", encoding="utf-8") as handle:
        inventory = json.load(handle)
    with open(args.backlog, "r", encoding="utf-8") as handle:
        backlog = json.load(handle)

    html_doc = build_html(inventory, backlog, args.title)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(html_doc)
    print("report written to %s (%d bytes, %d findings)" % (
        args.output, os.path.getsize(args.output), len(backlog)))


if __name__ == "__main__":
    main()
