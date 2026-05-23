import csv
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class VariantRecord:
    case_id: str
    variant_id: str
    output: str
    input_text: str = ""
    expected: str = ""


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    status: str
    severity: str
    variant_count: int
    unique_normalized_outputs: int
    unique_final_answers: int
    unique_numeric_answers: int
    expected_present: bool
    correctness_values: List[str]
    reason: str
    outputs: List[Dict[str, str]]


FRAGILE_STATUSES = {"CRITICAL_FRAGILE", "NUMERIC_FRAGILE", "ANSWER_FRAGILE"}


def normalize_text(text: str) -> str:
    text = str(text or "").strip().lower()
    text = text.replace("’", "'").replace("`", "'")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\.\,\-\+\=\:\%\/']", "", text)
    return text.strip()


def extract_last_number(text: str) -> Optional[str]:
    text = str(text or "")
    matches = re.findall(r"[-+]?\d+(?:[\.,]\d+)?", text)
    if not matches:
        return None

    value = matches[-1].replace(",", ".")
    try:
        f = float(value)
    except ValueError:
        return value

    if f.is_integer():
        return str(int(f))
    return str(f)


def extract_yes_no(text: str) -> Optional[str]:
    t = normalize_text(text)
    tokens = set(t.split())

    yes_words = {
        "yes", "true", "correct", "valid", "pass", "approved",
        "si", "sì", "vero", "corretto", "valido", "approvato",
    }
    no_words = {
        "no", "false", "incorrect", "invalid", "fail", "rejected",
        "falso", "sbagliato", "invalido", "respinto",
    }

    has_yes = bool(tokens & yes_words)
    has_no = bool(tokens & no_words)

    if has_yes and not has_no:
        return "YES"
    if has_no and not has_yes:
        return "NO"
    return None


def extract_final_answer(text: str) -> str:
    raw = str(text or "").strip()

    patterns = [
        r"(?:final answer|answer|therefore|so the answer is|risposta finale|risposta)\s*[:=]\s*(.+)$",
        r"####\s*(.+)$",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, raw, flags=re.IGNORECASE | re.MULTILINE)
        if matches:
            return normalize_text(matches[-1])

    yn = extract_yes_no(raw)
    if yn:
        return yn

    num = extract_last_number(raw)
    if num is not None:
        return num

    return normalize_text(raw)


def correctness_value(record: VariantRecord) -> str:
    if not record.expected:
        return "UNKNOWN"

    expected = extract_final_answer(record.expected)
    observed = extract_final_answer(record.output)

    if observed == expected:
        return "CORRECT"

    observed_num = extract_last_number(record.output)
    expected_num = extract_last_number(record.expected)

    if observed_num is not None and expected_num is not None:
        return "CORRECT" if observed_num == expected_num else "WRONG"

    return "WRONG"


def read_csv(path: Path) -> List[VariantRecord]:
    rows: List[VariantRecord] = []

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])

        required = {"case_id", "variant_id", "output"}
        missing = required - fields
        if missing:
            raise ValueError(f"Missing required CSV columns: {sorted(missing)}")

        for row in reader:
            rows.append(
                VariantRecord(
                    case_id=str(row.get("case_id", "")).strip(),
                    variant_id=str(row.get("variant_id", "")).strip(),
                    input_text=str(row.get("input", row.get("question", ""))).strip(),
                    output=str(row.get("output", "")).strip(),
                    expected=str(row.get("expected", row.get("expected_answer", ""))).strip(),
                )
            )

    return rows


def read_jsonl(path: Path) -> List[VariantRecord]:
    rows: List[VariantRecord] = []

    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue

            obj = json.loads(line)

            for key in ["case_id", "variant_id", "output"]:
                if key not in obj:
                    raise ValueError(f"Missing key {key!r} at line {line_no}")

            rows.append(
                VariantRecord(
                    case_id=str(obj.get("case_id", "")).strip(),
                    variant_id=str(obj.get("variant_id", "")).strip(),
                    input_text=str(obj.get("input", obj.get("question", ""))).strip(),
                    output=str(obj.get("output", "")).strip(),
                    expected=str(obj.get("expected", obj.get("expected_answer", ""))).strip(),
                )
            )

    return rows


def read_records(path: str) -> List[VariantRecord]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    suffix = p.suffix.lower()

    if suffix == ".csv":
        return read_csv(p)

    if suffix in {".jsonl", ".json"}:
        return read_jsonl(p)

    raise ValueError("Input must be .csv or .jsonl")


def group_by_case(records: List[VariantRecord]) -> Dict[str, List[VariantRecord]]:
    groups: Dict[str, List[VariantRecord]] = {}

    for record in records:
        if not record.case_id:
            continue
        groups.setdefault(record.case_id, []).append(record)

    return groups


def classify_case(case_id: str, records: List[VariantRecord]) -> CaseResult:
    normalized_outputs = [normalize_text(r.output) for r in records]
    final_answers = [extract_final_answer(r.output) for r in records]

    numeric_answers = []
    for r in records:
        n = extract_last_number(r.output)
        if n is not None:
            numeric_answers.append(n)

    correctness_values = [correctness_value(r) for r in records]

    unique_norm = set(normalized_outputs)
    unique_final = set(final_answers)
    unique_numeric = set(numeric_answers)
    unique_correctness = set(correctness_values)

    expected_present = any(bool(r.expected) for r in records)

    if len(records) < 2:
        status = "INSUFFICIENT_VARIANTS"
        severity = "LOW"
        reason = "Only one variant exists; fragility cannot be measured."
    elif expected_present and "CORRECT" in unique_correctness and "WRONG" in unique_correctness:
        status = "CRITICAL_FRAGILE"
        severity = "HIGH"
        reason = "Some equivalent variants are correct and others are wrong."
    elif len(unique_numeric) > 1:
        status = "NUMERIC_FRAGILE"
        severity = "HIGH"
        reason = "Equivalent variants produce different numeric answers."
    elif len(unique_final) > 1:
        status = "ANSWER_FRAGILE"
        severity = "MEDIUM"
        reason = "Equivalent variants produce different final answers."
    elif len(unique_norm) > 1:
        status = "SURFACE_VARIANT"
        severity = "LOW"
        reason = "Outputs differ in wording but extracted answers agree."
    else:
        status = "STABLE"
        severity = "NONE"
        reason = "All normalized outputs agree."

    return CaseResult(
        case_id=case_id,
        status=status,
        severity=severity,
        variant_count=len(records),
        unique_normalized_outputs=len(unique_norm),
        unique_final_answers=len(unique_final),
        unique_numeric_answers=len(unique_numeric),
        expected_present=expected_present,
        correctness_values=sorted(unique_correctness),
        reason=reason,
        outputs=[
            {
                "variant_id": r.variant_id,
                "input": r.input_text,
                "output": r.output,
                "final_answer": extract_final_answer(r.output),
                "numeric_answer": extract_last_number(r.output) or "",
                "correctness": correctness_value(r),
            }
            for r in records
        ],
    )


def analyze(path: str) -> Dict[str, Any]:
    records = read_records(path)
    groups = group_by_case(records)
    cases = [classify_case(case_id, rows) for case_id, rows in sorted(groups.items())]

    total = len(cases)
    fragile = [c for c in cases if c.status in FRAGILE_STATUSES]
    critical = [c for c in cases if c.status == "CRITICAL_FRAGILE"]
    stable = [c for c in cases if c.status == "STABLE"]

    summary = {
        "input_path": path,
        "total_records": len(records),
        "total_cases": total,
        "stable_cases": len(stable),
        "fragile_cases": len(fragile),
        "critical_fragile_cases": len(critical),
        "fragility_rate": (len(fragile) / total) if total else 0.0,
        "critical_rate": (len(critical) / total) if total else 0.0,
        "problem_solved": "Detects cases where equivalent input variants produce unstable outputs.",
    }

    return {
        "summary": summary,
        "cases": [asdict(c) for c in cases],
    }


def write_json_report(result: Dict[str, Any], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv_report(result: Dict[str, Any], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "case_id",
        "status",
        "severity",
        "variant_count",
        "unique_normalized_outputs",
        "unique_final_answers",
        "unique_numeric_answers",
        "expected_present",
        "correctness_values",
        "reason",
    ]

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for case in result["cases"]:
            row = {k: case.get(k, "") for k in fields}
            row["correctness_values"] = "|".join(case.get("correctness_values", []))
            writer.writerow(row)


def html_escape(x: str) -> str:
    return (
        str(x)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def write_html_report(result: Dict[str, Any], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for c in result["cases"]:
        if c["status"] in {"STABLE", "SURFACE_VARIANT"}:
            continue

        outputs = ""

        for o in c["outputs"]:
            outputs += f"""
            <details>
              <summary>{html_escape(o["variant_id"])} | final={html_escape(o["final_answer"])} | {html_escape(o["correctness"])}</summary>
              <p><b>Input</b></p>
              <pre>{html_escape(o["input"])}</pre>
              <p><b>Output</b></p>
              <pre>{html_escape(o["output"])}</pre>
            </details>
            """

        rows.append(f"""
        <tr>
          <td>{html_escape(c["case_id"])}</td>
          <td><b>{html_escape(c["status"])}</b></td>
          <td>{html_escape(c["severity"])}</td>
          <td>{html_escape(c["reason"])}</td>
          <td>{outputs}</td>
        </tr>
        """)

    summary = result["summary"]

    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>OMNIA Fragility Report</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          margin: 32px;
          line-height: 1.45;
        }}
        table {{
          border-collapse: collapse;
          width: 100%;
        }}
        th, td {{
          border: 1px solid #ddd;
          padding: 8px;
          vertical-align: top;
        }}
        th {{
          background: #f2f2f2;
        }}
        pre {{
          white-space: pre-wrap;
          background: #f7f7f7;
          padding: 10px;
          border: 1px solid #eee;
        }}
        .box {{
          background: #f8f8f8;
          padding: 16px;
          margin-bottom: 24px;
          border: 1px solid #eee;
        }}
      </style>
    </head>
    <body>
      <h1>OMNIA Fragility Report</h1>

      <div class="box">
        <p><b>Total cases:</b> {summary["total_cases"]}</p>
        <p><b>Fragile cases:</b> {summary["fragile_cases"]}</p>
        <p><b>Critical fragile cases:</b> {summary["critical_fragile_cases"]}</p>
        <p><b>Fragility rate:</b> {summary["fragility_rate"]:.4f}</p>
        <p><b>Problem solved:</b> {html_escape(summary["problem_solved"])}</p>
      </div>

      <h2>Fragile Cases</h2>

      <table>
        <tr>
          <th>Case</th>
          <th>Status</th>
          <th>Severity</th>
          <th>Reason</th>
          <th>Outputs</th>
        </tr>
        {''.join(rows)}
      </table>
    </body>
    </html>
    """

    out.write_text(html, encoding="utf-8")
