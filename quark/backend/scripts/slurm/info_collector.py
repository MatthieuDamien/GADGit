#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module pour le traitement des données d'un cluster SLURM.
"""

import logging
import re
from typing import Dict, List, Any

# pylint: disable=E0401, E0402
# MODIFIÉ: On n'importe plus les modules d'accès SLURM
from ..database.mongodb_client import MongoDBClient
from ..database.models import create_cluster_snapshot

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================
PARTITIONS_TO_IGNORE = ['transfer', 'mpi1']
GPU_CONFIG = {
    'partitions': {'gpu': 2, 'nompi': 0, 'mpi1': 0, 'mpi2': 0, 'transfer': 0},
    'node_patterns': {r'cn0-1[8-9]': 2, r'cn0-20': 2},
    'features': {'gpu': 2}
}
# ============================================================================


class SlurmInfoCollector:
    """
    Traite les données d'un cluster SLURM et les stocke dans MongoDB.
    """
    def __init__(self):
        # MODIFIÉ: Le constructeur est simplifié
        self.db = MongoDBClient()

    def process_and_store(self, sinfo_data: List[Dict], squeue_data: List[Dict]) -> bool:
        """
        MODIFIÉ: Orchestre le calcul des métriques et leur stockage.
        Reçoit les données en paramètre.
        """
        try:
            logger.info("Calcul des métriques cluster...")
            metrics = self._calculate_metrics(sinfo_data, squeue_data)

            snapshot = create_cluster_snapshot(sinfo_data)
            snapshot['raw_data']['squeue'] = squeue_data
            snapshot['metrics'] = metrics

            result = self.db.cluster_snapshots.insert_one(snapshot)
            logger.info("Snapshot cluster stocké avec l'ID: %s", result.inserted_id)

            gpu_totals = metrics.get('totals', {}).get('gpus', {})
            logger.info(
                "Métriques GPU - Total: %s, Idle: %s, Allocated: %s",
                gpu_totals.get('total', 0),
                gpu_totals.get('idle', 0),
                gpu_totals.get('allocated', 0)
            )
            return True
        except Exception as e:
            logger.error("Erreur durant le traitement des métriques: %s", e, exc_info=True)
            return False

    def _calculate_metrics(self, sinfo_data: List[Dict], squeue_data: List[Dict]) -> Dict:
        """
        Calcule les métriques globales et par partition de manière dynamique.
        """
        metrics: Dict[str, Any] = {
            'totals': {
                'nodes': {'total': 0, 'allocated': 0, 'idle': 0, 'other': 0},
                'cpus':  {'total': 0, 'allocated': 0, 'idle': 0, 'other': 0},
                'gpus':  {'total': 0, 'allocated': 0, 'idle': 0, 'other': 0}
            },
            'partitions': {},
            'jobs': {'running': 0, 'pending': 0}
        }

        for node_info in sinfo_data:
            try:
                partition = node_info.get('PARTITION', '').strip('*')
                if partition in PARTITIONS_TO_IGNORE:
                    continue
                if partition not in metrics['partitions']:
                    metrics['partitions'][partition] = {
                        'nodes': {'total': 0, 'allocated': 0, 'idle': 0, 'other': 0},
                        'cpus':  {'total': 0, 'allocated': 0, 'idle': 0, 'other': 0},
                        'gpus':  {'total': 0, 'allocated': 0, 'idle': 0, 'other': 0}
                    }

                nodes_aiot = node_info.get('NODES_AIOT', '0/0/0/0')
                allocated, idle, other, total = map(int, nodes_aiot.split('/'))
                cpus_per_node = int(node_info.get('CPUS', 0))
                gpus_per_node = self._parse_gpu_count(node_info)

                part_metrics = metrics['partitions'][partition]
                for key, val in [('total', total), ('idle', idle), ('allocated', allocated), ('other', other)]:
                    part_metrics['nodes'][key] += val
                    part_metrics['cpus'][key] += cpus_per_node * val
                    part_metrics['gpus'][key] += gpus_per_node * val
            except (ValueError, TypeError) as e:
                logger.warning("Impossible de parser la ligne sinfo: %s - %s", node_info, e)

        for part_data in metrics['partitions'].values():
            for res_type in ['nodes', 'cpus', 'gpus']:
                for key in ['total', 'idle', 'allocated', 'other']:
                    metrics['totals'][res_type][key] += part_data[res_type][key]

        for job in squeue_data:
            state = job.get('STATE', '').upper()
            if state in ['RUNNING', 'R']:
                metrics['jobs']['running'] += 1
            elif state in ['PENDING', 'PD']:
                metrics['jobs']['pending'] += 1
        return metrics

    def _parse_gpu_count(self, node: dict) -> int:
        if 'GRES' in node and node['GRES'] and node['GRES'] != '(null)':
            match = re.search(r'gpu:[\w]*:?(\d+)', str(node['GRES']))
            if match:
                return int(match.group(1))
        if 'GPUS' in node and node['GPUS']:
            try:
                return int(node['GPUS'])
            except (ValueError, TypeError):
                pass
        return self._get_gpu_from_config(node)

    def _get_gpu_from_config(self, node: dict) -> int:
        nodelist = node.get('NODELIST', '')
        for pattern, gpu_count in GPU_CONFIG['node_patterns'].items():
            if re.search(pattern, nodelist):
                return gpu_count
        partition = node.get('PARTITION', '')
        if partition in GPU_CONFIG['partitions']:
            return GPU_CONFIG['partitions'][partition]
        features = node.get('ACTIVE_FEATURES', '') or node.get('AVAIL_FEATURES', '')
        if features and features != '(null)':
            for feature, gpu_count in GPU_CONFIG['features'].items():
                if feature in features.lower():
                    return gpu_count
        return 0
