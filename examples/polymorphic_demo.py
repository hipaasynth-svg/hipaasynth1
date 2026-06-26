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

"""Polymorphic demo: render one synthetic patient in all seven documentation forms."""

import sys
from pathlib import Path

# Allow running this example without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent))

from hipaasynth.core.config import DEFAULT_SYNTHETIC_DISCLAIMER, GenerationConfig
from hipaasynth.pipelines.population_pipeline import generate_patients
from hipaasynth.polymorphic import PolymorphicFormEngine


def main() -> None:
    cfg = GenerationConfig(
        patient_count=1,
        seed=42,
        age_min=18,
        age_max=90,
        required_condition="stroke",
        sex_ratio_female=0.5,
        ethnicity_weights=None,
        include_visits=True,
        include_labs=True,
        visits_min=1,
        visits_max=2,
        synthetic_disclaimer=DEFAULT_SYNTHETIC_DISCLAIMER,
        run_date="2026-06-24",
    )
    patient = generate_patients(cfg)[0]
    engine = PolymorphicFormEngine()
    forms = engine.express_all(patient)

    print("=" * 70)
    print("POLYMORPHIC FORM DEMO")
    print("=" * 70)
    print(f"Patient: {patient.demographics.patient_id}")
    print(f"Age/Sex: {patient.demographics.age} / {patient.demographics.sex}")
    print(f"Conditions: {', '.join(c.name for c in patient.conditions if c.active)}")
    print()

    for form in forms:
        print(f"--- {form['form']} ---")
        text = form["full_text"]
        # Print first 600 characters so the demo stays readable.
        print(text[:600])
        if len(text) > 600:
            print("...")
        print()


if __name__ == "__main__":
    main()
