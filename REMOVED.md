# Removed Components

This document lists components that were removed from `hipaasynth-engine` during
the repository split and cleanup.

## Orinn / external-evaluation code

The following files and directories contained integrations with the external
Orinn evaluation API, ORINN_API_KEY handling, or were cloned external validation
harness code. They have been removed or replaced with stubs.

### Replaced with a stub

- `hipaasynth/adversarial/evaluator.py`
  - The original clinical-AI evaluator implementation was removed.
  - It is now a compatibility stub that exports `Evaluator`, `SYSTEM_PROMPT`,
    `_build_messages`, and `_parse_yes_no`.
  - Calling `Evaluator.evaluate(...)` or any helper raises:
    `NotImplementedError: Install evaluation provider separately`.

### Deleted

- `hipaasynth/adversarial/axis6_backfill_raw.py`
- `hipaasynth/adversarial/axis6_backfill_incremental.py`
- `hipaasynth/adversarial/axis6_probe_requery.py`
- `hipaasynth/adversarial/axis6_rerun.py`
  - These were Orinn-API backfill / probe / rerun tools.

- `hipaasynth/validation_harness/`
  - External cloned validation harness (not HipAAsynth-owned code).

### Environment-variable cleanup

- All `ORINN_API_KEY` environment-variable reads were removed from the Python
  source tree.

## What remains

- Core synthetic-patient generation (`hipaasynth/core/`)
- Clinical modules: diabetes, oncology, fabry, sma, chf, copd, oud, stroke,
  sepsis, cardiology, dmd, snf
- Pipeline generation (`hipaasynth/pipelines/`)
- Adversarial perturbation engine (`hipaasynth/adversarial/perturbations.py`)
- Temporal engine (`hipaasynth/adversarial/temporal.py`)
- Binary-search reducer (`hipaasynth/adversarial/reducer.py`)
- Axis-6 guardrail stress-test runner (`hipaasynth/adversarial/axis6.py`)
  - This file no longer calls Orinn APIs; it accepts an injectable `model_fn`.
- Exporters, validation, tests, and run scripts

## Verification

```bash
cd hipaasynth-engine
grep -ri "orinn\|ORINN" --include="*.py" .
```

Expected result: **zero results**.
