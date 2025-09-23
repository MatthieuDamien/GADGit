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

def execute_command_safe(ssh, command, timeout=30):
    """
    Exécute une commande SSH de manière sécurisée avec gestion d'erreurs
    """
    if not ssh:
        return None, "Pas de connexion SSH"
    
    try:
        print(f"Exécution de: {command}")
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        
        # Attendre que la commande se termine
        exit_status = stdout.channel.recv_exit_status()
        
        output = stdout.read().decode('utf-8', errors='replace')
        error = stderr.read().decode('utf-8', errors='replace')
        
        if exit_status != 0:
            print(f"⚠️ Commande terminée avec le code de sortie: {exit_status}")
        
        if error:
            print(f"⚠️ Erreur stderr: {error}")
        
        return output, error
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de '{command}': {e}")
        return None, str(e)

# Configuration SSH
USERNAME = "umw040ir"
HOST = "login-1.mesobfc.fr"
PASSWORD = "PaeDaegh5uiX"

# Commandes SLURM
SQUEUE_CMD = "squeue -a --format \"%.18i %.9P %.50j %.8u %.2t %.10M %.6D %R\""
SACCT_CMD = "sacct -a --format JobID,JobName%50,Partition,AllocCPUS,State,ExitCode,Elapsed,NNodes,NTasks,NodeList"
SINFO_CMD = "sinfo -a --format=\"%20P %10a %5D %15F %10T %6c %10m %20f %15l %20b %N\""

def test_connection():
    """Test de connexion et des commandes de base"""
    print("=" * 50)
    print("TEST DE CONNEXION SSH")
    print("=" * 50)
    
    ssh = connect_ssh(HOST, USERNAME, PASSWORD)
    
    if ssh:
        # Test des commandes SLURM
        commands = [
            ("pwd", 10),
            ("ls -la /work/work/shared/s-neomics", 15),
            (SINFO_CMD, 30),
            (SQUEUE_CMD, 30),
            (SACCT_CMD, 45)
        ]
        
        for cmd, timeout in commands:
            print(f"\n--- Test de: {cmd[:50]}... ---")
            output, error = execute_command_safe(ssh, cmd, timeout)
            
            if output:
                lines = output.strip().split('\n')
                print(f"✅ Sortie ({len(lines)} lignes):")
                # Afficher les premières lignes
                for i, line in enumerate(lines[:3]):
                    print(f"  {i+1}: {line}")
                if len(lines) > 3:
                    print(f"  ... et {len(lines) - 3} autres lignes")
            
            if error:
                print(f"❌ Erreur: {error}")
        
        ssh.close()
        print("\n✅ Connexion fermée")
    else:
        print("❌ Impossible d'établir la connexion SSH")

if __name__ == "__main__":
    test_connection()