import argparse
import sys
from pathlib import Path

from .core import analyze, write_csv_report, write_html_report, write_json_report


def main():
    parser = argparse.ArgumentParser(
        prog="omnia-fragility",
        description="Detect unstable AI outputs across equivalent prompt variants.",
    )

    parser.add_argument("input", help="Input CSV or JSONL file.")
    parser.add_argument("--out-dir", default="omnia_fragility_report", help="Output directory.")
    parser.add_argument("--fail-on-fragile", action="store_true", help="Exit with code 2 if fragile cases are found.")
    parser.add_argument("--fail-on-critical", action="store_true", help="Exit with code 3 if critical fragile cases are found.")

    args = parser.parse_args()

    result = analyze(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_json_report(result, str(out_dir / "report.json"))
    write_csv_report(result, str(out_dir / "report.csv"))
    write_html_report(result, str(out_dir / "report.html"))

    s = result["summary"]

    print("")
    print("OMNIA FRAGILITY CHECK")
    print("====================")
    print(f"input:                   {args.input}")
    print(f"total_records:           {s['total_records']}")
    print(f"total_cases:             {s['total_cases']}")
    print(f"stable_cases:            {s['stable_cases']}")
    print(f"fragile_cases:           {s['fragile_cases']}")
    print(f"critical_fragile_cases:  {s['critical_fragile_cases']}")
    print(f"fragility_rate:          {s['fragility_rate']:.4f}")
    print(f"critical_rate:           {s['critical_rate']:.4f}")
    print("")
    print(f"WROTE: {out_dir / 'report.json'}")
    print(f"WROTE: {out_dir / 'report.csv'}")
    print(f"WROTE: {out_dir / 'report.html'}")
    print("")

    if args.fail_on_critical and s["critical_fragile_cases"] > 0:
        sys.exit(3)

    if args.fail_on_fragile and s["fragile_cases"] > 0:
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
