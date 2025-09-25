"""

But du programme : Regrouper les jobs par analyses
Dans exemple on peut voir que pour l'analyse dijnbs10411 a 2 jobs, une dans la queue, une complétée et une en attente.
Nous allons donc créer un disctionnaire avec comme clé le nom du job (ici dijnbs10411) et comme valeur une liste de taches (2 dans l'exemple) avec les infos de chaque tache :
    - JOBID
    - JOBNAME
    - NODELIST
    - NODES
    - PARTITION
    - STATE
    - TIME
    - USER (si dispo)
    - Temps d'execution
    - Temps dans la queue
    - Temps total (queue + execution)


Exemple de sortie .json :{
    'name' : "dijnbs10411"
    'status' : 'running' ou 'pending' ou 'completed' ou 'error' 
        (si au moins un job est en cours, le status est running, 
         sinon si au moins un job est pending, le status est pending,
         sinon si au moins un job est error, le status est error,
         sinon completed)
    'total_time' : '00:20:00'            # temps total de l'analyse (queue + execution)
    'finished_time' : '23:11:32' or null # heure de fin de l'analyse (si terminée)
    'priorite' : 'high'                  # ou 'medium' ou 'low' (en fonction de l'utilisateur)
    'user' : 'ya0902du'                  # utilisateur qui a lancé l'analyse
    'tree' : [
        (Non envoyé pour l'application web, envoyé lors de la sélection d'une analyse)
        'pretraitement' : {
            'status' : 'running'   # ou 'pending' ou 'completed' ou 'error'
            'time' : '00:10:00'    # temps total de l'analyse (queue + execution)
            'tasks' : [
                'copy_pgc1': {
                    "JOBID": "54501",
                    ...
                },
                ...
                'fq2vcf': {
                    "JOBID": "54510",
                    ...
                }
            ]
        }
        'qualite' : {
            status : 'running'
            tasks : [
                'bam_to_cram': {
                    "JOBID": "54511",
                    ...
                },
                ...
                'process_varcall': {
                    "JOBID": "54525",
                    ...
                }
            ]
        }
        'traitementsPeriferiques' : {
            ...
        }
        'snv' : {
            ...
        }
        'cnv' : {
            ...
        }
        'integration' : {
            ...
        }
        ...
    ]
}

"""

import json
from typing import Dict, List, Any
from datetime import datetime, timedelta

from slurmSacct import get_sacct
from slurmQueue import get_squeue


exemple = {
    "squeue": [
        {
        "ALLOCCPUS": "1",
        "ELAPSED": "00:00:12",
        "EXITCODE": "0:0",
        "JOBID": "54501",
        "JOBNAME": "filter_varcall_nbs_dijnbs10411",
        "NNODES": "1",
        "NODELIST": "cn2-1",
        "PARTITION": "nompi",
        "STATE": "COMPLETED"
        }],
    "sacct": [
        {
        "JOBID": "54852",
        "JOBNAME": "run_md5_fastq_dijnbs10411",
        "NODELIST": "(Resources)",
        "NODES": "1",
        "PARTITION": "nompi",
        "STATE": "PD",
        "TIME": "0:00",
        "USER": "ya0902du"
        }
]}


with open('gs_solo_nbs.json', 'r') as file:
    gs_solo_nbs = json.load(file)

print(json.dumps(gs_solo_nbs, indent=4))


def parse_time(time_str: str) -> timedelta:
    # Convertit une chaîne de temps (ex: "00:10:00") en timedelta
    if time_str == "N/A":
        return timedelta(0)
    try:
        h, m, s = map(int, time_str.split(':'))
        return timedelta(hours=h, minutes=m, seconds=s)
    except:
        return timedelta(0)


def regroupeurParAnalyses(ssh) -> Dict[str, Any]:
    # Récupérer les données de squeue et sacct
    squeue_data = get_squeue(ssh)
    sacct_data = get_sacct(ssh)

    # Dictionnaire pour regrouper les jobs par analyse
    analyses: Dict[str, Dict[str, Any]] = {}

    # Parcourir les jobs de squeue et sacct
    for task in squeue_data + sacct_data:
        if 'dijnbs' in task['JOBNAME']:
            # Extraire le nom de l'analyse
            job_name_parts = task['JOBNAME'].split('_')
            analysis_name = job_name_parts[-1]  # Ex: "dijnbs10411"

            # Si l'analyse n'existe pas encore dans le dictionnaire, l'ajouter
            if analysis_name not in analyses:
                analyses[analysis_name] = {
                    'name': analysis_name,
                    'status': 'completed',  # Valeur par défaut
                    'total_time': '00:00:00',
                    'finished_time': None,
                    'priorite': 'medium',  # Par défaut
                    'user': task.get('USER', 'unknown'),
                    'tree': {}
                }

            # Ajouter la tâche à l'analyse
            task_info = {
                'JOBID': task['JOBID'],
                'JOBNAME': task['JOBNAME'],
                'NODELIST': task.get('NODELIST', 'N/A'),
                'NODES': task.get('NODES', 'N/A'),
                'PARTITION': task.get('PARTITION', 'N/A'),
                'STATE': task['STATE'],
                'TIME': task.get('TIME', '00:00:00'),
                'USER': task.get('USER', 'unknown'),
                'temps_execution': '00:00:00',  # À calculer
                'temps_queue': '00:00:00',      # À calculer
                'temps_total': '00:00:00'        # À calculer
            }

            # Mettre à jour le statut de l'analyse
            if task['STATE'] == 'RUNNING':
                analyses[analysis_name]['status'] = 'running'
            elif task['STATE'] == 'PENDING':
                if analyses[analysis_name]['status'] != 'running':
                    analyses[analysis_name]['status'] = 'pending'
            elif task['STATE'] == 'FAILED':
                analyses[analysis_name]['status'] = 'error'

    # Retourner le dictionnaire des analyses
    return analyses

