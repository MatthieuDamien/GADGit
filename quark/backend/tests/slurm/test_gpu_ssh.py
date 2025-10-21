#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test de diagnostic GPU via SSH sur le cluster MesoBFC
Vérifie le parsing GRES et le calcul du total de GPUs
"""

import paramiko
import re
from typing import Dict, List


# ============================================================================
# PARSING FUNCTIONS
# ============================================================================

def parse_gpu_count_from_gres(gres_string: str) -> int:
    """
    Parse le nombre de GPU par nœud depuis la string GRES.
    Supporte les formats: gpu:h100:2, gpu:2, gpu:tesla:4, etc.
    """
    if not gres_string or gres_string == '(null)':
        return 0
    
    if 'gpu' in gres_string.lower():
        # Pattern amélioré pour capturer le dernier nombre après gpu:
        match = re.search(r'gpu:[\w]*:?(\d+)', gres_string)
        if match:
            return int(match.group(1))
    
    return 0


def expand_nodelist(nodelist: str) -> int:
    """
    Compte le nombre de nœuds dans une NODELIST SLURM.
    Exemples:
    - "cn0-[18-20]" → 3 nœuds
    - "cn0-18" → 1 nœud
    - "cn0-[1-3,5,7-9]" → 7 nœuds
    """
    if not nodelist or nodelist == '(null)':
        return 0
    
    # Pattern pour détecter les ranges: [18-20] ou [1-3,5,7-9]
    range_pattern = r'\[([0-9,-]+)\]'
    match = re.search(range_pattern, nodelist)
    
    if not match:
        # Pas de range, c'est un seul nœud
        return 1
    
    # Parse le contenu du range
    range_content = match.group(1)
    total_nodes = 0
    
    for part in range_content.split(','):
        if '-' in part:
            # Range continu: 18-20
            start, end = map(int, part.split('-'))
            total_nodes += (end - start + 1)
        else:
            # Nœud unique: 5
            total_nodes += 1
    
    return total_nodes


def calculate_total_gpus(node_info: Dict) -> int:
    """
    Calcule le nombre total de GPUs pour une entrée sinfo.
    total_gpus = nombre_de_noeuds × gpus_par_noeud
    """
    # Méthode 1: Utiliser GRES
    gpus_per_node = parse_gpu_count_from_gres(node_info.get('GRES', ''))
    
    # Méthode 2: Compter les nœuds depuis NODELIST
    num_nodes = expand_nodelist(node_info.get('NODELIST', ''))
    
    total = num_nodes * gpus_per_node
    
    return total, gpus_per_node, num_nodes #type: ignore


# ============================================================================
# SSH CONNECTION & TESTS
# ============================================================================

def test_cluster_connection():
    """Test de connexion SSH et diagnostic GPU"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("=" * 80)
        print("CONNEXION AU CLUSTER")
        print("=" * 80)
        
        ssh.connect(
            hostname="login-1.mesobfc.fr",
            username="umw040ir",
            password="PaeDaegh5uiX",
            timeout=30
        )
        print("✅ Connexion SSH établie\n")
        
        # ====================================================================
        # TEST 1: Récupérer sinfo
        # ====================================================================
        print("=" * 80)
        print("TEST 1: RÉCUPÉRATION SINFO")
        print("=" * 80)
        
        stdin, stdout, stderr = ssh.exec_command(
            'sinfo -a --format="%20P %10a %5D %15F %10T %6c %10m %20G %20f %15l %20b %N"'
        )
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if error:
            print(f"⚠️  Erreur: {error}")
            return
        
        print("✅ Commande sinfo exécutée\n")
        
        # ====================================================================
        # TEST 2: Parser les infos GPU
        # ====================================================================
        print("=" * 80)
        print("TEST 2: PARSING DES INFORMATIONS GPU")
        print("=" * 80)
        
        lines = output.splitlines()[1:]  # Skip header
        gpu_entries = []
        
        for line in lines:
            parts = line.split(maxsplit=11)
            if len(parts) == 12:
                node_info = {
                    "PARTITION": parts[0],
                    "AVAIL": parts[1],
                    "NODES": parts[2],
                    "NODES_AIOT": parts[3],
                    "STATE": parts[4],
                    "CPUS": parts[5],
                    "MEMORY": parts[6],
                    "GRES": parts[7],
                    "AVAIL_FEATURES": parts[8],
                    "TIMELIMIT": parts[9],
                    "ACTIVE_FEATURES": parts[10],
                    "NODELIST": parts[11]
                }
                
                # Ne garder que les entrées avec GPU
                if 'gpu' in node_info['GRES'].lower():
                    gpu_entries.append(node_info)
        
        if not gpu_entries:
            print("⚠️  Aucune partition GPU trouvée!")
            return
        
        print(f"✅ {len(gpu_entries)} entrée(s) GPU trouvée(s)\n")
        
        # ====================================================================
        # TEST 3: Calcul des GPUs totaux
        # ====================================================================
        print("=" * 80)
        print("TEST 3: CALCUL DES GPUS TOTAUX")
        print("=" * 80)
        
        grand_total_gpus = 0
        
        for i, node_info in enumerate(gpu_entries, 1):
            print(f"\nEntrée #{i}")
            print(f"   Partition:  {node_info['PARTITION']}")
            print(f"   GRES:       {node_info['GRES']}")
            print(f"   NODELIST:   {node_info['NODELIST']}")
            print(f"   STATE:      {node_info['STATE']}")
            
            total_gpus, gpus_per_node, num_nodes = calculate_total_gpus(node_info)   #type: ignore
            
            print(f"\n   Analyse:")
            print(f"      - GPUs par nœud:  {gpus_per_node}")
            print(f"      - Nombre de nœuds: {num_nodes}")
            print(f"      - Total GPUs:      {total_gpus} ({num_nodes} × {gpus_per_node})")
            
            # Seulement compter les GPUs idle ou allocated
            if node_info['STATE'] in ['idle', 'alloc', 'mix']:
                grand_total_gpus += total_gpus
                print(f"      ✅ Comptés dans le total (state={node_info['STATE']})")
            else:
                print(f"      ⚠️  Non comptés (state={node_info['STATE']})")
        
        print("\n" + "=" * 80)
        print("RÉSULTAT FINAL")
        print("=" * 80)
        print(f"🎯 Total GPUs disponibles: {grand_total_gpus}")
        print(f"   (Attendu: 6 GPUs = 3 nœuds × 2 GPUs H100)")
        
        if grand_total_gpus == 6:
            print("\n✅ LE CALCUL EST CORRECT!")
        else:
            print(f"\n⚠️  PROBLÈME: attendu 6, obtenu {grand_total_gpus}")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        ssh.close()
        print("\n🔌 Connexion SSH fermée")


# ============================================================================
# TESTS UNITAIRES DES FONCTIONS
# ============================================================================

def test_parsing_functions():
    """Tests unitaires des fonctions de parsing"""
    
    print("\n" + "=" * 80)
    print("TESTS UNITAIRES")
    print("=" * 80)
    
    # Test 1: parse_gpu_count_from_gres
    print("\n📝 Test parse_gpu_count_from_gres:")
    test_cases_gres = [
        ("gpu:h100:2", 2),
        ("gpu:2", 2),
        ("gpu:tesla:4", 4),
        ("(null)", 0),
        ("", 0),
    ]
    
    for gres, expected in test_cases_gres:
        result = parse_gpu_count_from_gres(gres)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{gres}' → {result} (attendu: {expected})")
    
    # Test 2: expand_nodelist
    print("\n📝 Test expand_nodelist:")
    test_cases_nodelist = [
        ("cn0-[18-20]", 3),
        ("cn0-18", 1),
        ("cn0-[1-3,5,7-9]", 7),
        ("cn0-[1-5]", 5),
        ("(null)", 0),
    ]
    
    for nodelist, expected in test_cases_nodelist:
        result = expand_nodelist(nodelist)
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{nodelist}' → {result} nœuds (attendu: {expected})")
    
    # Test 3: calculate_total_gpus
    print("\n📝 Test calculate_total_gpus:")
    test_node = {
        "PARTITION": "gpu",
        "GRES": "gpu:h100:2",
        "NODELIST": "cn0-[18-20]",
        "STATE": "idle"
    }
    
    total, per_node, num_nodes = calculate_total_gpus(test_node) #type: ignore
    print(f"   Entrée de test: {test_node['GRES']} sur {test_node['NODELIST']}")
    print(f"   → {num_nodes} nœuds × {per_node} GPUs = {total} GPUs total")
    print(f"   {'✅' if total == 6 else '❌'} Attendu: 6 GPUs")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # D'abord les tests unitaires
    test_parsing_functions()
    
    # Puis le test sur le cluster
    print("\n\n")
    test_cluster_connection()