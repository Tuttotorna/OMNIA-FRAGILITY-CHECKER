# OMNIA Fragility Checker v0.2.0

Structural Fragility Bridge release.

This release turns equivalent output variants into inspectable structural fragility measurements.

## Core boundary

~~~text
measurement != inference != decision
~~~

## Main entrypoint

~~~bash
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report
~~~

## CI gates

~~~bash
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report --fail-on-fragile
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report --fail-on-critical
~~~

Expected gate behavior:

~~~text
--fail-on-fragile  -> exit code 2
--fail-on-critical -> exit code 3
~~~

## Severity scale

~~~text
STABLE
SURFACE_VARIANT
ANSWER_FRAGILE
NUMERIC_FRAGILE
CRITICAL_FRAGILE
~~~

## Showroom demo

~~~text
total_cases:       5
stable:            1
surface_variant:   1
answer_fragile:    1
numeric_fragile:   1
critical_fragile:  1
fragile_cases:     3
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

## Core claim

~~~text
surface validity is not structural stability
~~~

## Commit

~~~text
f7946f0
~~~

## DOI

~~~text
10.5281/zenodo.20382608
~~~

~~~text
https://doi.org/10.5281/zenodo.20382608
~~~
