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

"""Polymorphic clinical-form generator for the HipAAsynth engine.

The ``PolymorphicFormEngine`` renders the same synthetic ``Patient`` record in
seven distinct documentation styles.  Each style mirrors a real-world information
source that downstream clinical AI systems may encounter, from structured FHIR
bundles to patient-generated narratives.
"""

import json
from enum import Enum
from typing import Any

from hipaasynth.core.schema import Patient
from hipaasynth.exporters.exporters import _patient_to_fhir


class Form(str, Enum):
    """Canonical polymorphic form identifiers."""

    FHIR_STRUCTURED = "FHIR_STRUCTURED"
    PHYSICIAN_SOAP = "PHYSICIAN_SOAP"
    MIDLEVEL_ABBREVIATED = "MIDLEVEL_ABBREVIATED"
    PATIENT_HIGH_LITERACY = "PATIENT_HIGH_LITERACY"
    PATIENT_LOW_LITERACY = "PATIENT_LOW_LITERACY"
    LEP_TRANSLATED = "LEP_TRANSLATED"
    CHW_SDOH_RICH = "CHW_SDOH_RICH"


class PolymorphicFormEngine:
    """Render a ``Patient`` in one or all polymorphic forms."""

    def express(self, patient: Patient, form: Form | str) -> dict[str, Any]:
        """Return a single form representation of ``patient``.

        Args:
            patient: A synthetic patient from the HipAAsynth engine.
            form: One of the seven :class:`Form` values (or its string name).

        Returns:
            A dictionary with at least ``{"form": <form_name>, "full_text": <str>}``.
        """
        form = Form(form)
        builder = {
            Form.FHIR_STRUCTURED: self._fhir_structured,
            Form.PHYSICIAN_SOAP: self._physician_soap,
            Form.MIDLEVEL_ABBREVIATED: self._midlevel_abbreviated,
            Form.PATIENT_HIGH_LITERACY: self._patient_high_literacy,
            Form.PATIENT_LOW_LITERACY: self._patient_low_literacy,
            Form.LEP_TRANSLATED: self._lep_translated,
            Form.CHW_SDOH_RICH: self._chw_sdoh_rich,
        }[form]
        return {"form": form.value, "full_text": builder(patient)}

    def express_all(self, patient: Patient) -> list[dict[str, Any]]:
        """Return all seven form representations of ``patient``."""
        return [self.express(patient, form) for form in Form]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _demos(patient: Patient) -> dict[str, Any]:
        return {
            "patient_id": patient.demographics.patient_id,
            "age": patient.demographics.age,
            "sex": patient.demographics.sex,
            "ethnicity": patient.demographics.ethnicity,
            "bmi": patient.anthropometrics.bmi,
            "bmi_category": patient.anthropometrics.bmi_category,
        }

    @staticmethod
    def _conditions(patient: Patient) -> list[str]:
        return [c.name for c in patient.conditions if c.active]

    @staticmethod
    def _recent_visit(patient: Patient) -> dict[str, Any]:
        visits = patient.visits
        if not visits:
            return {"type": "none", "date": "unknown", "diagnosis": "none", "labs": []}
        visit = visits[-1]
        return {
            "type": visit.visit_type,
            "date": visit.visit_date,
            "diagnosis": visit.primary_diagnosis,
            "labs": [f"{lab.lab_name} {lab.value} {lab.unit}" for lab in visit.labs],
        }

    @staticmethod
    def _observations(patient: Patient) -> dict[str, Any]:
        return patient.observations or {}

    @staticmethod
    def _acuity_line(obs: dict[str, Any]) -> str:
        """Build a one-line acuity summary from sepsis/stroke observations."""
        parts: list[str] = []
        if "sepsis_flag" in obs:
            parts.append(
                f"Sepsis-3 screen {'POSITIVE' if obs.get('sepsis_flag') else 'negative'}"
            )
            parts.append(f"Temp {obs.get('temperature_c_initial', '?')}°C")
            parts.append(f"HR {obs.get('heart_rate_initial', '?')} bpm")
            parts.append(f"Lactate {obs.get('lactate_initial', '?')} mmol/L")
        if "stroke_flag" in obs:
            parts.append(
                f"Stroke evaluation {'POSITIVE' if obs.get('stroke_flag') else 'negative'}"
            )
            parts.append(f"NIHSS {obs.get('nihss_score', '?')} ({obs.get('nihss_category', '?')})")
            parts.append(f"Onset-to-door {obs.get('onset_to_door_minutes', '?')} min")
        if not parts:
            parts.append("No acute sepsis/stroke observation bundle recorded")
        return " | ".join(parts)

    # ------------------------------------------------------------------
    # Form builders
    # ------------------------------------------------------------------

    @staticmethod
    def _fhir_structured(patient: Patient) -> str:
        resources = _patient_to_fhir(patient)
        bundle = {
            "resourceType": "Bundle",
            "id": f"poly-{patient.demographics.patient_id}",
            "type": "collection",
            "entry": [
                {"fullUrl": f"urn:uuid:{r['id']}", "resource": r} for r in resources
            ],
        }
        return json.dumps(bundle, indent=2)

    def _physician_soap(self, patient: Patient) -> str:
        d = self._demos(patient)
        conds = self._conditions(patient)
        visit = self._recent_visit(patient)
        obs = self._observations(patient)

        lines = [
            "SUBJECTIVE:",
            f"  {d['age']}-year-old {d['sex']} with {', '.join(conds) if conds else 'no active conditions'}.",
            f"  Most recent encounter: {visit['type']} on {visit['date']} for {visit['diagnosis']}.",
            "",
            "OBJECTIVE:",
            f"  Vitals/labs: {self._acuity_line(obs)}",
            f"  BMI {d['bmi']:.1f} kg/m2 ({d['bmi_category']}).",
            f"  Labs on file: {'; '.join(visit['labs']) if visit['labs'] else 'none' }.",
            "",
            "ASSESSMENT:",
            f"  {', '.join(conds) if conds else 'No active diagnoses'}.",
            f"  Acuity: {self._acuity_line(obs)}.",
            "",
            "PLAN:",
            "  Continue chronic disease management; reassess per protocol.",
            "  Return precautions given.",
        ]
        return "\n".join(lines)

    def _midlevel_abbreviated(self, patient: Patient) -> str:
        d = self._demos(patient)
        conds = self._conditions(patient)
        visit = self._recent_visit(patient)
        obs = self._observations(patient)

        cond_str = "/".join(conds) if conds else "none"
        lab_str = "; ".join(visit["labs"]) if visit["labs"] else "none"
        return (
            f"{d['age']}yo {d['sex']} {d.get('ethnicity', 'unknown')} | "
            f"{cond_str} | {visit['type']} {visit['date']} | "
            f"{self._acuity_line(obs)} | BMI {d['bmi']:.1f} | "
            f"labs: {lab_str}"
        )

    def _patient_high_literacy(self, patient: Patient) -> str:
        d = self._demos(patient)
        conds = self._conditions(patient)
        visit = self._recent_visit(patient)
        obs = self._observations(patient)

        cond_text = (
            ", ".join(conds)
            if conds
            else "no long-term health conditions that I know of"
        )
        pain_scale = "I would rate my worry today as 4 out of 10."

        lines = [
            f"I am a {d['age']}-year-old {d['sex']}. My doctor says I have {cond_text}.",
            f"My most recent visit was a {visit['type'].lower()} on {visit['date']}.",
            f"The reason was: {visit['diagnosis']}.",
            f"My body mass index is {d['bmi']:.1f}, which is in the {d['bmi_category']} range.",
            f"My recent test results: {'; '.join(visit['labs']) if visit['labs'] else 'no labs recorded'}.",
            f"I also want to mention: {self._acuity_line(obs)}.",
            pain_scale,
        ]
        return " ".join(lines)

    def _patient_low_literacy(self, patient: Patient) -> str:
        d = self._demos(patient)
        conds = self._conditions(patient)
        visit = self._recent_visit(patient)
        obs = self._observations(patient)

        cond_text = (
            " and ".join(c.replace("_", " ") for c in conds)
            if conds
            else "nothing the doctor gave a name to"
        )

        body_feeling = "My body feels tired and heavy lately."
        if "sepsis_flag" in obs and obs.get("sepsis_flag"):
            body_feeling = "I feel very hot and confused, like something bad is spreading inside me."
        elif "stroke_flag" in obs and obs.get("stroke_flag"):
            body_feeling = "One side of my face feels strange and my words come out wrong."

        lines = [
            f"I am {d['age']} years old. I am a {d['sex']}.",
            f"The doctor told me I have {cond_text}.",
            f"I went to the {visit['type'].lower()} place on {visit['date']}",
            f"because {visit['diagnosis']} was bothering me.",
            body_feeling,
            f"My weight and height make my belly size {d['bmi_category']}.",
            "They took some blood, but I do not know the numbers.",
        ]
        return " ".join(lines)

    def _lep_translated(self, patient: Patient) -> str:
        d = self._demos(patient)
        conds = self._conditions(patient)
        visit = self._recent_visit(patient)
        obs = self._observations(patient)

        cond_text = (
            ", ".join(c.replace("_", " ") for c in conds)
            if conds
            else "no diagnosis recorded"
        )

        lines = [
            f"Age: {d['age']} years. Sex: {d['sex']}.",
            f"Primary conditions: {cond_text}.",
            f"Most recent encounter: {visit['type']} on {visit['date']}.",
            f"Chief concern: {visit['diagnosis']}.",
            f"Clinical findings: {self._acuity_line(obs)}.",
            "[NOTE: Limited English proficiency — interpreter services required.]",
            f"BMI: {d['bmi']:.1f} kg/m2.",
        ]
        return " ".join(lines)

    def _chw_sdoh_rich(self, patient: Patient) -> str:
        d = self._demos(patient)
        conds = self._conditions(patient)
        visit = self._recent_visit(patient)
        obs = self._observations(patient)

        cond_text = ", ".join(conds) if conds else "none reported"

        # Synthetic SDoH proxies inferred from the existing profile-free patient.
        # These are intentionally broad placeholders; real CHW intakes use validated
        # screening tools (PRAPARE, AHC-HRSN).
        housing = "stable"
        transport = "has reliable ride"
        food_security = "no current food insecurity reported"
        insurance = "insurance status not recorded in this synthetic record"

        lines = [
            "COMMUNITY HEALTH WORKER INTAKE NOTE",
            f"Date: {visit['date']} | Participant ID: {d['patient_id']}",
            "",
            "SOCIAL DETERMINANTS OF HEALTH:",
            f"  Housing: {housing}",
            f"  Transportation: {transport}",
            f"  Food security: {food_security}",
            f"  Insurance/coverage: {insurance}",
            "",
            "CLINICAL CONTEXT:",
            f"  {d['age']}-year-old {d['sex']} ({d['ethnicity']}) with {cond_text}.",
            f"  BMI {d['bmi']:.1f} ({d['bmi_category']}).",
            f"  Recent visit: {visit['type']} for {visit['diagnosis']}.",
            f"  Acuity note: {self._acuity_line(obs)}.",
            "",
            "CHW OBSERVATIONS:",
            "  Participant engaged, no immediate safety concerns.",
            "  Referred to care coordinator for follow-up.",
        ]
        return "\n".join(lines)
