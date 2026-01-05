"""
Module pour la gestion des connexions SSH et l'exécution de commandes de base sur un cluster SLURM.
"""
import paramiko

def connect_ssh(host, username, password, timeout=30):
    """
    Connexion SSH avec gestion d'erreurs améliorée
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # print(f"Tentative de connexion à {host} avec l'utilisateur {username}...")
        ssh_client.connect(
            hostname=host,
            username=username,
            password=password,
            timeout=timeout,
            banner_timeout=30,
            auth_timeout=30
        )

        # Test de la connexion avec une commande simple
        _, stdout, stderr = ssh_client.exec_command("whoami", timeout=10)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if error:
            print(f"Avertissement lors du test de connexion: {error}")

        if output == username:
            # print(f"✅ Connexion SSH établie avec succès à {host}")
            return ssh_client
        else:
            # print(f"❌ Test de connexion échoué - utilisateur attendu: {username}, reçu: {output}")
            ssh_client.close()
            return None

    except paramiko.AuthenticationException:
        print("❌ Erreur d'authentification - vérifiez le nom d'utilisateur et le mot de passe")
        return None
    except paramiko.SSHException as ssh_exception:
        print(f"❌ Erreur SSH: {ssh_exception}")
        return None
    except (IOError, TimeoutError) as e:
        print(f"❌ Erreur de connexion: {e}")
        return None

# ------------------------------------------------------------------------------

# Commandes de base à récupérer
SQUEUE_CMD = "squeue -a --format \"%.18i %.9P %.50j %.8u %.2t %.10M %.6D %R\""
SACCT_CMD = ("sacct -a -X --format JobID,JobName%50,Partition,AllocCPUS,State,ExitCode,"
             "Elapsed,NNodes,NodeList,User,Start,End,Submit,Timelimit,WorkDir,ReqMem,MaxRSS")
SINFO_CMD = "sinfo -a --format=\"%20P %10a %5D %15F %10T %6c %10m %20f %15l %20b %N\""

# Si besoin de supprimer un job de la liste
def drop_job_from_queue(job_id_a_supprimer, list_jobs):
    """Supprime un job d'une liste de jobs en se basant sur son JOBID."""
    # Trouver l'index du job avec cet ID
    for i, job in enumerate(list_jobs):
        if job["JOBID"] == job_id_a_supprimer:
            del list_jobs[i]
            break  # Sortir de la boucle après suppression


# Affiche la sortie d'une commande SSH
def exec_sortie_ssh(ssh_client, command):
    """Exécute une commande sur le client SSH et affiche la sortie."""
    _, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode()
    error  = stderr.read().decode()

    if output:
        print(f"\nSortie de la commande {command} :\n{output}")
    if error:
        print(f"Erreur :\n{error}")

# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    # pylint: disable=E0401
    from slurmSacct import get_sacct

    # Configuration SSH pour le test local
    TEST_USERNAME = "umw040ir"
    TEST_HOST = "login-1.mesobfc.fr"
    TEST_PASSWORD = "PaeDaegh5uiX"

    def printer():
        """Fonction de test pour la connexion et les commandes."""
        print("--- Lancement du test pour slurmAccess.py ---")
        ssh_client = connect_ssh(
            host=TEST_HOST,
            username=TEST_USERNAME,
            password=TEST_PASSWORD
        )

        if ssh_client:
            try:
                # exec_sortie_ssh(ssh_client, SINFO_CMD)
                # exec_sortie_ssh(ssh_client, SQUEUE_CMD)
                # exec_sortie_ssh(ssh_client, SACCT_CMD)
                print("\nAppel de get_sacct pour tester le parsing...")
                sacct_jobs = get_sacct(ssh_client)
                if sacct_jobs != "Error" and isinstance(sacct_jobs, list):
                    print(f"✅ {len(sacct_jobs)} jobs récupérés et parsés depuis sacct.")
                    if sacct_jobs:
                        print("\n--- Premier job parsé ---")
                        print(json.dumps(sacct_jobs[0], indent=4, ensure_ascii=False))
            finally:
                ssh_client.close()
                print("Connexion SSH de test fermée.")

    printer()