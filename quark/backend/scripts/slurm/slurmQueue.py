"""
Module pour interroger la commande `squeue` de SLURM et parser sa sortie.
"""
import re
import traceback
from logging import getLogger
# pylint: disable=E0401
from .slurmSacct import extract_sample_id, extract_step_name

logger = getLogger(__name__)

def get_squeue(ssh):
    """
    Récupère et parse la sortie de la commande `squeue` via une connexion SSH.
    Args:
        ssh: Un client SSH paramiko connecté.
    Returns:
        Une liste de dictionnaires, chaque dictionnaire représentant un job,
        ou "Error" en cas d'échec.
    """
    list_jobs_squeue = []
    # Commande squeue enrichie pour correspondre aux champs de sacct
    command = ("squeue -a --format=\"%.18i %.50j %.9P %.8u %.2t %.10M %.6D %R "
               "%.11S %.11L %.19V %.10l %C %m\"")
    _, stdout, stderr = ssh.exec_command(command)
    nb_colonnes = 14  # Nombre de colonnes attendues
    output = stdout.read().decode()
    error = stderr.read().decode()
    if error:
        logger.error("Erreur lors de l'exécution de squeue: %s", error)
        return "Error"
    try:
        for line in output.splitlines()[1:]:
            if not line:
                continue
            parts = re.split(r'\s+', line.strip(), maxsplit=nb_colonnes - 1)
            if len(parts) < nb_colonnes:
                continue
            try:
                (job_id, job_name, partition, user, state, time_used, nodes,
                 nodelist, start_time, time_limit, submit_time, time_left,
                 alloc_cpus, req_mem) = parts
                # Extraire le sample_id et le step_name
                sample_id = extract_sample_id(job_name.strip())
                step_name = extract_step_name(job_name.strip(), sample_id) if sample_id else None
                # Calculer les node_hours (à ajuster selon vos besoins)
                node_hours = "0.0000"  # Valeur par défaut, à calculer si nécessaire
                job_data = {
                    "JOBID": job_id.strip(),
                    "JOBNAME": job_name.strip(),
                    "PARTITION": partition.strip(),
                    "ALLOCCPUS": alloc_cpus.strip(),
                    "STATE": state.strip(),
                    "EXITCODE": "0:0",  # Valeur par défaut
                    "ELAPSED": time_used.strip(),
                    "NNODES": nodes.strip(),
                    "NODELIST": nodelist.strip() if nodelist.strip() != "None" else None,
                    "USER": user.strip(),
                    "START": start_time.strip() if start_time.strip() != "N/A" else None,
                    "END": None,  # Valeur par défaut
                    "SUBMIT": submit_time.strip(),
                    "TIMELIMIT": time_limit.strip(),
                    "WORKDIR": None,  # Valeur par défaut, car non disponible dans squeue
                    "REQMEM": req_mem.strip(),
                    "MAXRSS": "",  # Valeur par défaut
                    "SAMPLE_ID": sample_id,
                    "STEP_NAME": step_name,
                    "NODE_HOURS": node_hours,
                    "source": "squeue"  # Source des données
                }
                list_jobs_squeue.append(job_data)
            except ValueError:
                logger.warning("Ligne squeue mal formatée: '%s'", line)
                continue
        return list_jobs_squeue
    except (ValueError, IndexError) as e:
        logger.error("Erreur lors de l'analyse de la sortie (squeue): %s", e)
        traceback.print_exc()
        return "Error"
