import csv
import json

from omnia_fragility_checker.core import (
    analyze,
    classify_case,
    extract_final_answer,
    extract_last_number,
    normalize_text,
    read_records,
    VariantRecord,
)


def test_normalize_text_basic():
    assert normalize_text("  Hello   WORLD!! ") == "hello world"


def test_extract_last_number():
    assert extract_last_number("The answer is 42.") == "42"
    assert extract_last_number("x = 10.0") == "10"
    assert extract_last_number("no number") is None


def test_extract_final_answer_numeric():
    assert extract_final_answer("The answer is 42.") == "42"
    assert extract_final_answer("Final answer: 42") == "42"


def test_classify_critical_fragile_case():
    rows = [
        VariantRecord("c1", "a", "Final answer: 42", expected="42"),
        VariantRecord("c1", "b", "Final answer: 43", expected="42"),
    ]
    result = classify_case("c1", rows)
    assert result.status == "CRITICAL_FRAGILE"
    assert result.severity == "HIGH"


def test_classify_numeric_fragile_without_expected():
    rows = [
        VariantRecord("c1", "a", "Final answer: 42"),
        VariantRecord("c1", "b", "Final answer: 43"),
    ]
    result = classify_case("c1", rows)
    assert result.status == "NUMERIC_FRAGILE"


def test_analyze_csv(tmp_path):
    p = tmp_path / "sample.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "variant_id", "input", "output", "expected"])
        writer.writeheader()
        writer.writerow({"case_id": "c1", "variant_id": "a", "input": "x", "output": "42", "expected": "42"})
        writer.writerow({"case_id": "c1", "variant_id": "b", "input": "y", "output": "43", "expected": "42"})

    result = analyze(str(p))
    assert result["summary"]["total_cases"] == 1
    assert result["summary"]["critical_fragile_cases"] == 1


def test_analyze_jsonl(tmp_path):
    p = tmp_path / "sample.jsonl"
    rows = [
        {"case_id": "c1", "variant_id": "a", "input": "x", "output": "yes", "expected": "yes"},
        {"case_id": "c1", "variant_id": "b", "input": "y", "output": "no", "expected": "yes"},
    ]
    p.write_text("\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8")

    result = analyze(str(p))
    assert result["summary"]["total_cases"] == 1
    assert result["summary"]["critical_fragile_cases"] == 1


def test_read_records_rejects_unknown_suffix(tmp_path):
    p = tmp_path / "bad.txt"
    p.write_text("x", encoding="utf-8")
    try:
        read_records(str(p))
    except ValueError as e:
        assert "Input must be" in str(e)
    else:
        raise AssertionError("Expected ValueError")
