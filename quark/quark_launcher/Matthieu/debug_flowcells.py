#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
debug_flowcells.py

Description:
Script de debug pour diagnostiquer pourquoi aucune flowcell n'est trouvée.
Affiche tous les dossiers dans incoming/ et vérifie le pattern de recherche.

Auteur: Matthieu Damien
Creation Date: 2025-11-07
"""

import os
import sys
import glob

def debug_flowcells(input_dir: str):
    """
    Affiche des informations de debug sur la recherche de flowcells.

    Args:
        input_dir: Répertoire à analyser (normalement incoming/)
    """
    print(f"=== DEBUG FLOWCELLS ===")
    print(f"Répertoire analysé: {input_dir}")
    print()

    # Vérifier que le répertoire existe
    if not os.path.isdir(input_dir):
        print(f"❌ ERREUR: Le répertoire n'existe pas!")
        return

    print(f"✅ Le répertoire existe")
    print()

    # Lister TOUS les éléments du répertoire
    print("📁 Contenu complet du répertoire:")
    try:
        all_items = os.listdir(input_dir)
        if not all_items:
            print("  (vide)")
        else:
            for item in sorted(all_items):
                item_path = os.path.join(input_dir, item)
                item_type = "📁" if os.path.isdir(item_path) else "📄"
                print(f"  {item_type} {item}")
    except Exception as e:
        print(f"  ❌ Erreur lors du listage: {e}")
    print()

    # Tester le pattern de recherche utilisé par concat.py
    print("🔍 Recherche avec pattern '2*' (dossiers commençant par '2'):")
    pattern = os.path.join(input_dir, "2*")
    print(f"  Pattern glob: {pattern}")

    matches = glob.glob(pattern)
    print(f"  Résultats bruts de glob.glob(): {len(matches)} match(es)")
    for match in matches:
        print(f"    - {match}")
    print()

    # Filtrer comme le fait concat.py
    print("🔎 Filtrage (comme dans concat.py):")
    flowcells = [
        folder for folder in glob.glob(pattern)
        if os.path.isdir(folder) and not folder.endswith("logs")
    ]

    print(f"  Flowcells après filtrage: {len(flowcells)}")
    if flowcells:
        for fc in flowcells:
            print(f"    ✅ {os.path.basename(fc)}")
    else:
        print("    ❌ Aucune flowcell trouvée!")
    print()

    # Vérifier s'il y a des dossiers qui ne commencent pas par '2'
    print("💡 Autres dossiers (ne commençant PAS par '2'):")
    other_dirs = [
        item for item in os.listdir(input_dir)
        if os.path.isdir(os.path.join(input_dir, item))
        and not item.startswith("2")
        and item != "logs"
    ]

    if other_dirs:
        for d in sorted(other_dirs):
            print(f"    📁 {d}")
    else:
        print("    (aucun)")
    print()

    # Recommandations
    print("📋 Diagnostic:")
    if flowcells:
        print(f"  ✅ {len(flowcells)} flowcell(s) détectée(s)")
        print("  → Le code devrait fonctionner normalement")
    else:
        print("  ❌ Aucune flowcell détectée")
        print()
        print("  Causes possibles:")
        print("  1. Aucun dossier de flowcell présent dans incoming/")
        print("  2. Les flowcells ne commencent pas par '2' (ex: 20250101_...)")
        print("  3. Les flowcells sont dans un sous-répertoire")
        print()
        if other_dirs:
            print(f"  ℹ️  J'ai trouvé {len(other_dirs)} autre(s) dossier(s) qui ne commencent pas par '2'")
            print("     Vérifiez si vos flowcells sont là-dedans")

    print()
    print("=== FIN DEBUG ===")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_flowcells.py <incoming_dir>")
        print()
        print("Exemple:")
        print("  python debug_flowcells.py /work/work/shared/s-neomics/data/sandbox/quark/incoming")
        sys.exit(1)

    input_dir = sys.argv[1]
    debug_flowcells(input_dir)
