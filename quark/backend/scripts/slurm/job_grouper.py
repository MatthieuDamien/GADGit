#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module pour la collecte et le regroupement des jobs SLURM par analyse.

Ce module se connecte à un nœud de gestion SLURM, récupère les données
de 'squeue' (jobs en cours/en attente) et 'sacct' (jobs terminés),
puis regroupe ces jobs en "analyses" basées sur leur nom (ex: 'dijex12345').

Il calcule ensuite des métriques agrégées pour chaque analyse et stocke
un snapshot complet de l'état des analyses dans MongoDB.

Regroupe les jobs en analyses de manière dynamique en extrayant les IDs d'analyse
depuis les noms de jobs, sans dépendre d'une liste prédéfinie d'analyses.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
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

Error_list = [
    'FAILED', 'F', 'TIMEOUT', 'TO', 'CANCELLED', 'CA', 'NODE_FAIL',
    'OUT OF MEMORY', 'OUT_OF_ME+', 'CANCELLED+'
]

def parse_slurm_time_to_milliseconds(time_str: Optional[str]) -> int:
    """
    Convertit une chaîne de temps SLURM (ex: "1-02:30:00.500") en millisecondes.
    Gère les formats avec jours, heures, minutes, secondes et millisecondes.
    """
    if not time_str or time_str == "N/A":
        return 0
    days = 0
    milliseconds = 0
    if '-' in time_str:
        parts = time_str.split('-', 1)
        try:
            days = int(parts[0])
            time_str = parts[1]
        except ValueError:
            return 0
    if '.' in time_str:
        parts = time_str.split('.', 1)
        try:
            milliseconds = int(parts[1].ljust(3, '0')[:3])
            time_str = parts[0]
        except (ValueError, IndexError):
            milliseconds = 0
    parts = time_str.split(':')
    seconds = 0
    try:
        if len(parts) == 3:
            seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            seconds = int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1 and parts[0]:
            seconds = int(parts[0])
    except (ValueError, TypeError):
        return 0
    return ((days * 86400) + seconds) * 1000 + milliseconds

def parse_slurm_datetime(datetime_str: Optional[str]) -> Optional[datetime]:
    """Parse les formats de date de SLURM (ex: '2023-10-27T10:00:00')."""
    if not datetime_str or datetime_str in ["N/A", "Unknown"]:
        return None
    try:
        return datetime.fromisoformat(datetime_str)
    except (ValueError, TypeError):
        return None

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
        r'(dijex\d+)',
        r'(PED\d+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, job_name, re.IGNORECASE)
        if match:
            return match.group(1).lower()

    return None
# ====================================================================

def extract_step_name(job_name: str, sample_id: Optional[str]) -> str:
    """
    Extrait le nom de l'étape du pipeline depuis le nom du job.
    Exemple: 'fq2vcf_dijen21012' avec sample_id='dijen21012' -> 'fq2vcf'
    """
    if not job_name:
        return ''
    if not sample_id:
        return job_name

    # Retirer le sample_id du job_name (insensible à la casse) et nettoyer
    step_name = re.sub(rf"_{sample_id}|{sample_id}", "", job_name, flags=re.IGNORECASE)
    step_name = re.sub(r'_+', '_', step_name).strip('_')

    return step_name or job_name

def map_slurm_state_to_status(state: str) -> str:
    """Mappe un état SLURM détaillé à un statut simplifié."""
    state_upper = state.upper()
    if state_upper in ['RUNNING', 'R', 'COMPLETING', 'CG']:
        return 'running'
    if state_upper in ['PENDING', 'PD']:
        return 'pending'
    if state_upper == 'COMPLETED':
        return 'completed'
    # Regroupe tous les états d'échec sous 'error'
    return 'error'  # Par défaut, considérer comme erreur

def get_overall_status(statuses: List[str]) -> str:
    """
    Détermine le statut global d'une analyse à partir des statuts de ses jobs.
    La priorité est: running > error > pending > completed.
    """
    if 'running' in statuses:
        return 'running'
    if 'error' in statuses:
        return 'error'
    if 'pending' in statuses:
        return 'pending'
    if statuses and all(s == 'completed' for s in statuses):
        return 'completed'
    return 'error'
# ============================================================================
class SlurmJobCollector:
    """
    Collecte tous les jobs depuis squeue et sacct et les stocke dans un
    snapshot brut dans MongoDB.
    """
    def __init__(self):
        self.db = MongoDBClient()

    def process_and_store(self, sacct_data: List[Dict], squeue_data: List[Dict]) -> bool:
        """
        Fusionne les données de sacct et squeue et insère un snapshot unique.
        Utilise bulk_write pour insérer/mettre à jour chaque job individuellement.
        """
        try:
            logger.info("Traitement de %d jobs (sacct) et %d jobs (squeue)...",
                        len(sacct_data), len(squeue_data))

            operations = []
            all_job_ids = set()
            
            # Fusionner squeue et sacct, squeue a la priorité pour les jobs en cours
            merged_jobs = {job.get('JOBID'): job for job in sacct_data if job.get('JOBID')}
            merged_jobs.update({job.get('JOBID'): job for job in squeue_data if job.get('JOBID')})

            for job_id, job in merged_jobs.items():
                if not job_id:
                    continue
                
                job_name = job.get('JOBNAME', '').strip()
                job['SAMPLE_ID'] = extract_analysis_id(job_name)
                job['STEP_NAME'] = extract_step_name(job_name, job['SAMPLE_ID'])
                job['source'] = 'squeue' if job_id in {j.get('JOBID') for j in squeue_data} else 'sacct'
                job['last_seen'] = datetime.now(timezone.utc)

                operations.append(UpdateOne({'JOBID': job_id}, {'$set': job}, upsert=True))

            if operations:
                self.db.raw_jobs.bulk_write(operations)
                logger.info("%d jobs bruts insérés/mis à jour dans la collection 'raw_jobs'.", len(operations))

            return True

        except pymongo_errors.PyMongoError as e:
            logger.error("Erreur MongoDB durant le stockage du snapshot brut: %s", e, exc_info=True)
            return False


class JobSeparator:
    """
    Sépare les jobs de la collection brute en "analyses" et "jobs uniques",
    calcule les métriques et les stocke dans leurs collections respectives.
    """
    def __init__(self):
        self.db = MongoDBClient()

    def process_and_store(self) -> bool:
        """
        Orchestre la séparation, le calcul et le stockage des analyses et
        des jobs uniques à partir de la collection de jobs bruts.
        """
        try:
            logger.info("Traitement des jobs depuis la collection 'raw_jobs'...")
            all_jobs = list(self.db.raw_jobs.find({}))

            if not all_jobs:
                logger.warning("Aucun job brut à traiter. Le cycle continue.")
                return True

            analyses_docs, unique_jobs = self._separate_jobs(all_jobs)

            # --- AJOUT : Logique pour gérer les relances d'analyses ---
            if analyses_docs:
                existing_analyses = self.db.analysis_summaries.find({
                    'analysis_id': {'$in': list(analyses_docs.keys())},
                    'status': {'$in': ['completed', 'error']}
                })

                finished_analyses = {
                    analysis['analysis_id']: analysis['infos'].get('finished_at')
                    for analysis in existing_analyses
                    if analysis.get('infos', {}).get('finished_at')
                }

                for analysis_id, last_finish_time in finished_analyses.items():
                    if analysis_id in analyses_docs:
                        original_jobs = analyses_docs[analysis_id]['infos']['jobs_list']
                        # Filtrer la jobs_list pour ne garder que les jobs
                        # soumis APRÈS la fin de la dernière analyse
                        new_jobs = [
                            job for job in original_jobs
                            if (submit_time := parse_slurm_datetime(job.get('SUBMIT')))
                            and submit_time > last_finish_time # type: ignore
                        ]

                        # Si la nouvelle liste de jobs est vide, cela signifie qu'il n'y a
                        # pas de nouvelle exécution. On ignore cette mise à jour pour ne pas écraser
                        # l'analyse terminée avec une liste de jobs vide.
                        if not new_jobs:
                            del analyses_docs[analysis_id]
                        else:
                            analyses_docs[analysis_id]['infos']['jobs_list'] = new_jobs

            # --- Mise à jour des résumés d'analyse ---
            if analyses_docs: # analyses_docs peut avoir été modifié
                self._store_analysis_summaries(analyses_docs)

            # --- Stockage des jobs uniques ---
            if unique_jobs:
                self._store_unique_jobs(unique_jobs)

            return True

        except pymongo_errors.PyMongoError as e:
            logger.error("Erreur MongoDB durant la séparation des jobs: %s", e, exc_info=True)
            return False

    def _separate_jobs(self, all_jobs: List[Dict]) -> tuple[Dict[str, Any], List[Dict]]:
        """
        Sépare une liste de jobs en analyses et jobs uniques, et calcule les
        métriques pour les analyses.
        """
        analyses: Dict[str, Any] = {}
        unique_jobs: List[Dict] = []

        for job in all_jobs:
            # MODIFIÉ: Utiliser les champs pré-calculés
            analysis_id = job.get('SAMPLE_ID')

            if not analysis_id:
                unique_jobs.append(job)
                continue

            if analysis_id not in analyses:
                user = job.get('USER', 'unknown')
                analysis_doc = create_analysis_document(sample_id=analysis_id, user=user)
                analysis_doc.update({
                    '_job_statuses': [], 'jobs_total': 0, 'jobs_running': 0,
                    'jobs_pending': 0, 'jobs_completed': 0, 'jobs_error': 0,
                    '_job_starts': [], '_job_ends': [], '_job_submits': [],
                    'jobs_list': []  # Initialiser la liste des jobs
                })
                analyses[analysis_id] = analysis_doc

            analysis = analyses[analysis_id]
            status = map_slurm_state_to_status(job.get('STATE', 'PENDING'))
            analysis['_job_statuses'].append(status)
            analysis['jobs_total'] += 1
            if status in ['running', 'pending', 'completed', 'error']:
                analysis[f'jobs_{status}'] += 1

            if job.get('source') == 'sacct':
                elapsed_str = job.get('ELAPSED')
            else:
                elapsed_str = job.get('TIME')

            if status in ['completed', 'error']:
                elapsed_ms = parse_slurm_time_to_milliseconds(elapsed_str) # type: ignore
                current_exec_time = analysis.get('execution_time_seconds', 0) or 0
                analysis['execution_time_seconds'] = current_exec_time + (elapsed_ms / 1000)
            if 'NODE_HOURS' in job and job.get('NODE_HOURS'):
                try:
                    analysis['node_hours_used'] += float(job['NODE_HOURS'])
                except (ValueError, TypeError):
                    pass

            if start := parse_slurm_datetime(job.get('START')):
                analysis['_job_starts'].append(start)
            if end := parse_slurm_datetime(job.get('END')):
                analysis['_job_ends'].append(end)
            if submit := parse_slurm_datetime(job.get('SUBMIT')):
                analysis['_job_submits'].append(submit)

            # CORRIGÉ: Ajouter l'objet job complet (ou les champs nécessaires) à la liste.
            # Cela évite au frontend d'avoir à faire des jointures complexes.
            analysis['jobs_list'].append(job)

        final_analyses_docs = {}
        for analysis_id, data in analyses.items():
            data['submitted_at'] = min(data.pop('_job_submits')) if data.get('_job_submits') else None
            data['started_at'] = min(data.pop('_job_starts')) if data.get('_job_starts') else None
            data['finished_at'] = max(data.pop('_job_ends')) if data.get('_job_ends') else None

            final_analyses_docs[analysis_id] = {
                'analysis_id': analysis_id,
                'status': get_overall_status(data.pop('_job_statuses', [])),
                'last_update': datetime.now(timezone.utc),
                'infos': data
            }

        return final_analyses_docs, unique_jobs

    def _store_analysis_summaries(self, analyses_docs: Dict[str, Any]):
        """Stocke les résumés d'analyses via une opération bulk upsert."""
        logger.info("Mise à jour de %d résumés d'analyses...", len(analyses_docs))
        operations = [
            UpdateOne(
                {'analysis_id': analysis_id},
                {'$set': data},
                upsert=True
            ) for analysis_id, data in analyses_docs.items()
        ]
        self.db.analysis_summaries.bulk_write(operations)
        logger.info("Résumés d'analyses mis à jour avec succès.")

    def _store_unique_jobs(self, unique_jobs_list: List[Dict]):
        """Stocke les jobs uniques individuellement via une opération bulk upsert."""
        try:
            if not unique_jobs_list:
                logger.info("Aucun job unique à stocker.")
                return

            logger.info("Mise à jour de %d jobs uniques...", len(unique_jobs_list))
            
            # On ne doit jamais inclure le champ `_id` dans une opération `$set`.
            # On crée une copie du job sans ce champ avant de construire l'opération.
            operations = [
                UpdateOne({'JOBID': job['JOBID']}, 
                          {'$set': {k: v for k, v in job.items() if k != '_id'}}, 
                          upsert=True)
                for job in unique_jobs_list if job.get('JOBID')
            ]
            self.db.unique_jobs.bulk_write(operations)
            logger.info("Jobs uniques mis à jour avec succès.")
        except pymongo_errors.PyMongoError as e:
            logger.warning("Erreur lors de la mise à jour des jobs uniques: %s", e)
