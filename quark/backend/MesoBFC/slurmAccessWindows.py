import paramiko

from slurmInfo  import *
from slurmQueue import *
from slurmSacct import *

USERNAME = "umw040ir"
HOST = "login-1.mesobfc.fr"
PASSWORD = "PaeDaegh5uiX"  # À remplacer

ssh = paramiko.SSHClient()

# Commandes de base à récupérer
squeue = "squeue -a --format \"%.18i %.9P %.50j %.8u %.2t %.10M %.6D %R\""
sacct = "sacct -a --format JobID,JobName%50,Partition,AllocCPUS,State,ExitCode,Elapsed,NNodes,NTasks,NodeList"
sinfo = "sinfo -a --format=\"%20P %10a %5D %15F %10T %6c %10m %20f %15l %20b %N\""

def drop_job_from_queue(job_id_a_supprimer, list_jobs): # job à supprimer d'une liste
    # Trouver l'index du job avec cet ID
    for i, job in enumerate(list_jobs):
        if job["JOBID"] == job_id_a_supprimer:
            del list_jobs[i]
            break  # Sortir de la boucle après suppression



def exec_sortie_ssh(command):
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    error  = stderr.read().decode()
        
    if output:
        print(f"\nSortie de la commande {command} :\n{output}")
    if error:
        print(f"Erreur :\n{error}")


def run_ssh_command():
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USERNAME, password=PASSWORD)
        print(f"Connexion SSH établie avec succès à {HOST} !")
        exec_sortie_ssh("cd /work/work/shared/s-neomics && ls")
        # print(get_squeue())
        # exec_sortie_ssh(sacct)
    except Exception as e:
        print(f"Erreur de connexion ou d'exécution : {e}")


# Exemple d'utilisation
run_ssh_command()