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

"""DIF audit framework — public entry point for polymorphic fairness testing."""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from hipaasynth.core.config import GenerationConfig
from hipaasynth.core.schema import Patient
from hipaasynth.polymorphic import PolymorphicFormEngine
from hipaasynth.polymorphic.metrics import PolymorphicMetricCalculator
from hipaasynth.dif.model_interface import _ground_truth
from hipaasynth.dif.report import FairnessPassport


@dataclass(frozen=True)
class DIFConfig:
    """Configuration for a DIF audit run."""

    device_name: str = "Untitled Model"
    device_version: str = "0.0.0"
    dcs_threshold: float = 0.85
    isg_threshold: float = 0.15
    lfdi_threshold: float = 0.20
    saf_threshold: float = 0.20


def run_audit(
    model: Any,
    generator: Callable[[GenerationConfig], List[Patient]],
    gen_config: GenerationConfig,
    dif_config: Optional[DIFConfig] = None,
) -> List[FairnessPassport]:
    """
    Run a polymorphic DIF fairness audit.

    The audit generates synthetic patients from ``generator(gen_config)``, renders
    each patient in all seven polymorphic forms, queries ``model.predict(patient,
    form)`` for each form, and computes the polymorphic fairness metrics.

    Args:
        model: A model object implementing ``predict(patient: Patient, form: dict) -> bool``.
        generator: A callable returning a list of ``Patient`` records given a
            ``GenerationConfig``. Typically ``hipaasynth.pipelines.population_pipeline.generate_patients``.
        gen_config: Configuration controlling patient generation.
        dif_config: Optional DIF audit configuration (device name, thresholds).

    Returns:
        A list of :class:`FairnessPassport` objects, one per generated patient.
    """
    dif_config = dif_config or DIFConfig()
    form_engine = PolymorphicFormEngine()
    metric_calc = PolymorphicMetricCalculator(
        dcs_threshold=dif_config.dcs_threshold,
        isg_threshold=dif_config.isg_threshold,
        lfdi_threshold=dif_config.lfdi_threshold,
        saf_threshold=dif_config.saf_threshold,
    )

    patients = generator(gen_config)
    passports: List[FairnessPassport] = []

    for patient in patients:
        forms = form_engine.express_all(patient)
        decisions: dict[str, bool] = {}
        for form in forms:
            decisions[form["form"]] = bool(model.predict(patient, form))

        gt = _ground_truth(patient)
        metrics = metric_calc.calculate(decisions, gt)
        passport = FairnessPassport.build(
            device_name=dif_config.device_name,
            device_version=dif_config.device_version,
            patient_id=patient.demographics.patient_id,
            ground_truth=gt,
            decisions=decisions,
            metrics=metrics,
        )
        passports.append(passport)

    return passports
