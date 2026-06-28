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

"""PSF (Population Sparsity Fairness) axis demo — 7AAST Axis 6."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hipaasynth.core.model_interface import MockClinicalModel, ScoredMockModel
from hipaasynth.psf import PSFAudit, PSFConfig, PSFReport


def _banner(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main() -> None:
    _banner("HipAAsynth — PSF Axis Demo (Population Sparsity Fairness)")

    print("\n[1] Running PSF audit with MockClinicalModel (completeness-based scorer)...")
    config = PSFConfig(n_per_level=50, seed=42)
    result = PSFAudit().run(MockClinicalModel(seed=42), config)

    print(f"\n  SDI  : {result.sdi:.4f}  ({'PASS' if result.sdi_pass else 'FAIL'})")
    print("  Per-level mean scores:")
    for level, score in result.per_level_scores.items():
        print(f"    {level}: {score:.4f}")

    print("\n[2] Full markdown report (MockClinicalModel):\n")
    print(PSFReport(result).to_markdown())

    _banner("ScoredMockModel — Demographic Bias at Sparse Sparsity Levels")

    print("\n[3] Running PSF audit with ScoredMockModel (biased — AIAN penalty)...")
    biased_result = PSFAudit().run(ScoredMockModel(seed=42), PSFConfig(n_per_level=200, seed=42))

    demo_s1 = biased_result.demographic_scores.get("S1", {})
    print("\n  Demographic scores at S1 (most sparse):")
    for group, score in sorted(demo_s1.items(), key=lambda x: x[1]):
        print(f"    {group:<40} {score:.4f}")

    aian = demo_s1.get("American Indian or Alaska Native", float("nan"))
    white = demo_s1.get("White", float("nan"))
    print(f"\n  AIAN  score at S1 : {aian:.4f}")
    print(f"  White score at S1 : {white:.4f}")
    print(f"  Gap               : {white - aian:.4f}  (positive = disparity detected)")

    print("\n[4] Determinism check — running same audit twice with seed=42...")
    r1 = PSFAudit().run(MockClinicalModel(seed=42), PSFConfig(n_per_level=20, seed=42))
    r2 = PSFAudit().run(MockClinicalModel(seed=42), PSFConfig(n_per_level=20, seed=42))
    assert r1.sdi == r2.sdi, "Determinism check FAILED"
    assert r1.per_level_scores == r2.per_level_scores, "Determinism check FAILED"
    print("  Determinism check: PASS (identical SDI and per-level scores)")

    print()


if __name__ == "__main__":
    main()
