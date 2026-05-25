import json
import subprocess
import sys

from omnia_fragility_checker.classifier import classify_case, classify_pair


def row(case_id, variant_id, output, final_answer=None, **extra):
    data = {
        "case_id": case_id,
        "variant_id": variant_id,
        "model_output": output,
        "final_answer": final_answer if final_answer is not None else output,
    }
    data.update(extra)
    return data


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for item in rows:
            f.write(json.dumps(item) + chr(10))


def test_classify_stable():
    base = row("c", "base", "The drift_score is 0.42.", "0.42")
    var = row("c", "rephrase", "The drift_score is 0.42.", "0.42")
    assert classify_pair(base, var).severity == "STABLE"


def test_classify_surface_variant():
    base = row("c", "base", "Final answer: STABLE", "STABLE")
    var = row("c", "markdown", "**Final answer:** STABLE", "STABLE")
    assert classify_pair(base, var).severity == "SURFACE_VARIANT"


def test_classify_answer_fragile():
    base = row("c", "base", "Mode: observer perturbation", "observer perturbation")
    var = row("c", "rephrase", "Mode: representation drift", "representation drift")
    assert classify_pair(base, var).severity == "ANSWER_FRAGILE"


def test_classify_numeric_fragile():
    base = row("c", "base", "The drift_score is 0.42.", "0.42")
    var = row("c", "rephrase", "The drift_score is 0.57.", "0.57")
    assert classify_pair(base, var).severity == "NUMERIC_FRAGILE"


def test_classify_critical_fragile_from_gate():
    base = row("c", "base", "Gate: STOP", "STOP", observed_gate="STOP")
    var = row("c", "rephrase", "Gate: CONTINUE", "CONTINUE", observed_gate="CONTINUE")
    result = classify_pair(base, var)
    assert result.severity == "CRITICAL_FRAGILE"
    assert result.critical_flip == "stop -> continue"


def test_case_uses_worst_severity():
    rows = [
        row("c", "base", "Gate: STOP", "STOP", observed_gate="STOP"),
        row("c", "surface", "**Gate:** STOP", "STOP", observed_gate="STOP"),
        row("c", "bad", "Gate: CONTINUE", "CONTINUE", observed_gate="CONTINUE"),
    ]
    result = classify_case(rows)
    assert result.severity == "CRITICAL_FRAGILE"


def test_cli_writes_showroom_artifacts(tmp_path):
    input_path = tmp_path / "cases.jsonl"
    rows = [
        row("stable", "base", "Answer: 1", "1"),
        row("stable", "rephrase", "Answer: 1", "1"),
        row("critical", "base", "Gate: STOP", "STOP", observed_gate="STOP"),
        row("critical", "rephrase", "Gate: CONTINUE", "CONTINUE", observed_gate="CONTINUE"),
    ]
    write_jsonl(input_path, rows)

    out_dir = tmp_path / "report"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "omnia_fragility_checker.cli",
            "--input",
            str(input_path),
            "--out-dir",
            str(out_dir),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (out_dir / "report.json").exists()
    assert (out_dir / "report.csv").exists()
    assert (out_dir / "report.html").exists()
    assert (out_dir / "certificate.json").exists()
    data = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    assert data["summary"]["critical_fragile"] == 1


def test_cli_exit_codes(tmp_path):
    input_path = tmp_path / "cases.jsonl"
    rows = [
        row("critical", "base", "Gate: STOP", "STOP", observed_gate="STOP"),
        row("critical", "rephrase", "Gate: CONTINUE", "CONTINUE", observed_gate="CONTINUE"),
    ]
    write_jsonl(input_path, rows)

    out_dir = tmp_path / "report"

    proc_fragile = subprocess.run(
        [
            sys.executable,
            "-m",
            "omnia_fragility_checker.cli",
            "--input",
            str(input_path),
            "--out-dir",
            str(out_dir),
            "--fail-on-fragile",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc_fragile.returncode == 2

    proc_critical = subprocess.run(
        [
            sys.executable,
            "-m",
            "omnia_fragility_checker.cli",
            "--input",
            str(input_path),
            "--out-dir",
            str(out_dir),
            "--fail-on-critical",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc_critical.returncode == 3
