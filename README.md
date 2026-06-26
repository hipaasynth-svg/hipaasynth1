# HipAAsynth Engine

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**HipAAsynth** is a synthetic health-data fairness-testing engine for invisible populations.

It generates realistic synthetic patients, renders each record in seven distinct clinical documentation styles, and audits any binary decision model for fairness degradation across those styles.

## Quick start

```bash
pip install -e .
python -c "from hipaasynth.dif import run_audit; print('OK')"
```

Run a full fairness audit in a few lines:

```python
from hipaasynth.core.config import DEFAULT_SYNTHETIC_DISCLAIMER, GenerationConfig
from hipaasynth.dif import DIFConfig, run_audit
from hipaasynth.dif.model_interface import MockBiasedModel
from hipaasynth.pipelines.population_pipeline import generate_patients

cfg = GenerationConfig(
    patient_count=5,
    seed=42,
    required_condition="stroke",
    synthetic_disclaimer=DEFAULT_SYNTHETIC_DISCLAIMER,
)

passports = run_audit(
    MockBiasedModel(),
    generate_patients,
    cfg,
    DIFConfig(device_name="Demo Model", device_version="1.0.0"),
)

for passport in passports:
    print(passport.patient_id, "PASS" if passport.passed() else "FAIL")
    print(passport.to_markdown())
```

Each `passport` is a `FairnessPassport` containing:

- Device name, version, and test date
- The model’s decision on all seven forms
- Polymorphic fairness metrics (DCS, ISG, LFDI, SAF) with pass/fail flags
- FDA Total Product Life Cycle compliance mapping
- EU AI Act compliance mapping
- Remediation recommendations

## The seven polymorphic forms

The same synthetic patient can be expressed as:

1. **FHIR_STRUCTURED** — FHIR R5 Bundle
2. **PHYSICIAN_SOAP** — Formal clinical prose, A/P format
3. **MIDLEVEL_ABBREVIATED** — Telegraphic, time-pressed documentation
4. **PATIENT_HIGH_LITERACY** — Lay medical terms, first-person, pain scale
5. **PATIENT_LOW_LITERACY** — Metaphorical, somatic, no medical terminology
6. **LEP_TRANSLATED** — Simplified/broken English, gesture references
7. **CHW_SDOH_RICH** — Community health worker intake with full SDoH context

## Optional FHIR support

To enable FHIR R5 exporters:

```bash
pip install -e '.[fhir]'
```

## Examples

See the [`examples/`](./examples) directory:

- `examples/polymorphic_demo.py` — render one patient in all seven forms
- `examples/rare_disease_demo.py` — run DIF on rare-disease patients
- `examples/fairness_passport_demo.py` — generate a full markdown Fairness Passport

## Tests

```bash
python -m pytest
```

## Research tools

For proprietary research extensions — including Orinn evaluator integration, LLM harnesses, and validation pipelines — see [`hipaasynth-research/`](../hipaasynth-research).

## License

AGPL-3.0-or-later. See [LICENSE.md](./LICENSE.md).
