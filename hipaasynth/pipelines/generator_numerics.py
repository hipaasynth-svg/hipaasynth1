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

"""Numeric/lab value generator. All randomness from pipeline-owned rng."""
import random
import math
from datetime import datetime, timedelta
from hipaasynth.core.schema import LabResult, Visit, Condition

LAB_DEFINITIONS = {
    "Glucose": {"unit": "mg/dL", "reference_range": "70-99", "baseline_mean": 95.0, "baseline_std": 18.0},
    "Creatinine": {"unit": "mg/dL", "reference_range": "0.6-1.3", "baseline_mean": 1.0, "baseline_std": 0.25},
    "LDL": {"unit": "mg/dL", "reference_range": "<100", "baseline_mean": 111.0, "baseline_std": 32.0},
    "WBC": {"unit": "10^9/L", "reference_range": "4.0-11.0", "baseline_mean": 7.0, "baseline_std": 2.0},
}

CONDITION_LAB_MODIFIERS = {
    ("type2_diabetes", "Glucose"): "diabetic_glucose",
    ("chronic_kidney_disease", "Creatinine"): (1.05, 1.25),
    ("hyperlipidemia", "LDL"): (160.0, 260.0),
    ("sepsis", "WBC"): (11.0, 21.0),
}

_REFERENCE_DATE = datetime(2024, 6, 15)

def _normal_distribution(rng, mean, std):
    u1 = rng.random()
    u2 = rng.random()
    z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return mean + z0 * std

def _generate_lab_value(rng, lab_name, condition_names):
    lab_def = LAB_DEFINITIONS[lab_name]
    baseline = _normal_distribution(rng, lab_def["baseline_mean"], lab_def["baseline_std"])
    for condition in condition_names:
        key = (condition, lab_name)
        if key in CONDITION_LAB_MODIFIERS:
            modifier = CONDITION_LAB_MODIFIERS[key]
            if modifier == "diabetic_glucose":
                baseline = max(baseline, _normal_distribution(rng, 164.0, 40.0))
            else:
                min_val, max_val = modifier
                baseline = max(baseline, rng.uniform(min_val, max_val))
    # Physiological floors — prevent physically implausible values
    # Sources: ADA (glucose), KDIGO (creatinine), Sepsis-3 (WBC), ACC/AHA (LDL)
    FLOORS = {
        "Glucose": 65.0,    # ADA: severe hypoglycemia <54; 65 is conservative clinical floor
        "Creatinine": 0.4,  # Below 0.4 not physiologically plausible in adults
        "LDL": 20.0,        # Below 20 seen only in severe malnutrition/aggressive therapy
        "WBC": 2.0,         # Extreme leukopenia floor; Sepsis-3 defines <4 as abnormal
    }
    floor = FLOORS.get(lab_name, 0.0)
    return round(max(floor, baseline), 2)

def _generate_visit_date(rng):
    offset_days = rng.randint(0, 365)
    visit_date = _REFERENCE_DATE - timedelta(days=offset_days)
    return visit_date.strftime("%Y-%m-%d")

def generate_labs_for_visit(rng, conditions, visit_date):
    condition_names = {c.name for c in conditions}
    labs = []
    for lab_name, lab_def in LAB_DEFINITIONS.items():
        value = _generate_lab_value(rng, lab_name, condition_names)
        labs.append(LabResult(lab_name=lab_name, value=value, unit=lab_def["unit"],
                              reference_range=lab_def["reference_range"], date_recorded=visit_date))
    return labs

def generate_visits(rng, patient_seed, conditions, visits_min, visits_max, include_labs):
    visits = []
    num_visits = rng.randint(visits_min, visits_max)
    primary_diagnosis = conditions[0].name if conditions else "routine_check"
    visit_types = ["outpatient", "urgent_care", "telehealth"]
    for j in range(num_visits):
        visit_id = f"V-{patient_seed:08x}-{j+1}"
        visit_date = _generate_visit_date(rng)
        visit_type = rng.choice(visit_types)
        labs = []
        if include_labs:
            labs = generate_labs_for_visit(rng, conditions, visit_date)
        visits.append(Visit(visit_id=visit_id, visit_type=visit_type, visit_date=visit_date,
                            primary_diagnosis=primary_diagnosis, labs=labs))
    return visits
