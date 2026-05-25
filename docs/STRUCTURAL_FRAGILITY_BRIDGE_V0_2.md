# Structural Fragility Bridge v0.2

The Structural Fragility Bridge turns equivalent prompt/output variants into inspectable measurement artifacts.

It is part of the Structural Observability execution plane.

Core boundary:

~~~text
measurement != inference != decision
~~~

## Purpose

The bridge measures whether an output remains structurally stable when its form of observation changes.

It is designed to expose cases where surface validity hides structural fragility.

## Severity scale

~~~text
STABLE
SURFACE_VARIANT
ANSWER_FRAGILE
NUMERIC_FRAGILE
CRITICAL_FRAGILE
~~~

## Minimal command

~~~bash
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report
~~~

## CI gates

~~~bash
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report --fail-on-fragile
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report --fail-on-critical
~~~

Expected behavior:

~~~text
--fail-on-fragile  -> exit code 2
--fail-on-critical -> exit code 3
~~~

## Artifacts

~~~text
report.json
report.csv
report.html
fragile_cases.jsonl
critical_cases.jsonl
surface_variants.jsonl
certificate.json
~~~

## Showroom principle

~~~text
input -> command -> report -> exit code -> inspectable artifact
~~~
