#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test du parsing GRES avec différents formats
"""

import re


def parse_gpu_count(gres_string):
    """Parse le nombre de GPU depuis GRES"""
    if not gres_string or gres_string == '(null)':
        return 0
    
    if 'gpu' in gres_string.lower():
        # Pattern pour capturer le dernier nombre après gpu:
        match = re.search(r'gpu:[\w]*:?(\d+)', gres_string)
        if match:
            return int(match.group(1))
    
    return 0


# Tests avec différents formats GRES
test_cases = [
    ("gpu:h100:2", 2, "Format avec modèle H100"),
    ("gpu:2", 2, "Format simple"),
    ("gpu:tesla:4", 4, "Format avec modèle Tesla"),
    ("gpu:a100:8", 8, "Format avec modèle A100"),
    ("gpu", 0, "Juste 'gpu' sans nombre"),
    ("(null)", 0, "Null"),
    ("", 0, "Vide"),
    ("gpu:v100:1", 1, "Un seul GPU"),
    ("gpu:rtx3090:3", 3, "RTX 3090"),
]

print("=" * 80)
print("TEST PARSING GRES")
print("=" * 80)

all_passed = True

for gres, expected, description in test_cases:
    result = parse_gpu_count(gres)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    
    if result != expected:
        all_passed = False
    
    print(f"\n{status} | {description}")
    print(f"  GRES: '{gres}'")
    print(f"  Attendu: {expected}, Résultat: {result}")

print("\n" + "=" * 80)
if all_passed:
    print("✓ TOUS LES TESTS SONT PASSÉS")
else:
    print("✗ CERTAINS TESTS ONT ÉCHOUÉ")
print("=" * 80)