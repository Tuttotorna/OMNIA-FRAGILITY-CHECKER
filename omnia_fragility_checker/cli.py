"""Command line interface for OMNIA Fragility Checker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from .classifier import classify_records
from .reporter import write_reports


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            text = line.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL at {path}:{lineno}: {exc}") from exc
            if not isinstance(obj, dict):
                raise SystemExit(f"Invalid JSONL at {path}:{lineno}: each line must be an object")
            if "case_id" not in obj:
                raise SystemExit(f"Invalid JSONL at {path}:{lineno}: missing case_id")
            rows.append(obj)
    if not rows:
        raise SystemExit(f"No records found in {path}")
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omnia-fragility-checker",
        description="Measure structural fragility across equivalent output variants.",
    )
    parser.add_argument("--input", required=True, help="Input JSONL file with case_id grouped variants.")
    parser.add_argument("--out-dir", required=True, help="Output directory for report artifacts.")
    parser.add_argument("--fail-on-fragile", action="store_true", help="Exit 2 if fragile cases are detected.")
    parser.add_argument("--fail-on-critical", action="store_true", help="Exit 3 if critical cases are detected.")
    return parser


def print_summary(report):
    summary = report["summary"]
    print("OMNIA FRAGILITY CHECK")
    print("====================")
    print(f"input:                         {report['input']}")
    print(f"total_cases:                   {summary['total_cases']}")
    print(f"stable:                        {summary['stable']}")
    print(f"surface_variant:               {summary['surface_variant']}")
    print(f"answer_fragile:                {summary['answer_fragile']}")
    print(f"numeric_fragile:               {summary['numeric_fragile']}")
    print(f"critical_fragile:              {summary['critical_fragile']}")
    print(f"fragile_cases:                 {summary['fragile_cases']}")
    print(f"fragility_rate:                {summary['fragility_rate']:.6f}")
    print(f"critical_rate:                 {summary['critical_rate']:.6f}")
    print(f"max_severity:                  {summary['max_severity']}")
    print("")
    print("Boundary: measurement != inference != decision")


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    records = read_jsonl(Path(args.input))
    cases = classify_records(records)
    report = write_reports(Path(args.out_dir), cases, args.input)
    print_summary(report)

    for name in [
        "report.json",
        "report.csv",
        "report.html",
        "fragile_cases.jsonl",
        "critical_cases.jsonl",
        "surface_variants.jsonl",
        "certificate.json",
    ]:
        print(f"WROTE: {Path(args.out_dir) / name}")

    summary = report["summary"]

    if args.fail_on_critical and summary["critical_fragile"] > 0:
        return 3

    if args.fail_on_fragile and summary["fragile_cases"] > 0:
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
