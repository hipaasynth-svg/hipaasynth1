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

"""HipAAsynth CLI — Generate synthetic patient cohorts."""
import argparse
import time
from datetime import date
from pathlib import Path
from hipaasynth.core.config import GenerationConfig, DEFAULT_SYNTHETIC_DISCLAIMER, ENGINE_VERSION
from hipaasynth.pipelines.population_pipeline import generate_patients
from hipaasynth.exporters.exporters import (
    export_json, export_csv, export_fhir,
    summary_stats, print_summary, profile_fit_stats, print_profile_fit,
)
from hipaasynth.core.profile_loader import load_population_profile

def build_parser():
    parser = argparse.ArgumentParser(description="Generate synthetic healthcare cohorts")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="output")
    parser.add_argument("--profile", type=str, default=None)
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.demo:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(args.out) / f"demo_{timestamp}"
    else:
        output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "cohort.json"
    csv_path = output_dir / "cohort.csv"
    fhir_path = output_dir / "cohort_fhir.json"
    print("\n" + "=" * 50)
    print(f"HIPAASYNTH ENGINE v{ENGINE_VERSION}")
    print("=" * 50)
    profile_data = None
    if args.profile is not None:
        profile_data = load_population_profile(args.profile)
        print(f"  Profile: {profile_data['profile_name']}")
    print(f"  Patients : {args.count}")
    print(f"  Seed     : {args.seed}")
    print(f"  Output   : {output_dir}/")
    print()
    start_time = time.time()
    cfg = GenerationConfig(
        patient_count=args.count, seed=args.seed,
        age_min=18, age_max=90, required_condition=None,
        sex_ratio_female=profile_data["sex_ratio_female"] if profile_data else 0.5,
        ethnicity_weights=profile_data["ethnicity_weights"] if profile_data else None,
        include_visits=True, include_labs=True, visits_min=1, visits_max=3,
        synthetic_disclaimer=DEFAULT_SYNTHETIC_DISCLAIMER,
        run_date=date.today().isoformat(),
        age_band_weights=profile_data.get("age_band_weights") if profile_data else None,
        population_profile_path=args.profile,
        profile_name=profile_data["profile_name"] if profile_data else None,
    )
    patients = generate_patients(cfg)
    export_json(patients, str(json_path))
    export_csv(patients, str(csv_path))
    export_fhir(patients, str(fhir_path))
    elapsed = round(time.time() - start_time, 2)
    stats = summary_stats(patients)
    print_summary(stats)
    print_profile_fit(profile_fit_stats(patients, cfg))
    print(f"\n  Runtime  : {elapsed}s")
    print(f"  JSON     : {json_path}")
    print(f"  CSV      : {csv_path}")
    print(f"  FHIR     : {fhir_path}")

if __name__ == "__main__":
    main()
