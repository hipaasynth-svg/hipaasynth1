# HipAAsynth — Synthetic health data fairness testing for invisible populations.
# Copyright (C) 2026 HipAAsynth Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""FairnessPassport report for the DIF audit layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from hipaasynth.polymorphic.metrics import PolymorphicMetrics


@dataclass
class FairnessPassport:
    """
    Per-patient fairness passport produced by a DIF audit.

    A passport captures the model's decisions across all seven polymorphic
    forms for one synthetic patient, the computed polymorphic fairness metrics,
    and regulatory-compliance mappings with remediation guidance.
    """

    device_name: str
    device_version: str
    test_date: str
    patient_id: str
    ground_truth: bool
    decisions: Dict[str, bool]
    metrics: PolymorphicMetrics
    fda_tplc_mapping: Dict[str, str] = field(default_factory=dict)
    eu_ai_act_mapping: Dict[str, str] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    @classmethod
    def build(
        cls,
        device_name: str,
        device_version: str,
        patient_id: str,
        ground_truth: bool,
        decisions: Dict[str, bool],
        metrics: PolymorphicMetrics,
    ) -> "FairnessPassport":
        """Construct a fully populated passport with regulatory mappings."""
        fda = _fda_tplc_mapping(metrics)
        eu = _eu_ai_act_mapping(metrics)
        recs = _recommendations(metrics)
        return cls(
            device_name=device_name,
            device_version=device_version,
            test_date=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            patient_id=patient_id,
            ground_truth=ground_truth,
            decisions=decisions,
            metrics=metrics,
            fda_tplc_mapping=fda,
            eu_ai_act_mapping=eu,
            recommendations=recs,
        )

    def passed(self) -> bool:
        """Return True if all polymorphic metrics pass."""
        return self.metrics.all_pass()

    def to_markdown(self) -> str:
        """Render the passport as a markdown report."""
        m = self.metrics
        lines = [
            "# HipAAsynth Fairness Passport",
            "",
            "## Device Under Test",
            f"- **Device name:** {self.device_name}",
            f"- **Device version:** {self.device_version}",
            f"- **Test date (UTC):** {self.test_date}",
            f"- **Synthetic patient ID:** {self.patient_id}",
            f"- **Ground truth acute condition:** {'Yes' if self.ground_truth else 'No'}",
            "",
            "## Polymorphic Decisions",
            "| Form | Decision | Matches ground truth |",
            "|---|---|---|",
        ]
        for form_name, decision in sorted(self.decisions.items()):
            match = "✓" if decision == self.ground_truth else "✗"
            lines.append(
                f"| {form_name} | {'Yes' if decision else 'No'} | {match} |"
            )

        lines += [
            "",
            "## Polymorphic Fairness Metrics",
            "| Metric | Value | Pass |",
            "|---|---|---|",
            f"| DCS | {m.dcs:.3f} | {'PASS' if m.dcs_pass else 'FAIL'} |",
            f"| ISG | {m.isg:.3f} | {'PASS' if m.isg_pass else 'FAIL'} |",
            f"| LFDI | {m.lfdi:.3f} | {'PASS' if m.lfdi_pass else 'FAIL'} |",
            f"| SAF | {m.saf:.3f} | {'PASS' if m.saf_pass else 'FAIL'} |",
            "",
            f"**Overall result:** {'PASS' if self.passed() else 'FAIL'}",
            "",
            "## FDA TPLC Compliance Mapping",
        ]
        for stage, note in self.fda_tplc_mapping.items():
            lines.append(f"- **{stage}:** {note}")

        lines += ["", "## EU AI Act Compliance Mapping"]
        for article, note in self.eu_ai_act_mapping.items():
            lines.append(f"- **{article}:** {note}")

        if self.recommendations:
            lines += ["", "## Remediation Recommendations"]
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")

        lines += [
            "",
            "---",
            "",
            "*All data are synthetic. No PHI is used or referenced.*",
        ]
        return "\n".join(lines)


def _fda_tplc_mapping(metrics: PolymorphicMetrics) -> Dict[str, str]:
    """Map polymorphic metrics to FDA Total Product Life Cycle stages."""
    return {
        "Design & Development (21 CFR 820.30)": (
            "DCS confirms decision consistency across intended-use documentation styles. "
            f"{'PASS' if metrics.dcs_pass else 'FAIL'} — "
            f"{'consistent' if metrics.dcs_pass else 'inconsistent'} across forms."
        ),
        "Performance Evaluation / Clinical Validation": (
            "ISG measures accuracy equity between clinician-facing and patient/LEP forms. "
            f"{'PASS' if metrics.isg_pass else 'FAIL'} — "
            f"gradient = {metrics.isg:.3f}."
        ),
        "Labeling & Intended Use": (
            "LFDI captures linguistic-form disadvantage for low-literacy/LEP patients. "
            f"{'PASS' if metrics.lfdi_pass else 'FAIL'} — "
            f"index = {metrics.lfdi:.3f}."
        ),
        "Post-Market Surveillance": (
            "SAF monitors SDoH-rich CHW intake performance. "
            f"{'PASS' if metrics.saf_pass else 'FAIL'} — "
            f"factor = {metrics.saf:.3f}."
        ),
    }


def _eu_ai_act_mapping(metrics: PolymorphicMetrics) -> Dict[str, str]:
    """Map polymorphic metrics to EU AI Act obligations for high-risk AI."""
    return {
        "Art. 9 — Risk Management System": (
            "ISG and LFDI identify population-specific performance risks. "
            f"ISG {'PASS' if metrics.isg_pass else 'FAIL'}; "
            f"LFDI {'PASS' if metrics.lfdi_pass else 'FAIL'}."
        ),
        "Art. 10 — Data & Training Governance": (
            "DCS evaluates whether training-data documentation bias leaks into decisions. "
            f"DCS {'PASS' if metrics.dcs_pass else 'FAIL'}."
        ),
        "Art. 13 — Transparency & Instructions for Use": (
            "Passport documents intended-use populations and known form-dependent failure modes."
        ),
        "Art. 61 — Post-Market Monitoring": (
            "SAF tracks SDoH-amplified degradation over time. "
            f"SAF {'PASS' if metrics.saf_pass else 'FAIL'}."
        ),
    }


def _recommendations(metrics: PolymorphicMetrics) -> List[str]:
    """Generate remediation recommendations from failing metrics."""
    recs = []
    if not metrics.dcs_pass:
        recs.append(
            "Improve decision consistency: calibrate model confidence thresholds across "
            "structured and narrative inputs so the same clinical content yields the same decision."
        )
    if not metrics.isg_pass:
        recs.append(
            "Reduce information-source gradient: augment training data with patient-generated, "
            "LEP, and abbreviated clinical narratives; evaluate performance parity before deployment."
        )
    if not metrics.lfdi_pass:
        recs.append(
            "Reduce linguistic-form disadvantage: test against low-health-literacy and "
            "non-English inputs; add plain-language and interpreter-mediated intake support."
        )
    if not metrics.saf_pass:
        recs.append(
            "Address SDoH amplification: review model performance on CHW intake notes with "
            "full social-determinant context; ensure SDoH variables do not proxy for undesired exclusion."
        )
    if metrics.all_pass():
        recs.append(
            "No polymorphic fairness signals detected. Continue routine monitoring "
            "as documentation practices and patient populations evolve."
        )
    return recs
