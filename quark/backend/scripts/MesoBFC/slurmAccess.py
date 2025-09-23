import paramiko
import time

def connect_ssh(HOST, USERNAME, PASSWORD, timeout=30):
    """
    Connexion SSH avec gestion d'erreurs améliorée
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Tentative de connexion à {HOST} avec l'utilisateur {USERNAME}...")
        ssh.connect(
            hostname=HOST, 
            username=USERNAME, 
            password=PASSWORD,
            timeout=timeout,
            banner_timeout=30,
            auth_timeout=30
        )
        
        # Test de la connexion avec une commande simple
        stdin, stdout, stderr = ssh.exec_command("whoami", timeout=10)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if error:
            print(f"Avertissement lors du test de connexion: {error}")
        
        if output == USERNAME:
            print(f"✅ Connexion SSH établie avec succès à {HOST}")
            return ssh
        else:
            print(f"❌ Test de connexion échoué - utilisateur attendu: {USERNAME}, reçu: {output}")
            ssh.close()
            return None
            
    except paramiko.AuthenticationException:
        print("❌ Erreur d'authentification - vérifiez le nom d'utilisateur et le mot de passe")
        return None
    except paramiko.SSHException as ssh_exception:
        print(f"❌ Erreur SSH: {ssh_exception}")
        return None
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return None

# ------------------------------------------------------------------------------

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
sacct  = "sacct -a -X --format JobID,JobName%50,Partition,AllocCPUS,State,ExitCode,Elapsed,NNodes,NodeList" #,NTasks mais toujours null
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

# ------------------------------------------------------------------------------

# Test de la connexion et des commandes
def printer():
    connect_ssh_base()
    # print(get_sinfo(ssh))
    # print("\n-------------------\n")
    # print(get_squeue(ssh))
    # print("\n-------------------\n")
    print(get_sacct(ssh)) 
    # exec_sortie_ssh(sinfo)
    # exec_sortie_ssh(squeue)
    # exec_sortie_ssh(sacct)

if __name__ == "__main__":
    printer()