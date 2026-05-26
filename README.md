# OMNIA Fragility Checker

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20382608.svg)](https://doi.org/10.5281/zenodo.20382608)

Detect unstable AI outputs across equivalent prompt variants.

This is a practical command-line tool for AI evaluation and QA automation.

Problem solved:

    same task + equivalent prompt variants + different outputs = fragile case

## Why this exists

AI systems can look correct on one prompt and fail on a semantically equivalent rephrasing.

That is not a philosophical problem. It is a concrete testing problem.

This tool reads a CSV or JSONL file containing multiple outputs for the same case and reports where the output changes when it should remain stable.

## Install

    pip install -e .

## Run

    omnia-fragility examples/sample_outputs.csv --out-dir report

Output:

    report/report.json
    report/report.csv
    report/report.html

## Use in CI

    omnia-fragility examples/sample_outputs.csv --out-dir report --fail-on-fragile

Exit codes:

    0 = no blocking fragility detected
    2 = fragile cases detected
    3 = critical fragile cases detected when --fail-on-critical is used

## CSV input format

Required columns:

    case_id,variant_id,output

Optional columns:

    input,expected

Minimal example:

    case_id,variant_id,input,output,expected
    refund_001,base,"When will my refund arrive?","Refunds usually take 3-5 business days.","3-5 business days"
    refund_001,rephrase_1,"How long does a refund take?","Refunds are instant.","3-5 business days"
    refund_001,rephrase_2,"When do I get my money back?","Refunds usually take 3-5 business days.","3-5 business days"

## JSONL input format

    {"case_id":"policy_001","variant_id":"base","input":"Can this request be approved?","output":"Final answer: yes","expected":"yes"}
    {"case_id":"policy_001","variant_id":"rephrase_1","input":"Is this request allowed?","output":"Final answer: no","expected":"yes"}

## Classification

The tool emits case-level statuses:

    STABLE
    SURFACE_VARIANT
    ANSWER_FRAGILE
    NUMERIC_FRAGILE
    CRITICAL_FRAGILE
    INSUFFICIENT_VARIANTS

Meaning:

    STABLE
    All normalized outputs agree.

    SURFACE_VARIANT
    Wording differs, but extracted answers agree.

    ANSWER_FRAGILE
    Final extracted answers differ.

    NUMERIC_FRAGILE
    Numeric answers differ.

    CRITICAL_FRAGILE
    At least one equivalent variant is correct and at least one is wrong.

    INSUFFICIENT_VARIANTS
    Only one variant exists, so fragility cannot be measured.

## Practical use cases

- LLM evaluation
- prompt robustness testing
- AI support-answer QA
- model comparison
- regression testing
- pre-deployment checks
- CI/CD quality gates

## What this is not

This is not a general truth detector.

It does not prove whether an answer is universally correct.

It detects a narrower and concrete failure mode:

    the output changes across equivalent variants when it should not

## Citation

If you use this software, please cite the archived release:

    Massimiliano Brighindi. OMNIA Fragility Checker v0.1.0. Zenodo. https://doi.org/10.5281/zenodo.20365172

DOI:

    10.5281/zenodo.20365172

Release:

    https://github.com/Tuttotorna/OMNIA-FRAGILITY-CHECKER/releases/tag/v0.1.0

## Background

This tool is derived from the OMNIA measurement ecosystem, but it is intentionally packaged as a standalone practical utility.

The user does not need to understand OMNIA to use this tool.

## Related ecosystem

OMNIA Fragility Checker is a standalone practical tool.

It is derived from the broader OMNIA / L.O.N. measurement ecosystem, but it does not require any other repository to run.

For readers who want to explore the underlying research context:

- L.O.N. / OMNIA core: https://github.com/Tuttotorna/lon-mirror
- OMNIA: https://github.com/Tuttotorna/OMNIA
- OMNIA Validation: https://github.com/Tuttotorna/OMNIA-VALIDATION

<!-- STRUCTURAL_OBSERVABILITY_ROLE_START -->
## Structural Observability role

This repository is one bounded measurement role inside **Structural Observability**.

Role:

~~~text
AI output fragility auditor
~~~

Boundary:

~~~text
Fragility is structural. It does not by itself decide semantic truth.
~~~

Structural Observability foundation:

- lon-mirror: https://github.com/Tuttotorna/lon-mirror
- Foundation release: https://github.com/Tuttotorna/lon-mirror/releases/tag/v0.2.2
- DOI: https://doi.org/10.5281/zenodo.20379374

Role document:

- [Structural Observability Role](docs/STRUCTURAL_OBSERVABILITY_ROLE.md)
<!-- STRUCTURAL_OBSERVABILITY_ROLE_END -->

## Structural Fragility Bridge v0.2

OMNIA Fragility Checker measures whether outputs remain structurally stable under equivalent variants.

Boundary:

~~~text
measurement != inference != decision
~~~

Showroom command:

~~~bash
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report
~~~

CI gates:

~~~bash
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report --fail-on-fragile
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report --fail-on-critical
~~~

Artifacts:

~~~text
report.json
report.csv
report.html
fragile_cases.jsonl
critical_cases.jsonl
surface_variants.jsonl
certificate.json
~~~

Severity scale:

~~~text
STABLE
SURFACE_VARIANT
ANSWER_FRAGILE
NUMERIC_FRAGILE
CRITICAL_FRAGILE
~~~

Core claim:

~~~text
surface validity is not structural stability
~~~

See also:

~~~text
docs/STRUCTURAL_FRAGILITY_BRIDGE_V0_2.md
~~~

## Release v0.2.0

Structural Fragility Bridge v0.2 is available as a reproducible showroom release.

~~~text
input -> classifier -> report -> certificate -> CI exit code
~~~

Release:

~~~text
https://github.com/Tuttotorna/OMNIA-FRAGILITY-CHECKER/releases/tag/v0.2.0
~~~

Core claim:

~~~text
surface validity is not structural stability
~~~

## DOI

~~~text
10.5281/zenodo.20382608
~~~

~~~text
https://doi.org/10.5281/zenodo.20382608
~~~

## Release v0.2.0 DOI

Structural Fragility Bridge v0.2 is archived on Zenodo.

~~~text
DOI: 10.5281/zenodo.20382608
~~~

~~~text
https://doi.org/10.5281/zenodo.20382608
~~~

## Why this fails

A short 30-second explanation of the core failure mode is available here:

~~~text
docs/WHY_THIS_FAILS.md
~~~

Core idea:

~~~text
If the task, data, constraint, and decision boundary remain equivalent,
the output should remain structurally compatible.
~~~

This is the practical meaning of:

~~~text
surface validity is not structural stability
~~~
