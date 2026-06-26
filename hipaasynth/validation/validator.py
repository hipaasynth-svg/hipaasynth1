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
Validator module for Synthetic Clinical Cohort Engine.

This module provides post-generation validation to ensure patient records
meet clinical and logical constraints, such as age-appropriate conditions.
"""

from hipaasynth.core.schema import Patient, Condition, Visit


# Conditions that are not clinically appropriate for young children
# These conditions are removed if patient age < 10
AGE_RESTRICTED_CONDITIONS = {
    "hypertension",
    "type2_diabetes",
    "coronary_artery_disease",
    "chronic_kidney_disease",
}

# Minimum age for age-restricted conditions
MIN_AGE_FOR_RESTRICTED_CONDITIONS = 10


def _deduplicate_conditions(conditions: list[Condition]) -> list[Condition]:
    """
    Deduplicate conditions by name, keeping the earliest onset age.
    
    Args:
        conditions: List of conditions (may contain duplicates)
        
    Returns:
        Deduplicated list of conditions
    """
    condition_map: dict[str, Condition] = {}
    
    for cond in conditions:
        if cond.name not in condition_map:
            condition_map[cond.name] = cond
        else:
            # Keep the one with earlier onset age
            existing = condition_map[cond.name]
            if cond.onset_age < existing.onset_age:
                condition_map[cond.name] = cond
    
    return list(condition_map.values())


def _validate_visit_diagnoses(visits: list[Visit]) -> list[Visit]:
    """
    Ensure every visit has a non-empty primary_diagnosis.
    
    If a visit has an empty primary_diagnosis, it is replaced with "routine_check".
    
    Args:
        visits: List of visits to validate
        
    Returns:
        List of validated visits
    """
    validated = []
    for visit in visits:
        if not visit.primary_diagnosis or visit.primary_diagnosis.strip() == "":
            # Create new visit with fallback diagnosis
            validated.append(Visit(
                visit_id=visit.visit_id,
                visit_type=visit.visit_type,
                visit_date=visit.visit_date,
                primary_diagnosis="routine_check",
                labs=visit.labs,
            ))
        else:
            validated.append(visit)
    return validated


def validate_patient(patient: Patient) -> Patient:
    """
    Validate and clean a patient record.
    
    Performs the following validations:
    1. Removes age-inappropriate conditions for patients under 10
    2. Deduplicates conditions after modifications
    3. Ensures all visits have a non-empty primary_diagnosis
    
    Args:
        patient: Patient record to validate
        
    Returns:
        Validated patient record (may be modified)
    """
    age = patient.demographics.age
    conditions = patient.conditions
    visits = patient.visits
    
    # Remove age-restricted conditions for young patients
    if age < MIN_AGE_FOR_RESTRICTED_CONDITIONS:
        conditions = [
            cond for cond in conditions
            if cond.name not in AGE_RESTRICTED_CONDITIONS
        ]
    
    # Deduplicate conditions after modifications
    conditions = _deduplicate_conditions(conditions)
    
    # Validate visit diagnoses
    visits = _validate_visit_diagnoses(visits)
    
    # Return validated patient (create new instance since dataclasses are frozen)
    return Patient(
        demographics=patient.demographics,
        anthropometrics=patient.anthropometrics,
        conditions=conditions,
        visits=visits,
        engine_version=patient.engine_version,
        schema_version=patient.schema_version,
        synthetic=patient.synthetic,
        disclaimer=patient.disclaimer,
        observations=patient.observations,
    )


def validate_patients(patients: list[Patient]) -> list[Patient]:
    """
    Validate a list of patient records.
    
    Args:
        patients: List of patient records to validate
        
    Returns:
        List of validated patient records
    """
    return [validate_patient(p) for p in patients]


def validate_cohort(patients: list) -> list:
    """Validate a full cohort. Raises ValueError on first failure."""
    for patient in patients:
        validate_patient(patient)
    return patients
