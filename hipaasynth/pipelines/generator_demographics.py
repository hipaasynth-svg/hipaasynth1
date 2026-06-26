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

"""Demographics generator. All randomness from pipeline-owned rng."""
import random
from typing import Optional
from hipaasynth.core.schema import Demographics
from hipaasynth.core.config import DEFAULT_ETHNICITY_WEIGHTS

def _generate_patient_id(patient_seed: int) -> str:
    return f"SYN-{patient_seed:08x}"

def _weighted_choice(rng, options, weights):
    weight_list = [weights.get(opt, 0.0) for opt in options]
    total = sum(weight_list)
    if total == 0: return options[0]
    normalized = [w / total for w in weight_list]
    cumulative = []
    cumsum = 0.0
    for w in normalized:
        cumsum += w
        cumulative.append(cumsum)
    r = rng.random()
    for i, cum in enumerate(cumulative):
        if r <= cum: return options[i]
    return options[-1]

def generate_demographics(rng, patient_seed, age_min, age_max, sex_ratio_female,
                          ethnicity_weights, age_band_weights=None):
    patient_id = _generate_patient_id(patient_seed)
    default_age_bands = [(18, 44, 0.45), (45, 64, 0.33), (65, 80, 0.22)]
    age_bands = age_band_weights if age_band_weights is not None else default_age_bands
    valid_bands = []
    for lo, hi, weight in age_bands:
        clamped_lo = max(lo, age_min)
        clamped_hi = min(hi, age_max)
        if clamped_lo <= clamped_hi:
            valid_bands.append((clamped_lo, clamped_hi, weight))
    r = rng.random()
    if valid_bands:
        total_weight = sum(w for _, _, w in valid_bands)
        cumulative = 0.0
        band_lo, band_hi = valid_bands[0][0], valid_bands[0][1]
        for lo, hi, weight in valid_bands:
            cumulative += weight / total_weight
            if r <= cumulative:
                band_lo, band_hi = lo, hi
                break
    else:
        band_lo, band_hi = age_min, age_max
    age = rng.randint(band_lo, band_hi)
    sex = "female" if rng.random() < sex_ratio_female else "male"
    weights = ethnicity_weights if ethnicity_weights is not None else DEFAULT_ETHNICITY_WEIGHTS
    ethnicity_options = ["white", "black", "hispanic", "asian", "native", "other"]
    ethnicity = _weighted_choice(rng, ethnicity_options, weights)
    return Demographics(patient_id=patient_id, seed=patient_seed, age=age, sex=sex, ethnicity=ethnicity)
