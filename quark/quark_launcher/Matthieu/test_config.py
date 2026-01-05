#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_config.py

Script de test pour valider que la configuration est correctement chargée.
Vérifie que tous les chemins sont accessibles et absolus.
"""

import sys
import os

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# pylint: disable=E0401
from config import Config


def test_config_loading(config_file):
    """Test le chargement d'un fichier de configuration."""
    print(f"\n{'='*70}")
    print(f"TEST : Chargement de la configuration")
    print(f"Fichier : {config_file}")
    print(f"{'='*70}\n")

    try:
        # Charger la config
        config = Config(config_file)
        print("[OK] Configuration chargée avec succès\n")

        # Afficher la configuration
        print("Configuration chargée :")
        print("-" * 70)
        config_dict = config.to_dict()

        for key, value in config_dict.items():
            if key == 'config_file':
                continue

            # Vérifier si c'est un chemin
            is_path = key.endswith(('_dir', '_list', '_base'))

            if is_path:
                # Vérifier si le chemin est absolu
                is_absolute = os.path.isabs(value)
                abs_marker = "[ABS]" if is_absolute else "[REL]"

                # Vérifier si le chemin existe
                exists = os.path.exists(value)
                exists_marker = "[OK]" if exists else "[NO]"

                print(f"{exists_marker} {key:20s} {abs_marker:6s} : {value}")
            else:
                print(f"  {key:20s}         : {value}")

        print("-" * 70)

        # Vérifier les chemins critiques
        print("\nVérification des chemins :")

        critical_paths = [
            ('concat_out_dir', config.concat_out_dir),
            ('analysis_out_dir', config.analysis_out_dir),
            ('pipeline_base', config.pipeline_base),
            ('target_list', config.target_list),
            ('dev_test_dir', config.dev_test_dir)
        ]

        all_exist = True
        for name, path in critical_paths:
            exists = os.path.exists(path)
            is_absolute = os.path.isabs(path)

            if not is_absolute:
                print(f"  [WARN] {name:20s} : Chemin relatif détecté (devrait être absolu)")
                all_exist = False

            if not exists:
                print(f"  [NO]  {name:20s} : N'existe pas -> {path}")
                all_exist = False
            else:
                print(f"  [OK]  {name:20s} : Existe")

        if all_exist:
            print("\n[OK] Tous les chemins existent et sont valides")
        else:
            print("\n[WARN] Certains chemins n'existent pas (normaux pour les tests locaux)")
            print("   Créez-les avec : mkdir -p <chemin_manquant>")

        # Test de get_script_path
        print("\nTest de get_script_path() :")
        try:
            script_path = config.get_script_path("common/fastq/wrapper_concat_fastq.sh")
            print(f"  [OK] Chemin du script : {script_path}")

            if os.path.isfile(script_path):
                print(f"  [OK] Le script existe")
            else:
                print(f"  [NO] Le script n'existe pas (normal en local)")
        except FileNotFoundError as e:
            print(f"  [NO] Script introuvable : {e}")
        except ValueError as e:
            print(f"  [NO] Erreur de configuration : {e}")

        print("\n" + "="*70)
        print("[OK] TEST REUSSI : Configuration valide")
        print("="*70 + "\n")
        return True

    except FileNotFoundError as e:
        print(f"\n[ERREUR] Fichier de configuration introuvable")
        print(f"  {e}\n")
        return False

    except ValueError as e:
        print(f"\n[ERREUR] Configuration invalide")
        print(f"  {e}\n")
        return False

    except Exception as e:
        print(f"\n[ERREUR] INATTENDUE : {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Point d'entrée principal."""
    print("\n" + "="*70)
    print("    TEST DE CONFIGURATION - Quark Autolauncher")
    print("="*70)

    # Tester les deux fichiers de config
    configs = [
        ("config.csv", "Configuration PRODUCTION (cluster)"),
        ("config_local.csv", "Configuration TEST LOCAL")
    ]

    results = []
    for config_file, description in configs:
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            config_file
        )

        print(f"\n\n{'='*70}")
        print(f" {description}")
        print(f"{'='*70}")

        if not os.path.exists(config_path):
            print(f"\n[WARN] Fichier {config_file} introuvable, ignore")
            results.append((description, None))
            continue

        success = test_config_loading(config_path)
        results.append((description, success))

    # Resume
    print("\n" + "="*70)
    print("RESUME")
    print("="*70)
    for desc, result in results:
        if result is None:
            status = "[SKIP] NON TESTE"
        elif result:
            status = "[PASS]"
        else:
            status = "[FAIL]"
        print(f"{desc:40s} {status}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
