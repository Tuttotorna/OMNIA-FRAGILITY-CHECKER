import csv
import subprocess
import sys


def test_cli_writes_reports(tmp_path):
    input_path = tmp_path / "sample.csv"
    out_dir = tmp_path / "report"

    with input_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "variant_id", "input", "output", "expected"])
        writer.writeheader()
        writer.writerow({"case_id": "c1", "variant_id": "a", "input": "x", "output": "42", "expected": "42"})
        writer.writerow({"case_id": "c1", "variant_id": "b", "input": "y", "output": "43", "expected": "42"})

    result = subprocess.run(
        [sys.executable, "-m", "omnia_fragility_checker.cli", str(input_path), "--out-dir", str(out_dir)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0
    assert (out_dir / "report.json").exists()
    assert (out_dir / "report.csv").exists()
    assert (out_dir / "report.html").exists()


def test_cli_fail_on_fragile(tmp_path):
    input_path = tmp_path / "sample.csv"
    out_dir = tmp_path / "report"

    with input_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "variant_id", "output"])
        writer.writeheader()
        writer.writerow({"case_id": "c1", "variant_id": "a", "output": "42"})
        writer.writerow({"case_id": "c1", "variant_id": "b", "output": "43"})

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "omnia_fragility_checker.cli",
            str(input_path),
            "--out-dir",
            str(out_dir),
            "--fail-on-fragile",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 2
