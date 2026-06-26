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
HipAAsynth Oncology Outcomes Module (stdlib)

Generates:
- response
- progression
- survival
"""

import random
import math


class OutcomesModule:
    def __init__(self, n: int, rng: random.Random):
        self.n = n
        self.rng = rng

    def generate(self, sites, stages, treatments, biomarkers, comorbidity):
        data = self._empty()

        for i in range(self.n):
            stage = stages[i]
            site = sites[i]

            chemo = treatments["chemotherapy"][i]
            targeted = treatments["targeted_therapy"][i]
            io = treatments["immunotherapy"][i]

            egfr = biomarkers.get("egfr_status", [None]*self.n)[i]
            her2 = biomarkers.get("her2_status", [None]*self.n)[i]
            msi = biomarkers.get("msi_status", [None]*self.n)[i]
            pdl1 = biomarkers.get("pd_l1_tps", [0]*self.n)[i]

            cci = comorbidity.get("charlson_index", [0]*self.n)[i]

            # ---------------- RESPONSE ----------------
            response = None
            if chemo or targeted or io:
                if targeted and egfr == "+":
                    prob = 0.75
                elif targeted and her2 == "+":
                    prob = 0.5
                elif io and msi == "MSI-H":
                    prob = 0.5
                elif io and pdl1 >= 50:
                    prob = 0.4
                elif io:
                    prob = 0.2
                elif chemo:
                    prob = 0.35
                else:
                    prob = 0.1

                if self.rng.random() < prob:
                    response = "CR" if self.rng.random() < 0.1 else "PR"
                    data["response_month"][i] = self._randint(2, 6)
                else:
                    response = "SD" if self.rng.random() < 0.4 else "PD"

            data["best_response"][i] = response

            # ---------------- PROGRESSION ----------------
            prog_prob, median_ttp = self._stage_progression(stage)

            if response == "CR":
                prog_prob *= 0.2
                median_ttp *= 3
            elif response == "PR":
                prog_prob *= 0.5
                median_ttp *= 2
            elif response == "PD":
                prog_prob = 1.0
                median_ttp = 2

            if self.rng.random() < prog_prob:
                ttp = self._exp(median_ttp)
                data["progression"][i] = True
                data["progression_month"][i] = min(ttp, 60)
                data["progression_site"][i] = self._progression_site(site)

            # ---------------- SURVIVAL ----------------
            os_5yr, median_os = self._stage_survival(stage)

            if response == "CR":
                median_os *= 2
            elif response == "PR":
                median_os *= 1.5
            elif response == "PD":
                median_os *= 0.6

            median_os *= (0.9 ** cci)

            death = self.rng.random() > os_5yr
            if death:
                ttd = self._weibull(median_os)
                data["death"][i] = True
                data["death_month"][i] = min(ttd, 60)

        return data

    # ---------------- HELPERS ----------------

    def _stage_progression(self, stage):
        if stage == "I":
            return 0.15, 36
        if stage == "II":
            return 0.30, 24
        if stage == "III":
            return 0.50, 18
        return 0.90, 6

    def _stage_survival(self, stage):
        if stage == "I":
            return 0.95, 120
        if stage == "II":
            return 0.85, 96
        if stage == "III":
            return 0.65, 60
        return 0.20, 18

    def _exp(self, mean):
        return -mean * math.log(1 - self.rng.random())

    def _weibull(self, scale):
        shape = 1.5
        return scale * (-math.log(1 - self.rng.random())) ** (1/shape)

    def _randint(self, a, b):
        return a + int(self.rng.random() * (b - a))

    def _progression_site(self, site):
        if site == "breast":
            return self._choice(["bone", "liver", "lung", "brain"])
        if site == "lung":
            return self._choice(["brain", "bone", "liver"])
        return self._choice(["liver", "lung", "peritoneum"])

    def _choice(self, options):
        return options[self.rng.randrange(len(options))]

    def _empty(self):
        return {
            "best_response": [None]*self.n,
            "response_month": [None]*self.n,
            "progression": [False]*self.n,
            "progression_month": [None]*self.n,
            "progression_site": [None]*self.n,
            "death": [False]*self.n,
            "death_month": [None]*self.n,
        }