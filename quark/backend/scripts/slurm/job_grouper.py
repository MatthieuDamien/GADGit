#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module pour la collecte et le regroupement des jobs SLURM par analyse.

Ce module se connecte à un nœud de gestion SLURM, récupère les données
de 'squeue' (jobs en cours/en attente) et 'sacct' (jobs terminés),
puis regroupe ces jobs en "analyses" basées sur leur nom (ex: 'dijex12345').

Il calcule ensuite des métriques agrégées pour chaque analyse et stocke
un snapshot complet de l'état des analyses dans MongoDB.

Regroupe les jobs en analyses de manière dynamique (si possible).

exemple d'analyse_data renvoyée:
    'djex': {},
    'djen': {},
    'dijenbs': {
        'dijenbs12345': {
            'status': 'running',
            'user': 'ya0902du',
            'percent_complete': 50,
            
            'total_time': 3600,
            'running_time': 1800,
            'queue_time': 1800,
            
            'created_at': datetime,
            'completed_at': datetime,
            
            'priority': 'Medium',
            
            'total_reloads': 0,
            'error_count': 0,
            'last_error_message': '',
            
            'labkey_id': PED12345,
            'labkey_metadata': {...},
            
            'node_hours': 12.5,
            
            'tree_id': 0123456789,
            },
    'total': {
        'analysis': {
            'total': 1,
            'pending': 0,
            'running': 1,
            'completed': 0,
            'error': 0
        },
        'jobs': {
            'total': 40,
            'pending': 10,
            'running': 10,
            'completed': 20,
            'error': 0
        }
    }
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pymongo import UpdateOne
from pymongo import errors as pymongo_errors

# pylint: disable=E0401, E0402

# MODIFIÉ: On n'importe plus les modules d'accès SLURM
from ..database.mongodb_client import MongoDBClient
from ..database.models import create_analysis_document

logger = logging.getLogger(__name__)
# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def parse_slurm_time_to_milliseconds(time_str: Optional[str]) -> int:
    if not time_str or time_str == "N/A":
        return 0
    days = 0
    milliseconds = 0
    if '-' in time_str:
        parts = time_str.split('-', 1)
        try:
            days = int(parts[0])
            time_str = parts[1]
        except ValueError: return 0
    if '.' in time_str:
        parts = time_str.split('.', 1)
        try:
            milliseconds = int(parts[1].ljust(3, '0')[:3])
            time_str = parts[0]
        except (ValueError, IndexError): milliseconds = 0
    parts = time_str.split(':')
    seconds = 0
    try:
        if len(parts) == 3: seconds = int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
        elif len(parts) == 2: seconds = int(parts[0])*60 + int(parts[1])
        elif len(parts) == 1 and parts[0]: seconds = int(parts[0])
    except (ValueError, TypeError): return 0
    return ((days * 86400) + seconds) * 1000 + milliseconds

# ====================================================================
# MODIFICATION PRINCIPALE CI-DESSOUS
# ====================================================================
def extract_analysis_id(job_name: str) -> Optional[str]:
    """
    Extrait l'ID d'analyse (ex: 'dijen1854', 'PED13065') du nom du job.
    Cherche des patterns connus n'importe où dans le nom du job.
    """
    if not job_name:
        return None

    # Patterns à chercher, de plus spécifique à plus général.
    patterns = [
        r'(dijnbs\d+)',
        r'(dijen\d+)',  # CORRIGÉ: "djen" est devenu "dijen"
        r'(djex\d+)',
        r'(PED\d+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, job_name, re.IGNORECASE)
        if match:
            return match.group(1).lower()
            
    return None
# ====================================================================

def map_slurm_state_to_status(state: str) -> str:
    state_upper = state.upper()
    if state_upper in ['RUNNING', 'R', 'COMPLETING', 'CG']: return 'running'
    if state_upper in ['PENDING', 'PD']: return 'pending'
    if state_upper == 'COMPLETED': return 'completed'
    if state_upper in ['FAILED', 'F', 'TIMEOUT', 'TO', 'CANCELLED', 'CA', 'NODE_FAIL']: return 'error'
    return 'pending'

def get_overall_status(statuses: List[str]) -> str:
    if 'running' in statuses: return 'running'
    if 'pending' in statuses: return 'pending'
    if 'error' in statuses: return 'error'
    if statuses and all(s == 'completed' for s in statuses): return 'completed'
    return 'pending'
# ============================================================================

class SlurmAnalysisCollector:
    """
    Regroupe les données de jobs SLURM par analyse et stocke les métriques.
    """
    def __init__(self):
        self.db = MongoDBClient()

    def process_and_store(self, sacct_data: List[Dict], squeue_data: List[Dict]) -> bool:
        """
        Orchestre le regroupement et la mise à jour de chaque analyse
        individuellement dans la base de données.
        """
        try:
            logger.info("Regroupement des analyses...")
            analyses_to_update, utility_jobs = self._analysis_grouping(sacct_data, squeue_data)

            # --- Mise à jour des analyses ---
            if analyses_to_update:
                logger.info("Mise à jour de %d analyses dans la base de données...", len(analyses_to_update))
                operations = []
                for analysis_id, data in analyses_to_update.items():
                    # Crée une opération "update-or-insert" (upsert)
                    operations.append(
                        UpdateOne(
                            {'analysis_id': analysis_id}, # Le filtre pour trouver le document
                            {'$set': data},              # Les données à mettre à jour
                            upsert=True                  # Crée le document s'il n'existe pas
                        )
                    )
                # Exécute toutes les opérations en une seule fois
                self.db.analysis_summaries.bulk_write(operations)
                logger.info("Analyses mises à jour avec succès.")

            # --- Stockage des jobs utilitaires  ---
            if utility_jobs:
                try:
                    logger.info("Création du snapshot pour %d jobs utilitaires...", len(utility_jobs))
                    jobs_dict = { job.get('JOBID'): job for job in utility_jobs if job.get('JOBID') }
                    s_count = sum(1 for j in utility_jobs if j.get('source') == 'squeue')
                    utility_snapshot = {
                        'timestamp': datetime.utcnow(), 'jobs': jobs_dict,
                        'raw_data': {'squeue_count': s_count, 'sacct_count': len(jobs_dict) - s_count, 'total_jobs': len(jobs_dict) }
                    }
                    self.db.utility_job_snapshots.insert_one(utility_snapshot)
                    logger.info("Snapshot des jobs utilitaires stocké avec succès.")
                except pymongo_errors.PyMongoError as e:
                    logger.warning("Erreur lors de l'insertion du snapshot des jobs utilitaires: %s", e)
            
            return True

        except pymongo_errors.PyMongoError as e:
            logger.error("Erreur MongoDB durant le process_and_store: %s", e, exc_info=True)
            return False

    def _analysis_grouping(self, sacct_data: List[Dict], squeue_data: List[Dict]) -> tuple[Dict[str, Any], List[Dict]]:
        """
        Calcule les métriques pour chaque analyse et les retourne.
        Sépare les analyses des jobs utilitaires.
        """
        analyses: Dict[str, Any] = {}
        utility_jobs: List[Dict] = []
        all_jobs: Dict[str, Dict] = {}

        for job in sacct_data:
            if job_id := job.get('JOBID'):
                job['source'] = 'sacct'; all_jobs[job_id] = job
        for job in squeue_data:
            if job_id := job.get('JOBID'):
                job['source'] = 'squeue'; all_jobs[job_id] = job

        for job in all_jobs.values():
            if not (job_name := (job.get('JOBNAME') or job.get('JOB_NAME'))):
                continue
            if not (analysis_id := extract_analysis_id(job_name)):
                utility_jobs.append(job)
                continue

            if analysis_id not in analyses:
                user = job.get('USER', 'unknown')
                analysis_doc = create_analysis_document(sample_id=analysis_id, user=user)
                analysis_doc.update({
                    '_job_statuses': [], 'jobs_total': 0, 'jobs_running': 0,
                    'jobs_pending': 0, 'jobs_completed': 0, 'jobs_error': 0
                })
                analyses[analysis_id] = analysis_doc
            
            analysis = analyses[analysis_id]
            status = map_slurm_state_to_status(job.get('STATE', 'PENDING'))
            analysis['_job_statuses'].append(status)
            analysis['jobs_total'] += 1
            if status in ['running', 'pending', 'completed', 'error']:
                analysis[f'jobs_{status}'] += 1
            
            elapsed_str = job.get('ELAPSED') if job.get('source') == 'sacct' else job.get('TIME')
            if status in ['completed', 'error']:
                elapsed_ms = parse_slurm_time_to_milliseconds(elapsed_str)
                analysis['execution_time_seconds'] = (analysis.get('execution_time_seconds') or 0) + (elapsed_ms / 1000)
            if 'NODE_HOURS' in job and job.get('NODE_HOURS'):
                try: analysis['node_hours_used'] += float(job['NODE_HOURS'])
                except (ValueError, TypeError): pass

        # Passe finale pour formater chaque document d'analyse
        final_analyses_docs = {}
        for analysis_id, data in analyses.items():
            data.pop('status', None)  # Supprime le statut redondant avant de créer le sous-document
            final_doc = {
                'analysis_id': analysis_id,
                'status': get_overall_status(data.pop('_job_statuses', [])),
                'last_update': datetime.utcnow(),
                'infos': data # Le reste des données est dans le sous-document 'infos'
            }
            final_analyses_docs[analysis_id] = final_doc
            
        return final_analyses_docs, utility_jobs
