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

"""CC (Care Continuity) axis demo — 7AAST Axis 7."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hipaasynth.core.model_interface import MockClinicalModel
from hipaasynth.cc import CCAudit, CCConfig, CCReport, CONTINUITY_PROFILES


def _banner(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main() -> None:
    _banner("HipAAsynth — CC Axis Demo (Care Continuity)")

    print("\n[1] Running CC audit with MockClinicalModel...")
    config = CCConfig(n_per_profile=50, n_matched_pairs=25, seed=42)
    result = CCAudit().run(MockClinicalModel(seed=42), config)

    print(f"\n  CDI  : {result.cdi:.4f}  ({'PASS' if result.cdi_pass else 'FAIL'})")
    print("  Per-profile mean scores:")
    for profile in CONTINUITY_PROFILES:
        score = result.per_profile_scores[profile]
        print(f"    {profile}: {score:.4f}")

    a_score = result.per_profile_scores["PROFILE_A"]
    d_score = result.per_profile_scores["PROFILE_D"]
    print(f"\n  PROFILE_A (full continuity) : {a_score:.4f}")
    print(f"  PROFILE_D (ED-only / no PCP): {d_score:.4f}")
    print(f"  CDI = D/A                   : {d_score/a_score:.4f}")

    print("\n[2] Transition consistency (continuity bias):")
    n = len(result.transition_deltas)
    pos = sum(1 for d in result.transition_deltas if d > 0)
    print(f"  Matched pairs evaluated     : {n}")
    print(f"  Pairs with positive delta   : {pos}/{n} ({100*pos/n:.0f}%)")
    print(f"  Mean delta (A − D)          : {result.mean_transition_delta:.4f}")
    if result.transition_deltas:
        print(f"  Min delta                   : {min(result.transition_deltas):.4f}")
        print(f"  Max delta                   : {max(result.transition_deltas):.4f}")

    print("\n[3] Full markdown report:\n")
    print(CCReport(result).to_markdown())

    print()
    print("[4] Determinism check — running same audit twice with seed=42...")
    r1 = CCAudit().run(MockClinicalModel(seed=42), CCConfig(n_per_profile=20, seed=42))
    r2 = CCAudit().run(MockClinicalModel(seed=42), CCConfig(n_per_profile=20, seed=42))
    assert r1.cdi == r2.cdi, "Determinism check FAILED"
    assert r1.per_profile_scores == r2.per_profile_scores, "Determinism check FAILED"
    print("  Determinism check: PASS (identical CDI and per-profile scores)")

    print()


if __name__ == "__main__":
    main()
