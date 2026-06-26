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

"""Full fairness passport demo: generate, audit, and render a markdown report."""

import sys
from pathlib import Path

# Allow running this example without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent))

from hipaasynth.core.config import DEFAULT_SYNTHETIC_DISCLAIMER, GenerationConfig
from hipaasynth.dif import DIFConfig, run_audit
from hipaasynth.dif.model_interface import MockBiasedModel
from hipaasynth.pipelines.population_pipeline import generate_patients


def main() -> None:
    cfg = GenerationConfig(
        patient_count=3,
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

    dif_config = DIFConfig(
        device_name="Demo Acute Triage Model",
        device_version="2.0.0",
    )

    print("=" * 70)
    print("FAIRNESS PASSPORT DEMO")
    print("=" * 70)
    print("Running DIF audit on synthetic acute-stroke patients with a biased model...")
    print()

    passports = run_audit(MockBiasedModel(), generate_patients, cfg, dif_config)

    for passport in passports:
        print(passport.to_markdown())
        print("\n" + "=" * 70 + "\n")

    # Final summary
    passed = sum(1 for p in passports if p.passed())
    print(f"Summary: {passed}/{len(passports)} patients passed all polymorphic fairness checks.")


if __name__ == "__main__":
    main()
