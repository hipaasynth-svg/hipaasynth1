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

"""End-to-end integration test: generate → polymorphic express → DIF audit → passport."""

from hipaasynth.core.config import DEFAULT_SYNTHETIC_DISCLAIMER, GenerationConfig
from hipaasynth.dif import DIFConfig, run_audit
from hipaasynth.dif.model_interface import MockBiasedModel, MockFairModel
from hipaasynth.pipelines.population_pipeline import generate_patients
from hipaasynth.polymorphic import PolymorphicFormEngine


class TestEndToEnd:
    def test_generate_express_audit_passport_pipeline(self) -> None:
        gen_config = GenerationConfig(
            patient_count=2,
            seed=42,
            age_min=18,
            age_max=90,
            required_condition="sepsis",
            sex_ratio_female=0.5,
            ethnicity_weights=None,
            include_visits=True,
            include_labs=True,
            visits_min=1,
            visits_max=2,
            synthetic_disclaimer=DEFAULT_SYNTHETIC_DISCLAIMER,
            run_date="2026-06-24",
        )

        # Step 1: generate patients
        patients = generate_patients(gen_config)
        assert len(patients) == gen_config.patient_count

        # Step 2: express in all 7 forms
        engine = PolymorphicFormEngine()
        forms_per_patient = [engine.express_all(p) for p in patients]
        for forms in forms_per_patient:
            assert len(forms) == 7
            assert all("form" in f and "full_text" in f for f in forms)

        # Step 3: run DIF audit
        dif_config = DIFConfig(device_name="E2E-Model", device_version="1.0.0")
        passports = run_audit(MockFairModel(), generate_patients, gen_config, dif_config)

        # Step 4: verify passports
        assert len(passports) == gen_config.patient_count
        for passport in passports:
            assert passport.passed()
            assert passport.device_name == "E2E-Model"
            assert "Polymorphic Fairness Metrics" in passport.to_markdown()

    def test_biased_model_pipeline_surfaces_failures(self) -> None:
        gen_config = GenerationConfig(
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
        dif_config = DIFConfig(device_name="E2E-Biased", device_version="0.1.0")
        passports = run_audit(MockBiasedModel(), generate_patients, gen_config, dif_config)
        failing = [p for p in passports if not p.passed()]
        # The biased model should fail for at least some acute-positive patients.
        assert len(failing) > 0
