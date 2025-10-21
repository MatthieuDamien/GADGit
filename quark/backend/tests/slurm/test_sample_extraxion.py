#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour valider l'extraction des sample_id depuis les noms de jobs.
"""

import re


def extract_sample_id(job_name):
    """
    Extrait le sample_id depuis le nom du job.
    """
    if not job_name:
        return None
    
    patterns = [
        r'(djen\d{4,})',
        r'(djex\d{4,})',
        r'(djenbs\d{4,})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, job_name, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    
    return None


def extract_step_name(job_name, sample_id):
    """
    Extrait le nom de l'étape du pipeline.
    """
    if not job_name or not sample_id:
        return job_name
    
    step_name = re.sub(rf"_{sample_id}", "", job_name, flags=re.IGNORECASE)
    step_name = re.sub(rf"{sample_id}", "", step_name, flags=re.IGNORECASE)
    # Original: step_name = job_name.replace(f"_{sample_id}", "").replace(sample_id, "")
    step_name = re.sub(r'_+', '_', step_name).strip('_')
    
    return step_name if step_name else job_name


# Tests
test_cases = [
    "fq2vcf_djen21012",
    "align_djex5432",
    "variant_calling_djenbs1234",
    "preprocessing_DJEN99999",
    "annotation_djex0001",
    "qc_check_djen12345678",
    "djenbsXXXX_postprocessing",
    "random_job_name",
    "djen1234",  # Exactement le sample_id
    "analysis_djen4567_final",
]

print("=" * 80)
print("TEST D'EXTRACTION DES SAMPLE_ID")
print("=" * 80)

for job_name in test_cases:
    sample_id = extract_sample_id(job_name)
    step_name = extract_step_name(job_name, sample_id) if sample_id else None
    
    print(f"\nJob Name: {job_name:40} -> Sample ID: {sample_id or 'None':15} | Step: {step_name or 'N/A'}")

print("\n" + "=" * 80)