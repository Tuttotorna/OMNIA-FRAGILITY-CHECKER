"""Structural fragility classification core.

The classifier is deterministic and bounded.

It does not infer semantic truth.
It measures whether supplied outputs remain structurally stable
under equivalent variants.

Boundary:
measurement != inference != decision
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
import hashlib
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence


SEVERITY_ORDER = {
    "STABLE": 0,
    "SURFACE_VARIANT": 1,
    "ANSWER_FRAGILE": 2,
    "NUMERIC_FRAGILE": 3,
    "CRITICAL_FRAGILE": 4,
}

CRITICAL_TOKENS = {
    "pass", "fail", "passed", "failed",
    "go", "no_go", "nogo",
    "continue", "stop",
    "safe", "unsafe",
    "allow", "deny", "allowed", "denied",
    "accept", "reject", "accepted", "rejected",
    "true", "false", "yes", "no",
    "valid", "invalid",
    "stable", "unstable",
}

CRITICAL_FIELDS = (
    "decision",
    "gate",
    "status",
    "verdict",
    "classification",
    "label",
    "risk",
    "safe",
    "allowed",
    "accepted",
    "passed",
    "observed_decision",
    "expected_decision",
    "observed_gate",
    "expected_gate",
    "observed_status",
    "expected_status",
)

_NUMBER_RE = re.compile(r"[-+]?(?:\d+\.\d+|\d+|\.\d+)(?:[eE][-+]?\d+)?")


@dataclass(frozen=True)
class PairClassification:
    case_id: str
    base_variant_id: str
    variant_id: str
    severity: str
    reason: str
    base_hash: str
    variant_hash: str
    base_normalized: str
    variant_normalized: str
    base_final: str
    variant_final: str
    numeric_delta: Optional[str] = None
    critical_flip: Optional[str] = None


@dataclass(frozen=True)
class CaseClassification:
    case_id: str
    severity: str
    reason: str
    base_variant_id: str
    variants: int
    pair_results: List[Dict[str, Any]]


def normalize_surface(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"`{1,3}", "", text)
    text = re.sub(r"[*_~>#]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_answer(value: Any) -> str:
    text = normalize_surface(value).lower()
    text = re.sub(r"^(final answer|answer|result|value)\s*[:=]\s*", "", text)
    return text.strip(" .,:;")


def stable_hash(value: Any) -> str:
    text = normalize_surface(value)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _field(record: Dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in record and record[name] is not None:
            return record[name]
    return None


def raw_output_text(record: Dict[str, Any]) -> str:
    value = _field(record, "model_output", "output", "response", "model_raw_output")
    if value is None:
        value = final_value(record)
    if value is None:
        return ""
    return str(value).strip()


def output_text(record: Dict[str, Any]) -> str:
    return normalize_surface(raw_output_text(record))


def final_value(record: Dict[str, Any]) -> str:
    value = _field(
        record,
        "final_answer",
        "observed_answer",
        "answer",
        "value",
        "output_value",
        "model_final_extracted_answer",
    )
    if value is None:
        value = _field(record, "model_output", "output", "response", "model_raw_output")
    return normalize_answer(value)


def _decimal_or_none(value: Any) -> Optional[Decimal]:
    text = normalize_answer(value)
    if not text:
        return None
    if not _NUMBER_RE.fullmatch(text):
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def extract_numbers(value: Any) -> List[Decimal]:
    text = normalize_surface(value)
    out: List[Decimal] = []
    for item in _NUMBER_RE.findall(text):
        try:
            out.append(Decimal(item))
        except InvalidOperation:
            pass
    return out


def critical_value(record: Dict[str, Any]) -> Optional[str]:
    for key in CRITICAL_FIELDS:
        if key in record and record[key] is not None:
            val = normalize_answer(record[key])
            if val:
                return val
    val = final_value(record)
    if val in CRITICAL_TOKENS:
        return val
    return None


def detect_critical_flip(base: Dict[str, Any], variant: Dict[str, Any]) -> Optional[str]:
    b = critical_value(base)
    v = critical_value(variant)
    if b is not None and v is not None and b != v:
        return f"{b} -> {v}"

    b_final = final_value(base)
    v_final = final_value(variant)
    if b_final in CRITICAL_TOKENS and v_final in CRITICAL_TOKENS and b_final != v_final:
        return f"{b_final} -> {v_final}"

    return None


def detect_numeric_delta(base: Dict[str, Any], variant: Dict[str, Any]) -> Optional[str]:
    b_final = final_value(base)
    v_final = final_value(variant)

    b_num = _decimal_or_none(b_final)
    v_num = _decimal_or_none(v_final)
    if b_num is not None and v_num is not None and b_num != v_num:
        return str(v_num - b_num)

    b_nums = extract_numbers(output_text(base))
    v_nums = extract_numbers(output_text(variant))
    if b_nums and v_nums and b_nums != v_nums:
        return "numeric_sequence_changed"

    return None


def classify_pair(base: Dict[str, Any], variant: Dict[str, Any]) -> PairClassification:
    case_id = str(_field(base, "case_id", "id") or _field(variant, "case_id", "id") or "unknown_case")
    base_variant_id = str(_field(base, "variant_id", "prompt_variant") or "base")
    variant_id = str(_field(variant, "variant_id", "prompt_variant") or "variant")

    b_raw = raw_output_text(base)
    v_raw = raw_output_text(variant)
    b_out = output_text(base)
    v_out = output_text(variant)
    b_final = final_value(base)
    v_final = final_value(variant)

    b_hash = stable_hash(b_out)
    v_hash = stable_hash(v_out)

    critical_flip = detect_critical_flip(base, variant)
    if critical_flip is not None:
        return PairClassification(
            case_id=case_id,
            base_variant_id=base_variant_id,
            variant_id=variant_id,
            severity="CRITICAL_FRAGILE",
            reason="decision_boundary_or_polarity_changed",
            base_hash=b_hash,
            variant_hash=v_hash,
            base_normalized=b_out,
            variant_normalized=v_out,
            base_final=b_final,
            variant_final=v_final,
            critical_flip=critical_flip,
        )

    numeric_delta = detect_numeric_delta(base, variant)
    if numeric_delta is not None:
        return PairClassification(
            case_id=case_id,
            base_variant_id=base_variant_id,
            variant_id=variant_id,
            severity="NUMERIC_FRAGILE",
            reason="numeric_value_changed",
            base_hash=b_hash,
            variant_hash=v_hash,
            base_normalized=b_out,
            variant_normalized=v_out,
            base_final=b_final,
            variant_final=v_final,
            numeric_delta=numeric_delta,
        )

    if b_final != v_final:
        return PairClassification(
            case_id=case_id,
            base_variant_id=base_variant_id,
            variant_id=variant_id,
            severity="ANSWER_FRAGILE",
            reason="final_answer_changed",
            base_hash=b_hash,
            variant_hash=v_hash,
            base_normalized=b_out,
            variant_normalized=v_out,
            base_final=b_final,
            variant_final=v_final,
        )

    if b_raw != v_raw:
        return PairClassification(
            case_id=case_id,
            base_variant_id=base_variant_id,
            variant_id=variant_id,
            severity="SURFACE_VARIANT",
            reason="raw_surface_changed_but_final_structure_preserved",
            base_hash=b_hash,
            variant_hash=v_hash,
            base_normalized=b_out,
            variant_normalized=v_out,
            base_final=b_final,
            variant_final=v_final,
        )

    return PairClassification(
        case_id=case_id,
        base_variant_id=base_variant_id,
        variant_id=variant_id,
        severity="STABLE",
        reason="normalized_output_and_final_answer_stable",
        base_hash=b_hash,
        variant_hash=v_hash,
        base_normalized=b_out,
        variant_normalized=v_out,
        base_final=b_final,
        variant_final=v_final,
    )


def classify_case(records: Sequence[Dict[str, Any]]) -> CaseClassification:
    if not records:
        raise ValueError("classify_case requires at least one record")

    case_id = str(_field(records[0], "case_id", "id") or "unknown_case")

    base = None
    for row in records:
        variant = str(_field(row, "variant_id", "prompt_variant") or "").lower()
        if variant in {"base", "canonical", "control"}:
            base = row
            break

    if base is None:
        base = records[0]

    base_variant_id = str(_field(base, "variant_id", "prompt_variant") or "base")
    pair_results = []

    for row in records:
        if row is base:
            continue
        pair_results.append(classify_pair(base, row))

    if not pair_results:
        severity = "STABLE"
        reason = "single_record_case"
    else:
        worst = max(pair_results, key=lambda r: SEVERITY_ORDER[r.severity])
        severity = worst.severity
        reason = worst.reason

    return CaseClassification(
        case_id=case_id,
        severity=severity,
        reason=reason,
        base_variant_id=base_variant_id,
        variants=len(records),
        pair_results=[asdict(x) for x in pair_results],
    )


def classify_records(records: Iterable[Dict[str, Any]]) -> List[CaseClassification]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for row in records:
        cid = str(_field(row, "case_id", "id") or "unknown_case")
        groups.setdefault(cid, []).append(row)
    return [classify_case(groups[cid]) for cid in sorted(groups)]


def summary_from_cases(cases: Sequence[CaseClassification]) -> Dict[str, Any]:
    counts = {name: 0 for name in SEVERITY_ORDER}
    for case in cases:
        counts[case.severity] += 1

    fragile = counts["ANSWER_FRAGILE"] + counts["NUMERIC_FRAGILE"] + counts["CRITICAL_FRAGILE"]
    total = len(cases)

    return {
        "total_cases": total,
        "stable": counts["STABLE"],
        "surface_variant": counts["SURFACE_VARIANT"],
        "answer_fragile": counts["ANSWER_FRAGILE"],
        "numeric_fragile": counts["NUMERIC_FRAGILE"],
        "critical_fragile": counts["CRITICAL_FRAGILE"],
        "fragile_cases": fragile,
        "fragility_rate": round(fragile / total, 6) if total else 0.0,
        "critical_rate": round(counts["CRITICAL_FRAGILE"] / total, 6) if total else 0.0,
        "max_severity": max((case.severity for case in cases), key=lambda x: SEVERITY_ORDER[x], default="STABLE"),
        "boundary": "measurement != inference != decision",
    }


def to_jsonable(cases: Sequence[CaseClassification]) -> List[Dict[str, Any]]:
    return [asdict(case) for case in cases]
