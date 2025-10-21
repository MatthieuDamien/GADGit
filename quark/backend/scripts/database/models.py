"""
Définition des schémas de documents pour la base de données MongoDB.
Chaque fonction retourne un dictionnaire représentant un modèle de document.
"""
from datetime import datetime
from typing import Optional, List, Dict

from requests import get

def create_analysis_document(sample_id: str, user: str, priority: str = 'Medium'):
    """Crée un document de base pour une nouvelle analyse."""
    return {
        'sample_id': sample_id,
        'status': 'pending',  # pending | running | completed | error
        'priority': priority,
        'user_name': user,

        # Timestamps
        'created_at': datetime.utcnow(),
        'started_at': None,
        'finished_at': None,

        # Métriques
        'total_time_seconds': None,
        'queue_time_seconds': None,
        'execution_time_seconds': None,

        # Compteurs
        'total_reloaded': 0,
        'error_count': 0,
        'steps_completed': 0,
        'steps_total': 0,

        # Erreurs
        'last_error_message': None,

        # Ressources
        'node_hours_used': 0.0,

        # LabKey sync
        'labkey_id': None,
        'labkey_sync_time': None,
        'labkey_metadata': {}
    }

def create_pipeline_step_document(
    analysis_id: str,
    step_name: str,
    step_category: str,
    job_id: Optional[int] = None
):
    """Crée un document de base pour une étape de pipeline."""
    return {
        'job_id': job_id,  # ID SLURM
        'analysis_id': analysis_id,

        # Identification
        'step_name': step_name,
        'step_category': step_category,
        'step_order': None,

        # État
        'status': 'pending',
        'exit_code': None,

        # Ressources demandées
        'resources': {
            'partition': 'gpu',
            'nodes': 1,
            'cpus': 8,
            'gpus': 0,  # NOUVEAU: Nombre de GPUs requis (0 si pas besoin)
            'memory_gb': 32,
            'time_limit_hours': 24
        },

        # Ressources utilisées (sera rempli par sacct)
        'resources_used': {
            'nodes': None,
            'node_list': None,
            'cpus': None,
            'memory_mb': None,
            'gpu_used': None
        },

        # Timestamps
        'submitted_at': None,
        'started_at': None,
        'finished_at': None,
        'execution_time_seconds': None,

        # Relances
        'reloaded': 0,
        'max_reload': 3,

        # Erreurs
        'error_message': None,

        # Données SLURM brutes
        'slurm_data': {},

        # Dépendances
        'dependencies': []
    }

def create_cluster_snapshot(sinfo_data: List):
    """Crée un document de snapshot de l'état du cluster."""
    return {
        'timestamp': datetime.utcnow(),
        # Données brutes (optionnel : stocker dans un sous-document ou
        # une collection séparée si volumineux)
        'raw_data': {
            'sinfo': sinfo_data,
            # 'squeue': squeue_data,  # À décommenter si nécessaire
            # 'sacct': sacct_data,
        },
        # Métriques calculées, regroupées par type de ressource
        'metrics': {
            'nodes': {
                'total': 0,
                'idle': 0,
                'allocated': 0,
                'other': 0,
            },
            'jobs': {
                'running': 0,
                'pending': 0,
            },
            'cpus': {
                'total': 0,
                'allocated': 0,
                'idle': 0,
                'other': 0,
            },
            'nompi': {
                'total': 0,
                'allocated': 0,
                'idle': 0,
                'other': 0,
            },
            'mpi2': {
                'total': 0,
                'allocated': 0,
                'idle': 0,
                'other': 0,
            },
            'gpus': {
                'total': 0,
                'allocated': 0,
                'idle': 0,
                'other': 0,
            }
        }
    }

def create_job_queue_entry(
    sample_id: str,):
    """Crée une entrée pour la file d'attente des jobs."""
    priority_scores = {'Low': 1, 'Medium': 2, 'High': 3}

    return {
        'sample_id': sample_id,
        'status': 'queued',  # queued | processing | submitted | failed
        # 'priority': priority,
        # 'priority_score': priority_scores.get(priority, 2),
        'created_at': datetime.utcnow(),
        'attempts': 0,
        'last_attempt_at': None,
        'error_message': None
    }