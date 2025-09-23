#!/usr/bin/env python3
"""
Test des fonctions SLURM pour déboguer l'API
Fichier à placer dans backend/tests/MesoBFC/
"""

import sys
import os
import traceback
from datetime import datetime

# Ajouter le chemin vers les scripts
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'MesoBFC'))

try:
    from slurmAccess import connect_ssh
    from slurmInfo import get_sinfo
    from slurmQueue import get_squeue
    from slurmSacct import get_sacct
except ImportError as e:
    print(f"Erreur d'import : {e}")
    print("Vérifiez que les fichiers sont dans le bon répertoire")
    sys.exit(1)

def test_ssh_connection():
    """Test de la connexion SSH"""
    print("=" * 50)
    print("TEST 1: Connexion SSH")
    print("=" * 50)
    
    username = "umw040ir"
    host = "login-1.mesobfc.fr"
    password = "PaeDaegh5uiX"
    
    try:
        ssh = connect_ssh(HOST=host, USERNAME=username, PASSWORD=password)
        if ssh:
            print("✅ Connexion SSH réussie")
            # Test d'une commande simple
            stdin, stdout, stderr = ssh.exec_command("whoami")
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if output:
                print(f"✅ Utilisateur connecté: {output}")
            if error:
                print(f"⚠️  Erreur: {error}")
            
            return ssh
        else:
            print("❌ Échec de la connexion SSH")
            return None
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        traceback.print_exc()
        return None

def main():
    """Fonction principale de test"""
    print(f"🧪 Tests SLURM - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Test de connexion
    ssh = test_ssh_connection()
    
    if ssh:
        # Fermer la connexion
        ssh.close()
        print("\n✅ Connexion SSH fermée")
    else:
        print("\n❌ Impossible de continuer les tests sans connexion SSH")
    
    print("\n" + "=" * 70)
    print("🏁 Tests terminés")

if __name__ == "__main__":
    main()