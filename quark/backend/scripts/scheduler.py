"""
Module principal du scheduler Quark, responsable de l'orchestration
de la collecte de données, de la mise à jour et de la soumission des jobs SLURM.
"""
import subprocess
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import paramiko  # NOUVEAU: Import pour la gestion SSH

from .database.mongodb_client import MongoDBClient
# MODIFIÉ: Imports des modules
from .slurm.info_collector import SlurmInfoCollector
from .slurm.job_grouper import SlurmJobCollector, JobSeparator
from .slurm.optimizer import JobOptimizer
# NOUVEAU: Imports directs pour le fetch des données
from .slurm.slurmAccess import connect_ssh
from .slurm.slurmInfo import get_sinfo
from .slurm.slurmQueue import get_squeue
from .slurm.slurmSacct import get_sacct

logger = logging.getLogger(__name__)


class QuarkScheduler:
    """
    Schedule les jobs pour soumission sur le cluster
    """
    def __init__(self, host: str, username: str, password: str):
        self.db = MongoDBClient()
        # MODIFIÉ: Les collecteurs n'ont plus besoin d'identifiants
        self.info_collector = SlurmInfoCollector() # Pour les métriques du cluster (sinfo)
        self.job_collector = SlurmJobCollector()   # Pour tous les jobs (squeue, sacct)
        self.job_separator = JobSeparator()        # Pour séparer analyses et jobs uniques
        self.optimizer = JobOptimizer()
        # MODIFIÉ: Le scheduler garde les identifiants
        self.host = host
        self.username = username
        self.password = password

    def _fetch_slurm_data(self) -> tuple[bool, Optional[paramiko.SSHClient],
                                       Optional[List], Optional[List], Optional[List]]:
        """
        Établit la connexion SSH et récupère toutes les données brutes.
        """
        ssh = None
        try:
            logger.info("Connexion SSH à %s...", self.host)
            ssh = connect_ssh(
                host=self.host,
                username=self.username,
                password=self.password
            )
            if not ssh:
                logger.error("Échec de la connexion SSH.")
                return False, None, None, None, None

            logger.info("Collecte des données sinfo, squeue et sacct...")
            sinfo_data = get_sinfo(ssh)
            squeue_data = get_squeue(ssh)
            sacct_data = get_sacct(ssh)

            sinfo_data = sinfo_data if isinstance(sinfo_data, list) else []
            squeue_data = squeue_data if isinstance(squeue_data, list) else []
            sacct_data = sacct_data if isinstance(sacct_data, list) else []

            logger.info("Données collectées: %d sinfo, %d squeue, %d sacct",
                         len(sinfo_data), len(squeue_data), len(sacct_data))

            return True, ssh, sinfo_data, squeue_data, sacct_data

        except paramiko.SSHException as e:
            logger.error("Erreur SSH durant la collecte SLURM: %s", e, exc_info=True)
            if ssh:
                ssh.close()
            return False, None, None, None, None

    def run_cycle(self):
        """
        Cycle d'orchestration centralisé.
        """
        logger.info("=== Début cycle Quark ===")
        ssh_client = None
        try:
            # 1. Collecte des données SLURM (logique centralisée)
            success, ssh_client, sinfo_data, squeue_data, sacct_data = self._fetch_slurm_data()

            if not success or sinfo_data is None or squeue_data is None or sacct_data is None:
                logger.error("Échec collecte SLURM, cycle annulé")
                return False

            # 2. Lancement des processeurs de données
            # 2a. Snapshot de l'état du cluster
            logger.info("Génération du snapshot de l'état du cluster...")
            self.info_collector.process_and_store(sinfo_data, squeue_data)

            # 2b. Stockage du snapshot brut de tous les jobs
            logger.info("Génération du snapshot brut de tous les jobs...")
            self.job_collector.process_and_store(sacct_data, squeue_data)

            # 2c. Séparation et traitement des jobs (analyses vs uniques)
            logger.info("Séparation et traitement des jobs...")
            self.job_separator.process_and_store()

            # 3. Sélection des jobs à soumettre
            logger.info("Sélection des prochains jobs...")
            jobs_to_submit = self.optimizer.select_next_jobs(max_jobs=5)

            logger.info("%d jobs sélectionnés pour soumission", len(jobs_to_submit))

            # 4. Soumission
            if ssh_client:
                for job_info in jobs_to_submit:
                    self._submit_job(job_info, ssh_client)

            logger.info("=== Fin cycle Quark ===")
            return True

        except (paramiko.SSHException, ValueError) as e:
            logger.error("Erreur inattendue dans run_cycle: %s", e, exc_info=True)
            return False
        finally:
            if ssh_client:
                ssh_client.close()
                logger.info("Connexion SSH fermée.")

    def _submit_job(self, job_info: Dict[str, Any], ssh_client: paramiko.SSHClient):
        """MODIFIÉ: Soumet un job SLURM via le client SSH existant."""
        sample_id = job_info['sample_id']
        step = job_info['step']
        logger.info("Soumission job: %s - %s", sample_id, step['step_name'])

        sbatch_cmd = self._build_sbatch_command(step)
        try:
            _, stdout, stderr = ssh_client.exec_command(sbatch_cmd, timeout=30)
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')

            if exit_code != 0:
                raise subprocess.CalledProcessError(
                    exit_code, sbatch_cmd, output=stdout_data, stderr=stderr_data)

            job_id = self._parse_job_id(stdout_data)
            if job_id == 0:
                raise ValueError(f"Impossible de parser le JOBID depuis la sortie: {stdout_data}")

            # Mise à jour MongoDB
            self.db.pipeline_steps.update_one(
                {'_id': step['_id']},
                {'$set': {
                    'job_id': job_id,
                    'status': 'running',
                    'submitted_at': datetime.utcnow()
                }}
            )
            # La mise à jour du statut de l'analyse est maintenant gérée par le snapshotter.
            # Pas besoin de mettre à jour une collection 'analyses' qui n'existe plus.
            logger.info("Job %d soumis avec succès", job_id)

        except subprocess.CalledProcessError as e:
            logger.error("Échec soumission: %s", e.stderr)
            self._handle_submission_error(step, e.stderr)
        except (paramiko.SSHException, ValueError) as e:
            logger.error("Exception soumission: %s", e)
            self._handle_submission_error(step, str(e))

    def _build_sbatch_command(self, step: Dict[str, Any]) -> str:
        """Construit la commande sbatch"""
        resources = step.get('resources', {})
        cmd = (f"sbatch "
               f"--job-name={step['step_name']} "
               f"--partition={resources.get('partition', 'gpu')} "
               f"--nodes={resources.get('nodes', 1)} "
               f"--cpus-per-task={resources.get('cpus', 8)} "
               f"--mem={resources.get('memory_gb', 32)}G "
               f"--time={resources.get('time_limit_hours', 24)}:00:00 "
               f"/path/to/script.sh {step['analysis_id']} {step['step_name']}")
        return cmd

    def _parse_job_id(self, sbatch_output: str) -> int:
        """Parse l'ID du job depuis la sortie de sbatch"""
        match = re.search(r'(\d+)', sbatch_output)
        if match:
            return int(match.group(1))
        return 0

    def _handle_submission_error(self, step: Dict[str, Any], error_msg: str):
        """Gère les erreurs de soumission"""
        self.db.pipeline_steps.update_one(
            {'_id': step['_id']},
            {'$set': {
                'status': 'error',
                'error_message': error_msg
            }}
        )
