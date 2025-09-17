import paramiko

from slurmInfo  import *
from slurmQueue import *
from slurmSacct import *

# Configuration SSH de matt.damien@icloud.com
USERNAME = "umw040ir"
HOST = "login-1.mesobfc.fr"
PASSWORD = "PaeDaegh5uiX"

ssh = paramiko.SSHClient()

# ------------------------------------------------------------------------------

# Commandes de base à récupérer
squeue = "squeue -a --format \"%.18i %.9P %.50j %.8u %.2t %.10M %.6D %R\""
sacct  = "sacct -a --format JobID,JobName%50,Partition,AllocCPUS,State,ExitCode,Elapsed,NNodes,NTasks,NodeList"
sinfo  = "sinfo -a --format=\"%20P %10a %5D %15F %10T %6c %10m %20f %15l %20b %N\""

# Si besoin de supprimer un job de la liste
def drop_job_from_queue(job_id_a_supprimer, list_jobs):
    # Trouver l'index du job avec cet ID
    for i, job in enumerate(list_jobs):
        if job["JOBID"] == job_id_a_supprimer:
            del list_jobs[i]
            break  # Sortir de la boucle après suppression


# Affiche la sortie d'une commande SSH
def exec_sortie_ssh(command):
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    error  = stderr.read().decode()
        
    if output:
        print(f"\nSortie de la commande {command} :\n{output}")
    if error:
        print(f"Erreur :\n{error}")

# ------------------------------------------------------------------------------

# Connexion SSH avec la configuration de matt.damien@icloud.com
def connect_ssh_base():
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USERNAME, password=PASSWORD)
        print(f"Connexion SSH établie avec succès à {HOST} !")
        # ssh.exec_command("cd /work/work/shared/s-neomics && ls")
        exec_sortie_ssh("cd /work/work/shared/s-neomics && ls")
    except Exception as e:
        print(f"Erreur de connexion ou d'exécution : {e}")

# Connexion SSH avec configuration personnalisée
def connect_ssh(HOST, USERNAME, PASSWORD):
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USERNAME, password=PASSWORD)
        print(f"Connexion SSH établie avec succès à {HOST} !")
        # ssh.exec_command("cd /work/work/shared/s-neomics && ls")
        exec_sortie_ssh("cd /work/work/shared/s-neomics && ls")
    except Exception as e:
        print(f"Erreur de connexion ou d'exécution : {e}")


# ------------------------------------------------------------------------------

# Test de la connexion et des commandes
def printer():
    connect_ssh_base()
    # print(get_sinfo(ssh))
    # print("\n-------------------\n")
    # print(get_squeue(ssh))
    # print("\n-------------------\n")
    # print(get_sacct(ssh))
    exec_sortie_ssh(sinfo)
    exec_sortie_ssh(squeue)
    #exec_sortie_ssh(sacct)

# Exemple d'utilisation
printer()
# connect_ssh_base()  # Connexion avec les paramètres par défaut