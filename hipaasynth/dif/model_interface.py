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

"""DIF mock models for demonstrating polymorphic fairness signals.

These models are intentionally simple.  They operate on the synthetic patient's
acute-condition ground truth (sepsis_flag or stroke_flag in ``observations``)
and produce deterministic binary decisions for every polymorphic form.
"""

from typing import Any

from hipaasynth.core.schema import Patient
from hipaasynth.polymorphic.forms import Form


def _ground_truth(patient: Patient) -> bool:
    """Return the acute-condition ground truth for a synthetic patient."""
    obs = patient.observations or {}
    return bool(obs.get("sepsis_flag") or obs.get("stroke_flag"))


class MockFairModel:
    """Reference fair model: consistent, correct decisions across all 7 forms."""

    def predict(self, patient: Patient, form: dict[str, Any]) -> bool:
        """Return the ground-truth decision regardless of form."""
        return _ground_truth(patient)


class MockBiasedModel:
    """
    Reference biased model: accurate on clinician-facing forms (1-3) but
    systematically under-triages patient-facing and LEP forms (4-6).

    Under-triage here means positive acute cases are classified as negative
    for the disadvantaged forms, while negative cases remain correctly
    classified.
    """

    UNDER_TRIAGED_FORMS = {
        Form.PATIENT_HIGH_LITERACY.value,
        Form.PATIENT_LOW_LITERACY.value,
        Form.LEP_TRANSLATED.value,
    }

    def predict(self, patient: Patient, form: dict[str, Any]) -> bool:
        """Return ground truth for clinician/CHW forms; under-triage patient/LEP."""
        gt = _ground_truth(patient)
        form_name = form.get("form", "")
        if form_name in self.UNDER_TRIAGED_FORMS and gt:
            return False
        return gt
