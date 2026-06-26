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
HipAAsynth — Run All Modules
==============================
Single command to generate all three new cohorts and run calibration.

Usage:
    python3 run_all_modules.py

Outputs:
    output/copd_50/         HuggingFace public cohort (n=50)
    output/copd_1000/       Calibration cohort (n=1000)
    output/chf_50/
    output/chf_1000/
    output/oud_50/
    output/oud_1000/
    output/calibration_report.json
"""

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from copd.copd_generator import generate_copd_cohort, save_cohort as save_copd
from chf.chf_generator   import generate_chf_cohort,  save_cohort as save_chf
from oud.oud_generator   import generate_oud_cohort,   save_cohort as save_oud
from calibration_validator import run_all

BASE = os.path.join(os.path.dirname(__file__), "output")

def banner(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def run():
    banner("COPD MODULE — HuggingFace cohort (n=50)")
    pts, anchor = generate_copd_cohort(seed=3001, n=50, label="us_copd_hf_public")
    j, c, m = save_copd(pts, anchor, f"{BASE}/copd_50", "copd_hf_public")
    print(f"  Patients: {len(pts)}")
    print(f"  Anchor:   {anchor[:32]}...")
    print(f"  JSON:     {j}")

    banner("COPD MODULE — Calibration cohort (n=1000)")
    pts, anchor = generate_copd_cohort(seed=3002, n=1000, label="us_copd_calibration")
    j, c, m = save_copd(pts, anchor, f"{BASE}/copd_1000", "copd_calibration")
    print(f"  Patients: {len(pts)} | Anchor: {anchor[:32]}...")

    banner("CHF MODULE — HuggingFace cohort (n=50)")
    pts, anchor = generate_chf_cohort(seed=4001, n=50, label="us_chf_hf_public")
    j, c, m = save_chf(pts, anchor, f"{BASE}/chf_50", "chf_hf_public")
    print(f"  Patients: {len(pts)}")
    print(f"  Anchor:   {anchor[:32]}...")
    print(f"  JSON:     {j}")

    banner("CHF MODULE — Calibration cohort (n=1000)")
    pts, anchor = generate_chf_cohort(seed=4002, n=1000, label="us_chf_calibration")
    j, c, m = save_chf(pts, anchor, f"{BASE}/chf_1000", "chf_calibration")
    print(f"  Patients: {len(pts)} | Anchor: {anchor[:32]}...")

    banner("OUD MODULE — HuggingFace cohort (n=50)")
    pts, anchor = generate_oud_cohort(seed=5001, n=50, label="us_oud_hf_public")
    j, c, m = save_oud(pts, anchor, f"{BASE}/oud_50", "oud_hf_public")
    print(f"  Patients: {len(pts)}")
    print(f"  Anchor:   {anchor[:32]}...")
    print(f"  JSON:     {j}")

    banner("OUD MODULE — Calibration cohort (n=1000)")
    pts, anchor = generate_oud_cohort(seed=5002, n=1000, label="us_oud_calibration")
    j, c, m = save_oud(pts, anchor, f"{BASE}/oud_1000", "oud_calibration")
    print(f"  Patients: {len(pts)} | Anchor: {anchor[:32]}...")

    banner("CALIBRATION VALIDATOR")
    run_all()

    banner("COMPLETE")
    print("  All cohorts generated and calibrated.")
    print(f"  Output directory: {BASE}")
    print()

if __name__ == "__main__":
    run()
