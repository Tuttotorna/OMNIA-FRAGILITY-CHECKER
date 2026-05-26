# Why This Fails

This document shows the core failure mode measured by OMNIA-FRAGILITY-CHECKER.

The point is not that every surface variation must produce identical text.

The point is narrower and more important:

~~~text
If the task, data, constraint, and decision boundary remain equivalent,
the output should remain structurally compatible.
~~~

When equivalent variants produce incompatible outputs, the system is fragile.

---

## Core claim

~~~text
Surface validity is not structural stability.
~~~

---

## What is being tested

The checker compares output behavior across equivalent variants.

A variant is considered operationally equivalent when these elements remain unchanged:

~~~text
task
input data
constraint
expected output contract
decision boundary
~~~

The surface may change.

The operational contract should not.

---

## Minimal example

Prompt A:

~~~text
Return only YES or NO.

The user has the admin role.
Can the user access the admin panel?
~~~

Prompt B:

~~~text
Return only: YES or NO.

The user has the admin role.
Is access to the admin panel allowed?
~~~

These prompts are not identical.

But for this test, the operational contract is equivalent:

~~~text
same user role
same resource
same access question
same output constraint
same YES/NO decision boundary
~~~

Expected structural behavior:

~~~text
YES / YES
~~~

Fragile behavior:

~~~text
YES / NO
~~~

This is not normal linguistic variation.

This is a structural incompatibility under an equivalent task.

---

## Why this matters

A model output may look correct in isolation.

But production systems do not only need one good answer.

They need stability under controlled variation.

A fragile system may pass a manual prompt check and still fail when:

~~~text
the prompt is rephrased
the sentence order changes
the formatting changes
the context wrapper changes
the same policy is expressed differently
~~~

If those changes do not alter the operational contract, but the output flips, the system should not be trusted silently.

It should be measured.

---

## What the checker reports

OMNIA-FRAGILITY-CHECKER classifies observed behavior into discrete severity classes:

~~~text
STABLE
SURFACE_VARIANT
ANSWER_FRAGILE
NUMERIC_FRAGILE
CRITICAL_FRAGILE
~~~

The important distinction is this:

~~~text
surface difference != structural rupture
equivalent task + incompatible answer = structural fragility
~~~

---

## Severity intuition

### STABLE

The output remains structurally compatible.

~~~text
YES -> YES
~~~

### SURFACE_VARIANT

The surface changes, but the structural answer remains compatible.

~~~text
Final answer: YES
**Final answer:** YES
~~~

### ANSWER_FRAGILE

The answer changes in a way that may affect interpretation or downstream behavior.

~~~text
APPROVED
LIKELY_APPROVED
~~~

### NUMERIC_FRAGILE

A numerical value changes under equivalent conditions.

~~~text
limit = 5000
limit = 50000
~~~

### CRITICAL_FRAGILE

The output flips polarity or violates the decision boundary.

~~~text
YES
NO
~~~

---

## Reproducible command

Run the minimal showroom:

~~~bash
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report
~~~

Expected artifacts:

~~~text
report.json
report.csv
report.html
fragile_cases.jsonl
critical_cases.jsonl
surface_variants.jsonl
certificate.json
~~~

---

## CI gates

Fail the pipeline on any fragile case:

~~~bash
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report --fail-on-fragile
~~~

Expected exit code:

~~~text
2
~~~

Fail only on critical fragility:

~~~bash
python -m omnia_fragility_checker.cli --input examples/sample_fragility_bridge_cases.jsonl --out-dir report --fail-on-critical
~~~

Expected exit code:

~~~text
3
~~~

---

## Why this is engineering, not belief

The checker does not claim that a model is truthful.

It does not decide what the final business action should be.

It measures whether structure remains compatible under controlled variation.

Boundary:

~~~text
measurement != inference != decision
~~~

Operational chain:

~~~text
input -> command -> report -> certificate -> CI exit code
~~~

---

## One-line summary

~~~text
A correct-looking answer is not enough if an equivalent observation can make the structure collapse.
~~~
