# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0]

Initial public release of the HipAAsynth engine — the open-source (AGPL v3)
fairness-testing core for clinical AI accountability.

### Added

- **7-Axis Adversarial Stress Test (7AAST)** with all axes implemented.
- **6 calibrated clinical modules**: sepsis, stroke, COPD, CHF, OUD, and diabetes.
- **Polymorphic form engine** rendering each synthetic patient in 7 distinct
  documentation forms.
- **DIF fairness audit** producing a per-patient FairnessPassport with 4 metrics:
  DCS (Decision Consistency Score), ISG (Information-Source Gradient),
  LFDI (Linguistic-Form Disadvantage Index), and SAF (SDoH Amplification Factor).
- **PSF (Population Stability)** and **CC (Consistency Checker)** adversarial axes.
- **Adversarial perturbations**: noise injection, missingness, and temporal drift.
- **Regulatory mapping** to FDA Total Product Life Cycle (TPLC) and the EU AI Act.
- **Exporters** for JSON, CSV, and FHIR R5.
- **54 automated tests** with zero external dependencies (pure Python standard library).

[1.0.0]: https://github.com/hipaasynth-svg/HipAAsynth/releases/tag/v1.0.0
