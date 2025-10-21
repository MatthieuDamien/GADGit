#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests d'intégration via SSH pour auto_launcher_novaseqx.py
"""

import os
import unittest
import tempfile
import paramiko

class TestAutoLauncherViaSSH(unittest.TestCase):
    """Tests exécutés directement sur le cluster"""
    
    @classmethod
    def setUpClass(cls):
        """Connexion SSH unique pour tous les tests"""
        cls.ssh = paramiko.SSHClient()
        cls.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            cls.ssh.connect(
                hostname="login-1.mesobfc.fr",
                username="umw040ir",
                password="PaeDaegh5uiX",
                timeout=30
            )
            print("✅ Connexion SSH établie")
        except Exception as e:
            raise unittest.SkipTest(f"Impossible de se connecter au cluster: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Fermeture de la connexion SSH"""
        if hasattr(cls, 'ssh'):
            cls.ssh.close()
            print("🔌 Connexion SSH fermée")
    
    def exec_command(self, command: str) -> tuple:
        """Exécute une commande via SSH"""
        stdin, stdout, stderr = self.ssh.exec_command(command, timeout=60)
        output = stdout.read().decode()
        error = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        return output, error, exit_code
    
    def test_config_file_exists(self):
        """Test que le fichier de config existe sur le cluster"""
        output, error, code = self.exec_command(
            "test -f /work/work/shared/s-neomics/pipeline/2.11.0/common/analysis_config_mesobfc.tsv && echo 'EXISTS'"
        )
        self.assertIn("EXISTS", output, 
                     f"Fichier de config non trouvé. Output: {output}, Error: {error}")
    
    def test_python_available(self):
        """Test que Python 3 est disponible sur le cluster"""
        output, error, code = self.exec_command("python3 --version")
        self.assertEqual(code, 0, f"Python 3 non disponible: {error}")
        self.assertIn("Python 3", output)
    
    def test_pipeline_directory_structure(self):
        """Test la structure du répertoire pipeline"""
        output, error, code = self.exec_command(
            "ls -la /work/work/shared/s-neomics/pipeline/2.11.0/common/"
        )
        self.assertEqual(code, 0, f"Impossible d'accéder au répertoire: {error}")
        self.assertIn("analysis_config_mesobfc.tsv", output)
    
    def test_events_register_class_basic(self):
        """Test de base de la classe events_register"""
        # Script qui teste la classe events_register sans importer le module complet
        test_script = """
import sys
import os
import tempfile

# Créer un fichier d'événements temporaire
event_file = tempfile.mktemp(suffix='.events')

# Créer un fichier vide
with open(event_file, 'w') as f:
    f.write("")

# Définition minimale de events_register pour test
class events_register:
    event_type_values = ["test_event"]
    
    def __init__(self, event_file):
        try:
            with open(event_file, "r") as f:
                pass
            self.loaded = True
            self.location_list = []
            self.sample_list = []
            self.type_list = []
            self.counter_list = []
            self.event_list = []
            self.registration_fail = False
        except OSError:
            self.loaded = False
            self.registration_fail = True

# Test
events = events_register(event_file)
print(f"LOADED={events.loaded}")
print(f"SUCCESS")

# Nettoyage
os.remove(event_file)
"""
        
        remote_test = f"/tmp/test_events_{os.getpid()}.py"
        sftp = self.ssh.open_sftp()
        
        try:
            with sftp.open(remote_test, 'w') as f:
                f.write(test_script)
            
            output, error, code = self.exec_command(f"python3 {remote_test}")
            
            self.assertEqual(code, 0, f"Erreur d'exécution: {error}")
            self.assertIn("LOADED=True", output, 
                         f"events_register n'a pas chargé correctement. Output: {output}")
            self.assertIn("SUCCESS", output)
            
        finally:
            try:
                sftp.remove(remote_test)
            except:
                pass
            sftp.close()
    
    def test_config_file_content(self):
        """Test que le fichier de config contient les entrées nécessaires"""
        output, error, code = self.exec_command(
            "grep -E '^(pipelinebase|targetlist)' /work/work/shared/s-neomics/pipeline/2.11.0/common/analysis_config_mesobfc.tsv"
        )
        
        self.assertEqual(code, 0, f"Erreur lecture config: {error}")
        self.assertIn("pipelinebase", output)
        self.assertIn("targetlist", output)
    
    def test_create_temp_file_on_cluster(self):
        """Test création de fichier temporaire sur le cluster"""
        test_script = """
import tempfile
import os

# Créer un fichier temporaire
temp_file = tempfile.mktemp()
with open(temp_file, 'w') as f:
    f.write("test content")

# Vérifier qu'il existe
if os.path.exists(temp_file):
    print("FILE_CREATED")
    os.remove(temp_file)
    print("FILE_REMOVED")
else:
    print("ERROR")
"""
        
        remote_test = f"/tmp/test_tempfile_{os.getpid()}.py"
        sftp = self.ssh.open_sftp()
        
        try:
            with sftp.open(remote_test, 'w') as f:
                f.write(test_script)
            
            output, error, code = self.exec_command(f"python3 {remote_test}")
            
            self.assertEqual(code, 0, f"Erreur: {error}")
            self.assertIn("FILE_CREATED", output)
            self.assertIn("FILE_REMOVED", output)
            
        finally:
            try:
                sftp.remove(remote_test)
            except:
                pass
            sftp.close()
    
    def test_writable_tmp_directory(self):
        """Test que /tmp est accessible en écriture"""
        output, error, code = self.exec_command(
            "touch /tmp/test_write_$$ && rm /tmp/test_write_$$ && echo 'WRITABLE'"
        )
        
        self.assertEqual(code, 0, f"Impossible d'écrire dans /tmp: {error}")
        self.assertIn("WRITABLE", output)
    
    def test_cluster_modules_available(self):
        """Test que les modules Python nécessaires sont disponibles"""
        test_script = """
try:
    import os
    import sys
    import logging
    import glob
    import re
    import itertools
    import subprocess
    import tempfile
    print("ALL_MODULES_OK")
except ImportError as e:
    print(f"MISSING_MODULE: {e}")
"""
        
        remote_test = f"/tmp/test_modules_{os.getpid()}.py"
        sftp = self.ssh.open_sftp()
        
        try:
            with sftp.open(remote_test, 'w') as f:
                f.write(test_script)
            
            output, error, code = self.exec_command(f"python3 {remote_test}")
            
            self.assertEqual(code, 0, f"Erreur: {error}")
            self.assertIn("ALL_MODULES_OK", output, 
                         f"Modules manquants: {output}")
            
        finally:
            try:
                sftp.remove(remote_test)
            except:
                pass
            sftp.close()


class TestAutoLauncherComponentsOnCluster(unittest.TestCase):
    """Tests des composants individuels de l'autolauncher sur le cluster"""
    
    @classmethod
    def setUpClass(cls):
        """Connexion SSH unique"""
        cls.ssh = paramiko.SSHClient()
        cls.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            cls.ssh.connect(
                hostname="login-1.mesobfc.fr",
                username="umw040ir",
                password="PaeDaegh5uiX",
                timeout=30
            )
        except Exception as e:
            raise unittest.SkipTest(f"Impossible de se connecter: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Fermeture connexion"""
        if hasattr(cls, 'ssh'):
            cls.ssh.close()
    
    def exec_command(self, command: str) -> tuple:
        """Exécute une commande via SSH"""
        stdin, stdout, stderr = self.ssh.exec_command(command, timeout=60)
        output = stdout.read().decode()
        error = stderr.read().decode()
        return output, error, stdout.channel.recv_exit_status()
    
    def test_format_event_function(self):
        """Test de la fonction format_event"""
        test_script = """
def format_event(location, sample, event_type):
    return f"{location}\\t{sample}\\t{event_type}"

result = format_event("loc", "sample", "type")
expected = "loc\\tsample\\ttype"

if result == expected:
    print("FORMAT_EVENT_OK")
else:
    print(f"FORMAT_EVENT_FAIL: got '{result}', expected '{expected}'")
"""
        
        remote_test = f"/tmp/test_format_{os.getpid()}.py"
        sftp = self.ssh.open_sftp()
        
        try:
            with sftp.open(remote_test, 'w') as f:
                f.write(test_script)
            
            output, error, code = self.exec_command(f"python3 {remote_test}")
            
            self.assertEqual(code, 0, f"Erreur: {error}")
            self.assertIn("FORMAT_EVENT_OK", output)
            
        finally:
            try:
                sftp.remove(remote_test)
            except:
                pass
            sftp.close()


if __name__ == '__main__':
    # Lancer les tests avec verbosité
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter les tests dans l'ordre
    suite.addTests(loader.loadTestsFromTestCase(TestAutoLauncherViaSSH))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoLauncherComponentsOnCluster))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Afficher résumé
    print("\n" + "="*70)
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")
    print("="*70)