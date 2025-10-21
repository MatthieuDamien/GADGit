"""
Optimiseur de jobs SLURM basé sur les ressources disponibles.

"""

from typing import List, Dict, Optional
import logging
import re

# pylint: disable=E0401, E0402
from ..database.mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION GPU (doit être identique à collector.py)
# ============================================================================

GPU_CONFIG = {
    'partitions': {
        'gpu': 6,      # 2 GPU H100 par nœud
        'nompi': 0,
        'mpi1': 0,
        'mpi2': 0,
        'transfer': 0,
    },
    'node_patterns': {
        r'cn0-1[8-9]': 4,  # cn0-18, cn0-19
        r'cn0-20': 2,       # cn0-20
    },
    'features': {
        'gpu': 2,  # 2 GPU par nœud avec feature "gpu"
    }
}

# ============================================================================


class JobOptimizer:
    def __init__(self):
        self.db = MongoDBClient()
    
    def get_available_resources(self) -> Dict:
        """Récupère les ressources disponibles depuis le dernier snapshot"""
        snapshot = self.db.cluster_snapshots.find_one(
            sort=[('timestamp', -1)]
        )
        
        if not snapshot:
            logger.warning("Aucun snapshot disponible")
            return {
                'nodes_idle': 0,
                'cpus_idle': 0,
                'gpus_idle': 0,
                'partitions': {}
            }
        
        # MODIFIÉ: Utilisation de la nouvelle structure de métriques
        metrics = snapshot.get('metrics', {})
        nodes_metrics = metrics.get('nodes', {})
        cpus_metrics = metrics.get('cpus', {})
        gpus_metrics = metrics.get('gpus', {})
        
        # Le reste de la fonction qui parse `sinfo` pour les détails par partition
        # peut rester tel quel, car il fournit une vue plus granulaire qui est toujours utile.
        partitions = {}
        # Le nom correct des données brutes est 'sinfo', pas 'raw_data.sinfo' au premier niveau du snapshot
        sinfo_data = snapshot.get('raw_data', {}).get('sinfo', [])

        for node in sinfo_data:
            partition = node.get('PARTITION', 'unknown').strip('*')
            if partition not in partitions:
                partitions[partition] = {
                    'nodes_idle': 0,
                    'cpus_idle': 0,
                    'gpus_idle': 0,
                    'nodes_total': 0
                }
            
            # ... (le reste de la boucle reste identique) ...
            state = node.get('STATE', '').lower()
            cpus = int(node.get('CPUS', 0))
            gpus = self._parse_gpu_count(node)
            
            partitions[partition]['nodes_total'] += 1
            if 'idle' in state:
                # NODES_AIOT: "allocated/idle/other/total"
                try:
                    _, idle_nodes, _, _ = map(int, node.get('NODES_AIOT', '0/0/0/0').split('/'))
                    partitions[partition]['nodes_idle'] += idle_nodes
                    partitions[partition]['cpus_idle'] += cpus * idle_nodes
                    partitions[partition]['gpus_idle'] += gpus * idle_nodes
                except ValueError:
                    continue # Ignore les lignes mal formées
        
        return {
            # MODIFIÉ: Lecture depuis les métriques pré-calculées
            'nodes_idle': nodes_metrics.get('idle', 0),
            'cpus_idle': cpus_metrics.get('idle', 0),
            'gpus_idle': gpus_metrics.get('idle', 0),
            'partitions': partitions
        }
    
    def _parse_gpu_count(self, node: dict) -> int:
        """
        Parse le nombre de GPUs (même logique que collector).
        Gère: gpu:h100:2, gpu:2, gpu:tesla:2, etc.
        """
        # 1. Essayer GRES d'abord
        if 'GRES' in node and node['GRES'] and node['GRES'] != '(null)':
            gres = str(node['GRES'])
            if 'gpu' in gres.lower():
                # Pattern pour gpu:modèle:nombre ou gpu:nombre
                match = re.search(r'gpu:[\w]*:?(\d+)', gres)
                if match:
                    return int(match.group(1))
                # Fallback sur config si juste "gpu" sans nombre
                return self._get_gpu_from_config(node)
        
        # 2. Essayer GPUS directement
        if 'GPUS' in node and node['GPUS']:
            try:
                return int(node['GPUS'])
            except (ValueError, TypeError):
                pass
        
        # 3. Fallback sur configuration
        return self._get_gpu_from_config(node)
    
    def _get_gpu_from_config(self, node: dict) -> int:
        """Configuration GPU manuelle (même logique que collector)"""
        # Par pattern de noeud
        nodelist = node.get('NODELIST', '')
        for pattern, gpu_count in GPU_CONFIG['node_patterns'].items():
            if re.search(pattern, nodelist):
                return gpu_count
        
        # Par partition
        partition = node.get('PARTITION', '')
        if partition in GPU_CONFIG['partitions']:
            return GPU_CONFIG['partitions'][partition]
        
        # Par features
        features = node.get('ACTIVE_FEATURES', '') or node.get('AVAIL_FEATURES', '')
        if features and features != '(null)':
            for feature, gpu_count in GPU_CONFIG['features'].items():
                if feature in features.lower():
                    return gpu_count
        
        return 0
    
    def can_submit_job(self, step: Dict, resources: Dict) -> bool:
        """
        Vérifie si un job peut être soumis avec les ressources disponibles.
        Prend en compte: nodes, CPUs, et GPUs.
        """
        required = step.get('resources', {})
        partition = required.get('partition', 'gpu')
        
        partition_resources = resources.get('partitions', {}).get(partition, {})
        
        # Vérifications
        nodes_needed = required.get('nodes', 1)
        cpus_needed = required.get('cpus', 1)
        gpus_needed = required.get('gpus', 0)
        
        if partition_resources.get('nodes_idle', 0) < nodes_needed:
            logger.debug(f"Pas assez de nodes idle pour {step.get('step_name')}: "
                        f"{partition_resources.get('nodes_idle', 0)} < {nodes_needed}")
            return False
        
        if partition_resources.get('cpus_idle', 0) < cpus_needed:
            logger.debug(f"Pas assez de CPUs idle pour {step.get('step_name')}: "
                        f"{partition_resources.get('cpus_idle', 0)} < {cpus_needed}")
            return False
        
        # Vérification GPU si nécessaire
        if gpus_needed > 0:
            if partition_resources.get('gpus_idle', 0) < gpus_needed:
                logger.debug(f"Pas assez de GPUs idle pour {step.get('step_name')}: "
                            f"{partition_resources.get('gpus_idle', 0)} < {gpus_needed}")
                return False
        
        return True
    
    def select_next_jobs(self, max_jobs: int = 5) -> List[Dict]:
        """
        Sélectionne les prochains jobs à soumettre en fonction:
        - De la priorité
        - Des ressources disponibles (nodes, CPUs, GPUs)
        - Des dépendances
        """
        resources = self.get_available_resources()
        
        logger.info(f"Ressources disponibles: "
                   f"Nodes: {resources['nodes_idle']}, "
                   f"CPUs: {resources['cpus_idle']}, "
                   f"GPUs: {resources['gpus_idle']}")
        
        # Récupérer les jobs en attente, triés par priorité
        pending_jobs = list(
            self.db.job_queue.find({
                'status': 'queued'
            }).sort([
                ('priority_score', -1),
                ('created_at', 1)
            ]).limit(max_jobs * 2)
        )
        
        selected_jobs = []
        
        for job_entry in pending_jobs:
            if len(selected_jobs) >= max_jobs:
                break
            
            # Récupérer les steps du pipeline
            sample_id = job_entry['sample_id']
            
            # CORRIGÉ: Récupérer le résumé de l'analyse directement depuis la collection dédiée.
            analysis_summary = self.db.analysis_summaries.find_one({'analysis_id': sample_id})

            if not analysis_summary:
                logger.warning(f"Aucun résumé trouvé pour l'analyse {sample_id}")
                continue
            
            # Trouver le prochain step à lancer
            next_step = self._find_next_step(analysis_summary['analysis_id'])
            
            if not next_step:
                continue
            
            # Vérifier si on peut le soumettre
            if self.can_submit_job(next_step, resources):
                selected_jobs.append({
                    'analysis_id': analysis_summary['analysis_id'],
                    'sample_id': sample_id,
                    'step': next_step,
                    'priority': job_entry['priority']
                })
                
                logger.info(f"Job sélectionné: {sample_id} - {next_step.get('step_name')}")
                
                # Mettre à jour les ressources "virtuelles" pour éviter over-commit
                self._reserve_resources(next_step, resources)
            else:
                logger.debug(f"Job {sample_id} - {next_step.get('step_name')} ne peut pas être soumis "
                            f"(ressources insuffisantes)")
        
        return selected_jobs
    
    def _find_next_step(self, analysis_id) -> Optional[Dict]:
        """Trouve le prochain step à lancer pour une analyse"""
        # Récupérer tous les steps de l'analyse
        steps = list(
            self.db.pipeline_steps.find({ # 'analysis_id' dans pipeline_steps est le sample_id
                'analysis_id': str(analysis_id)
            }).sort('step_order', 1)
        )
        
        # Trouver le premier step pending dont les dépendances sont satisfaites
        for step in steps:
            if step['status'] != 'pending':
                continue
            
            # Vérifier les dépendances
            if self._dependencies_satisfied(step):
                return step
        
        return None
    
    def _dependencies_satisfied(self, step: Dict) -> bool:
        """Vérifie que toutes les dépendances d'un step sont satisfaites"""
        dependencies = step.get('dependencies', [])
        
        if not dependencies:
            return True
        
        for dep_id in dependencies:
            dep_step = self.db.pipeline_steps.find_one({'_id': dep_id})
            if not dep_step or dep_step['status'] != 'completed':
                return False
        
        return True
    
    def _reserve_resources(self, step: Dict, resources: Dict):
        """Réserve virtuellement des ressources (pour éviter over-commit)"""
        required = step.get('resources', {})
        partition = required.get('partition', 'gpu')
        
        if partition in resources['partitions']:
            resources['partitions'][partition]['nodes_idle'] -= required.get('nodes', 1)
            resources['partitions'][partition]['cpus_idle'] -= required.get('cpus', 1)
            resources['partitions'][partition]['gpus_idle'] -= required.get('gpus', 0)
            
        # Mettre à jour aussi les totaux globaux
        resources['nodes_idle'] -= required.get('nodes', 1)
        resources['cpus_idle'] -= required.get('cpus', 1)
        resources['gpus_idle'] -= required.get('gpus', 0)