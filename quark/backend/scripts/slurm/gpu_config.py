#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration GPU du cluster.
Permet de définir manuellement le nombre de GPU par type de nœud
si GRES n'est pas configuré dans SLURM.
"""

# Configuration GPU par partition ou par pattern de nom de noeud
GPU_CONFIG = {
    # Configuration par partition
    'partitions': {
        'gpu': 2,      # La partition 'gpu' a 2 GPU H100 par noeud
        'nompi': 0,    # Pas de GPU
        'mpi1': 0,
        'mpi2': 0,
        'transfer': 0,
    },
    
    # Configuration par pattern de noeud (regex)
    # Si un noeud matche un pattern, utiliser ce nombre de GPU
    'node_patterns': {
        r'cn0-1[8-9]': 2,  # cn0-18, cn0-19 ont 2 GPU H100
        r'cn0-20': 2,       # cn0-20 a 2 GPU H100
        r'cn0-2[1-9]': 2,   # cn0-21 à cn0-29 ont 2 GPU (si ajoutés)
    },
    
    # Configuration par feature
    # Si un noeud a cette feature, appliquer ce nombre de GPU
    'features': {
        'gpu': 2,  # Tout noeud avec feature "gpu" a 2 GPU H100
    }
}


def get_gpu_count_from_config(node_info: dict) -> int:
    """
    Retourne le nombre de GPU pour un noeud basé sur la configuration.
    Priorité: node_patterns > partition > features
    """
    import re
    
    # 1. Vérifier par pattern de nom de noeud
    nodelist = node_info.get('NODELIST', '')
    for pattern, gpu_count in GPU_CONFIG['node_patterns'].items():
        if re.search(pattern, nodelist):
            return gpu_count
    
    # 2. Vérifier par partition
    partition = node_info.get('PARTITION', '')
    if partition in GPU_CONFIG['partitions']:
        return GPU_CONFIG['partitions'][partition]
    
    # 3. Vérifier par features
    features = node_info.get('ACTIVE_FEATURES', '') or node_info.get('AVAIL_FEATURES', '')
    if features and features != '(null)':
        for feature, gpu_count in GPU_CONFIG['features'].items():
            if feature in features.lower():
                return gpu_count
    
    # Aucune configuration trouvée
    return 0


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    # Exemple de noeuds de ton cluster
    test_nodes = [
        {
            "PARTITION": "gpu",
            "NODELIST": "cn0-18",
            "ACTIVE_FEATURES": "zen4,InfiniBand,gpu,",
        },
        {
            "PARTITION": "gpu",
            "NODELIST": "cn0-19",
            "ACTIVE_FEATURES": "zen4,InfiniBand,gpu,",
        },
        {
            "PARTITION": "mpi2",
            "NODELIST": "cn2-3",
            "ACTIVE_FEATURES": "IceLake,InfiniBand",
        },
    ]
    
    print("=" * 80)
    print("TEST CONFIGURATION GPU")
    print("=" * 80)
    
    for node in test_nodes:
        gpu_count = get_gpu_count_from_config(node)
        print(f"\nNoeud: {node['NODELIST']:15} | "
              f"Partition: {node['PARTITION']:10} | "
              f"GPUs: {gpu_count}")
    
    print("\n" + "=" * 80)