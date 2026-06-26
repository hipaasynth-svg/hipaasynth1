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

"""
HipAAsynth Oncology Biomarkers Module

Generates site-specific biomarkers with realistic correlations.
No pandas. Fully deterministic via shared RNG.
Uses stdlib random for NixOS compatibility.
"""

import random
import math


class BiomarkerModule:
    def __init__(self, n: int, rng: random.Random):
        self.n = n
        self.rng = rng

    def generate(self, sites, ages, races):
        """
        Args:
            sites (list): cancer site per patient
            ages (list): age per patient
            races (list): race per patient

        Returns:
            dict of biomarker lists
        """
        data = {}

        # Initialize all fields
        data.update(self._empty_fields())

        for i in range(self.n):
            site = sites[i]

            if site == "breast":
                self._breast(i, data, ages[i])

            elif site == "lung":
                self._lung(i, data, races[i])

            elif site == "colon":
                self._colon(i, data)

        return data

    def _empty_fields(self):
        return {
            # Breast
            "er_status": [None] * self.n,
            "pr_status": [None] * self.n,
            "her2_status": [None] * self.n,
            "ki67_percent": [0.0] * self.n,
            "brca_mutation": [None] * self.n,
            "subtype": [None] * self.n,

            # Lung
            "never_smoker": [False] * self.n,
            "egfr_status": [None] * self.n,
            "alk_status": [None] * self.n,
            "ros1_status": [None] * self.n,
            "braf_status": [None] * self.n,
            "kras_status": [None] * self.n,
            "pd_l1_tps": [0] * self.n,
            "histology": [None] * self.n,

            # Colon
            "msi_status": [None] * self.n,
            "nras_status": [None] * self.n,
            "cea_at_dx": [0.0] * self.n,
            "primary_side": [None] * self.n,
        }

    # Utility function for clipping
    @staticmethod
    def _clip(value, low, high):
        return max(low, min(high, value))

    # Utility function for gaussian sampling
    def _gauss(self, mean, std):
        return self.rng.gauss(mean, std)

    # Utility function for lognormal sampling
    def _lognormal(self, mean, std):
        """Sample from lognormal distribution."""
        normal_sample = self.rng.gauss(mean, std)
        return math.exp(normal_sample)

    # Utility function for beta sampling
    def _betavariate(self, alpha, beta):
        return self.rng.betavariate(alpha, beta)

    # Utility function for choice
    def _choice(self, values, probs):
        return self.rng.choices(values, weights=probs, k=1)[0]

    # ---------------- BREAST ----------------

    def _breast(self, i, d, age):
        er = self._choice(["+", "-"], [0.75, 0.25])
        her2 = self._choice(["+", "-"], [0.15, 0.85])

        pr = (
            self._choice(["+", "-"], [0.70, 0.30])
            if er == "+"
            else self._choice(["+", "-"], [0.20, 0.80])
        )

        ki67 = (
            self._gauss(40, 15) if her2 == "+" else self._gauss(20, 12)
        )
        ki67 = self._clip(ki67, 1, 95)

        brca = (
            "positive"
            if self.rng.random() < (0.10 if age < 40 else 0.05)
            else "negative"
        )

        # subtype logic
        if er == "+" and her2 == "-":
            subtype = "Luminal_A" if ki67 < 20 else "Luminal_B"
        elif her2 == "+":
            subtype = "HER2_enriched" if er == "-" else "Luminal_B_HER2"
        else:
            subtype = "Triple_negative"

        d["er_status"][i] = er
        d["pr_status"][i] = pr
        d["her2_status"][i] = her2
        d["ki67_percent"][i] = round(ki67, 1)
        d["brca_mutation"][i] = brca
        d["subtype"][i] = subtype

    # ---------------- LUNG ----------------

    def _lung(self, i, d, race):
        nonsmoke = self.rng.random() < (0.15 if race == "Asian" else 0.10)

        if nonsmoke and race == "Asian":
            egfr_p = 0.40
        elif nonsmoke:
            egfr_p = 0.10
        else:
            egfr_p = 0.05

        egfr = "+" if self.rng.random() < egfr_p else "-"
        alk = "+" if self.rng.random() < (0.10 if nonsmoke else 0.03) else "-"
        ros1 = "+" if self.rng.random() < (0.05 if nonsmoke else 0.01) else "-"
        braf = self._choice(["+", "-"], [0.02, 0.98])

        if egfr == "+" or alk == "+":
            kras = "-"
        else:
            kras = "+" if self.rng.random() < 0.30 else "-"

        pdl1 = int(
            self._clip(
                self._betavariate(2, 8) * 100, 0, 100
            )
        )

        hist = (
            "adenocarcinoma"
            if (nonsmoke or egfr == "+") and self.rng.random() < 0.90
            else "squamous_cell"
        )

        d["never_smoker"][i] = nonsmoke
        d["egfr_status"][i] = egfr
        d["alk_status"][i] = alk
        d["ros1_status"][i] = ros1
        d["braf_status"][i] = braf
        d["kras_status"][i] = kras
        d["pd_l1_tps"][i] = pdl1
        d["histology"][i] = hist

    # ---------------- COLON ----------------

    def _colon(self, i, d):
        right = self.rng.random() < 0.60
        msi = "MSI-H" if self.rng.random() < (0.15 if right else 0.02) else "MSS"

        braf = (
            "+" if self.rng.random() < (0.50 if msi == "MSI-H" else 0.10) else "-"
        )
        kras = (
            "+" if self.rng.random() < (0.20 if msi == "MSI-H" else 0.40) else "-"
        )

        nras = "-" if kras == "+" else ("+" if self.rng.random() < 0.08 else "-")

        her2 = self._choice(["+", "-"], [0.03, 0.97])

        cea = self._clip(self._lognormal(3, 1.5), 0.5, 5000)

        d["msi_status"][i] = msi
        d["braf_status"][i] = braf
        d["kras_status"][i] = kras
        d["nras_status"][i] = nras
        d["her2_status"][i] = her2
        d["cea_at_dx"][i] = round(cea, 1)
        d["primary_side"][i] = "right" if right else "left"
