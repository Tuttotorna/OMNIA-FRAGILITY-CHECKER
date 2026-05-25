"""Report writers for OMNIA Fragility Checker."""

from __future__ import annotations

import csv
import html
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Sequence

from .classifier import CaseClassification, summary_from_cases, to_jsonable


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def severity_class(severity: str) -> str:
    return severity.lower().replace("_", "-")


def write_reports(out_dir: Path, cases: Sequence[CaseClassification], input_path: str) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summary_from_cases(cases)

    report = {
        "tool": "OMNIA Fragility Checker",
        "version": "0.2.0",
        "mode": "Structural Fragility Bridge",
        "input": input_path,
        "summary": summary,
        "cases": to_jsonable(cases),
        "boundary": "measurement != inference != decision",
    }

    write_json(out_dir / "report.json", report)

    write_json(
        out_dir / "certificate.json",
        {
            "tool": report["tool"],
            "version": report["version"],
            "mode": report["mode"],
            "input": input_path,
            "summary": summary,
            "certificate": "structural_fragility_measurement_only",
            "decision": "external",
            "boundary": "measurement != inference != decision",
        },
    )

    with (out_dir / "report.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case_id",
                "severity",
                "reason",
                "base_variant_id",
                "variants",
                "pair_count",
            ],
        )
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {
                    "case_id": case.case_id,
                    "severity": case.severity,
                    "reason": case.reason,
                    "base_variant_id": case.base_variant_id,
                    "variants": case.variants,
                    "pair_count": len(case.pair_results),
                }
            )

    fragile = [asdict(c) for c in cases if c.severity in {"ANSWER_FRAGILE", "NUMERIC_FRAGILE", "CRITICAL_FRAGILE"}]
    critical = [asdict(c) for c in cases if c.severity == "CRITICAL_FRAGILE"]
    surface = [asdict(c) for c in cases if c.severity == "SURFACE_VARIANT"]

    write_jsonl(out_dir / "fragile_cases.jsonl", fragile)
    write_jsonl(out_dir / "critical_cases.jsonl", critical)
    write_jsonl(out_dir / "surface_variants.jsonl", surface)
    write_html(out_dir / "report.html", report)

    return report


def write_html(path: Path, report: Dict[str, Any]) -> None:
    summary = report["summary"]
    cases = report["cases"]

    rows = []
    for case in cases:
        pair_details = []
        for pair in case.get("pair_results", []):
            sev = pair.get("severity", "STABLE")
            pair_details.append(
                "<div class='pair'>"
                f"<b>{html.escape(pair.get('variant_id', 'variant'))}</b> "
                f"<span class='badge {severity_class(sev)}'>{html.escape(sev)}</span>"
                f"<br><span class='muted'>{html.escape(pair.get('reason', ''))}</span>"
                f"<br><code>{html.escape(pair.get('base_final', ''))}</code> -&gt; <code>{html.escape(pair.get('variant_final', ''))}</code>"
                "</div>"
            )

        rows.append(
            "<tr>"
            f"<td>{html.escape(case['case_id'])}</td>"
            f"<td><span class='badge {severity_class(case['severity'])}'>{html.escape(case['severity'])}</span></td>"
            f"<td>{html.escape(case['reason'])}</td>"
            f"<td>{html.escape(str(case['variants']))}</td>"
            f"<td>{''.join(pair_details)}</td>"
            "</tr>"
        )

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>OMNIA Fragility Checker Report</title>
<style>
:root {{
  --bg: #0b0d10;
  --panel: #13171d;
  --text: #e8edf2;
  --muted: #9aa7b2;
  --border: #27313b;
  --stable: #2e7d32;
  --surface: #6a5acd;
  --answer: #b7791f;
  --numeric: #c05621;
  --critical: #c53030;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
}}
main {{
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px 20px 56px;
}}
h1 {{ font-size: 32px; margin: 0 0 8px; }}
h2 {{ margin-top: 32px; }}
p {{ color: var(--muted); }}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin: 24px 0;
}}
.card {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px;
}}
.card .num {{
  font-size: 28px;
  font-weight: 750;
}}
.card .label {{
  color: var(--muted);
  font-size: 13px;
  margin-top: 4px;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
}}
th, td {{
  text-align: left;
  vertical-align: top;
  padding: 12px;
  border-bottom: 1px solid var(--border);
}}
th {{
  color: var(--muted);
  font-weight: 650;
  background: #10141a;
}}
tr:last-child td {{ border-bottom: none; }}
.badge {{
  display: inline-block;
  padding: 4px 8px;
  border-radius: 999px;
  color: white;
  font-size: 12px;
  font-weight: 750;
}}
.stable {{ background: var(--stable); }}
.surface-variant {{ background: var(--surface); }}
.answer-fragile {{ background: var(--answer); }}
.numeric-fragile {{ background: var(--numeric); }}
.critical-fragile {{ background: var(--critical); }}
.muted {{ color: var(--muted); }}
.pair {{
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 8px;
  margin-bottom: 8px;
}}
code {{
  background: #080a0d;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 2px 5px;
}}
.footer {{
  margin-top: 28px;
  color: var(--muted);
  font-size: 13px;
}}
</style>
</head>
<body>
<main>
<h1>OMNIA Fragility Checker</h1>
<p>Structural Fragility Bridge v0.2 - measurement only. Decision remains external.</p>

<div class="grid">
  <div class="card"><div class="num">{summary['total_cases']}</div><div class="label">total cases</div></div>
  <div class="card"><div class="num">{summary['stable']}</div><div class="label">stable</div></div>
  <div class="card"><div class="num">{summary['surface_variant']}</div><div class="label">surface variants</div></div>
  <div class="card"><div class="num">{summary['answer_fragile']}</div><div class="label">answer fragile</div></div>
  <div class="card"><div class="num">{summary['numeric_fragile']}</div><div class="label">numeric fragile</div></div>
  <div class="card"><div class="num">{summary['critical_fragile']}</div><div class="label">critical fragile</div></div>
</div>

<h2>Case inspection</h2>
<table>
<thead>
<tr>
<th>case</th>
<th>severity</th>
<th>reason</th>
<th>variants</th>
<th>pair details</th>
</tr>
</thead>
<tbody>
{''.join(rows)}
</tbody>
</table>

<div class="footer">
Boundary: measurement != inference != decision<br>
Surface validity is not structural stability.
</div>
</main>
</body>
</html>
"""
    path.write_text(page, encoding="utf-8")
