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

"""Anthropometrics generator. All randomness from pipeline-owned rng."""
import random
from hipaasynth.core.schema import Anthropometrics

def _clip(value, lower, upper):
    return min(max(value, lower), upper)

def _bmi_category(bmi):
    if bmi < 18.5: return "underweight"
    if bmi < 25.0: return "normal"
    if bmi < 30.0: return "overweight"
    if bmi < 35.0: return "obesity_class_1"
    if bmi < 40.0: return "obesity_class_2"
    return "obesity_class_3"

def _generate_height_cm(rng, age, sex):
    if sex == "male": value = rng.gauss(176.0, 7.0)
    elif sex == "female": value = rng.gauss(162.0, 7.0)
    else: raise ValueError(f"Unsupported sex: {sex!r}")
    adult_height = round(_clip(value, 140.0, 205.0), 1)
    if age >= 18:
        return adult_height
    # Simple pediatric scaling: newborn ~50 cm, adult height by ~18 y.
    # Keep the same RNG consumption count as the adult branch.
    factor = _clip(0.35 + 0.036 * age, 0.45, 0.97)
    return round(_clip(adult_height * factor, 70.0, adult_height - 1.0), 1)


def _bmi_category_pediatric(bmi):
    # Simplified pediatric categories for engine testing; not clinical growth-chart percentiles.
    if bmi < 14.0: return "underweight"
    if bmi < 22.0: return "normal"
    if bmi < 25.0: return "overweight"
    if bmi < 30.0: return "obesity_class_1"
    return "obesity_class_2"


def _generate_bmi(rng, age, sex):
    if sex == "female": sex_offset = 0.3
    elif sex == "male": sex_offset = 0.0
    else: raise ValueError(f"Unsupported sex: {sex!r}")

    if age < 18:
        # Pediatric BMI mean rises from ~15 at age 1 to ~22 by age 17.
        mean = 15.0 + 0.39 * age + sex_offset
        bmi = round(_clip(rng.gauss(mean, 2.5), 11.0, 35.0), 1)
        return bmi, _bmi_category_pediatric(bmi)

    mean = 29.0
    if age < 25: mean -= 2.0
    elif age >= 65: mean -= 0.5
    mean += sex_offset
    return round(_clip(rng.gauss(mean, 5.0), 15.0, 60.0), 1), None


def generate_anthropometrics(rng, age, sex):
    height_cm = _generate_height_cm(rng, age, sex)
    bmi, pediatric_category = _generate_bmi(rng, age, sex)
    category = pediatric_category if pediatric_category is not None else _bmi_category(bmi)
    height_m = height_cm / 100.0
    weight_kg = round(bmi * (height_m ** 2), 1)
    return Anthropometrics(height_cm=height_cm, weight_kg=weight_kg, bmi=bmi, bmi_category=category)
