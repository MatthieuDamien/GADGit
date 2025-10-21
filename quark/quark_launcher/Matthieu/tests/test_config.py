#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour config.py - Configuration centralisée de l'autolauncher de Matthieu
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import os
import sys
import tempfile
import shutil
from pathlib import Path

from ..config import Config

# Ajouter le chemin du module parent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))




class TestConfigDefaults(unittest.TestCase):
    """Tests pour les valeurs par défaut de la configuration"""

    def test_default_values(self):
        """Test des valeurs par défaut de la classe Config"""
        self.assertEqual(Config.DEFAULT_LOG_FILE, "autolauncher.log")
        self.assertEqual(Config.DEFAULT_EVENT_FILE, "autolauncher.events")
        self.assertEqual(Config.DEFAULT_MAIL_FILE, "autolauncher_mailing.sh")

    def test_config_constants(self):
        """Test que les constantes sont bien définies"""
        # Vérifier que les constantes existent et sont des chaînes
        self.assertIsInstance(Config.DEFAULT_LOG_FILE, str)
        self.assertIsInstance(Config.DEFAULT_EVENT_FILE, str)
        self.assertIsInstance(Config.DEFAULT_MAIL_FILE, str)

        # Vérifier qu'elles ne sont pas vides
        self.assertGreater(len(Config.DEFAULT_LOG_FILE), 0)
        self.assertGreater(len(Config.DEFAULT_EVENT_FILE), 0)
        self.assertGreater(len(Config.DEFAULT_MAIL_FILE), 0)


class TestConfigInitialization(unittest.TestCase):
    """Tests pour l'initialisation de la configuration"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, "test_config.tsv")

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_with_valid_config_file(self):
        """Test initialisation avec fichier de configuration valide"""
        # Créer un fichier de configuration de test
        config_content = """# Configuration test
pipelinebase	/test/pipeline/path
targetlist	/test/target/list.txt
other_param	some_value
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)

        config = Config(self.config_file)

        # Vérifier les valeurs par défaut
        self.assertEqual(config.config_file, self.config_file)
        self.assertEqual(config.mail_bioinfo, "gad-astreinte-bioinfo@u-bourgogne.fr")
        self.assertEqual(config.labkey_address, "translad.chu-dijon.fr")
        self.assertEqual(config.concat_out_dir, "/work/work/shared/s-neomics/data/incoming/")
        self.assertEqual(config.analysis_out_dir, "/work/work/shared/s-neomics/data/analyse/")

        # Vérifier les valeurs chargées
        self.assertEqual(config.pipeline_base, "/test/pipeline/path")
        self.assertEqual(config.target_list, "/test/target/list.txt")

    def test_init_with_default_config_path(self):
        """Test initialisation sans spécifier de fichier de configuration"""
        # Mock le fichier de configuration par défaut
        config_content = "pipelinebase\t/default/pipeline\ntargetlist\t/default/target\n"

        with patch('builtins.open', mock_open(read_data=config_content)):
            with patch('os.path.isfile', return_value=True):
                config = Config()

                self.assertEqual(config.config_file, "/work/work/shared/s-neomics/pipeline/2.11.0/common/analysis_config_mesobfc.tsv")
                self.assertEqual(config.pipeline_base, "/default/pipeline")
                self.assertEqual(config.target_list, "/default/target")

    def test_init_missing_config_file(self):
        """Test initialisation avec fichier de configuration manquant"""
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.tsv")

        with self.assertRaises(FileNotFoundError) as context:
            Config(nonexistent_file)

        self.assertIn("Fichier de configuration introuvable", str(context.exception))
        self.assertIn(nonexistent_file, str(context.exception))


class TestConfigLoading(unittest.TestCase):
    """Tests pour le chargement de la configuration depuis un fichier"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, "test_config.tsv")

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_load_config_with_all_parameters(self):
        """Test chargement avec tous les paramètres nécessaires"""
        config_content = """pipelinebase	/full/pipeline/path
targetlist	/full/target/list.txt
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)

        config = Config(self.config_file)

        self.assertEqual(config.pipeline_base, "/full/pipeline/path")
        self.assertEqual(config.target_list, "/full/target/list.txt")

    def test_load_config_with_comments_and_empty_lines(self):
        """Test chargement avec commentaires et lignes vides"""
        config_content = """# Ceci est un commentaire

pipelinebase	/pipeline/with/comments
# Autre commentaire
targetlist	/target/with/comments

# Ligne vide au-dessus
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)

        config = Config(self.config_file)

        self.assertEqual(config.pipeline_base, "/pipeline/with/comments")
        self.assertEqual(config.target_list, "/target/with/comments")

    def test_load_config_with_extra_parameters(self):
        """Test chargement avec paramètres supplémentaires"""
        config_content = """pipelinebase	/pipeline/path
targetlist	/target/list.txt
extra_param1	value1
extra_param2	value2
unknown_param	unknown_value
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)

        config = Config(self.config_file)

        # Vérifier que les paramètres connus sont chargés
        self.assertEqual(config.pipeline_base, "/pipeline/path")
        self.assertEqual(config.target_list, "/target/list.txt")

        # Les paramètres inconnus sont ignorés (pas d'erreur)

    def test_load_config_missing_required_parameters(self):
        """Test chargement avec paramètres requis manquants"""
        config_content = """# Fichier de config incomplet
some_other_param	some_value
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)

        config = Config(self.config_file)

        # Les paramètres manquants restent à None
        self.assertIsNone(config.pipeline_base)
        self.assertIsNone(config.target_list)

    def test_load_config_malformed_lines(self):
        """Test chargement avec lignes mal formées"""
        config_content = """pipelinebase	/valid/pipeline/path
ligne_sans_tabulation
targetlist	/valid/target/list.txt
ligne	avec	trop	de	tabulations
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)

        config = Config(self.config_file)

        # Les lignes valides doivent être chargées
        self.assertEqual(config.pipeline_base, "/valid/pipeline/path")
        self.assertEqual(config.target_list, "/valid/target/list.txt")

    def test_load_config_with_whitespace(self):
        """Test chargement avec espaces en début/fin de ligne"""
        config_content = """  pipelinebase	/pipeline/with/spaces
 targetlist	/target/with/spaces
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)

        config = Config(self.config_file)

        # Les espaces doivent être supprimés
        self.assertEqual(config.pipeline_base, "/pipeline/with/spaces")
        self.assertEqual(config.target_list, "/target/with/spaces")

    def test_load_config_duplicate_parameters(self):
        """Test chargement avec paramètres dupliqués"""
        config_content = """pipelinebase	/first/pipeline/path
targetlist	/first/target/list.txt
pipelinebase	/second/pipeline/path
targetlist	/second/target/list.txt
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)

        config = Config(self.config_file)

        # La dernière valeur doit être utilisée
        self.assertEqual(config.pipeline_base, "/second/pipeline/path")
        self.assertEqual(config.target_list, "/second/target/list.txt")


class TestConfigAccessors(unittest.TestCase):
    """Tests pour l'accès aux propriétés de configuration"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, "test_config.tsv")

        # Créer un fichier de configuration de test
        config_content = """pipelinebase	/test/pipeline
targetlist	/test/target.txt
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)

        self.config = Config(self.config_file)

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_all_properties_accessible(self):
        """Test que toutes les propriétés sont accessibles"""
        # Propriétés fixes
        self.assertIsInstance(self.config.mail_bioinfo, str)
        self.assertIsInstance(self.config.labkey_address, str)
        self.assertIsInstance(self.config.concat_out_dir, str)
        self.assertIsInstance(self.config.analysis_out_dir, str)

        # Propriétés chargées depuis le fichier
        self.assertEqual(self.config.pipeline_base, "/test/pipeline")
        self.assertEqual(self.config.target_list, "/test/target.txt")

    def test_fixed_properties_values(self):
        """Test des valeurs des propriétés fixes"""
        self.assertEqual(self.config.mail_bioinfo, "gad-astreinte-bioinfo@u-bourgogne.fr")
        self.assertEqual(self.config.labkey_address, "translad.chu-dijon.fr")
        self.assertEqual(self.config.concat_out_dir, "/work/work/shared/s-neomics/data/incoming/")
        self.assertEqual(self.config.analysis_out_dir, "/work/work/shared/s-neomics/data/analyse/")

    def test_config_immutability(self):
        """Test que les propriétés peuvent être modifiées (pas d'immutabilité forcée)"""
        # La configuration doit être modifiable si nécessaire
        original_mail = self.config.mail_bioinfo
        self.config.mail_bioinfo = "new@example.com"
        self.assertEqual(self.config.mail_bioinfo, "new@example.com")
        self.assertNotEqual(self.config.mail_bioinfo, original_mail)


class TestConfigErrorHandling(unittest.TestCase):
    """Tests pour la gestion d'erreurs dans la configuration"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_permission_denied_error(self):
        """Test gestion d'erreur de permission lors de la lecture"""
        config_file = os.path.join(self.test_dir, "no_permission.tsv")

        # Créer le fichier puis simuler une erreur de permission
        Path(config_file).touch()

        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(PermissionError):
                Config(config_file)

    def test_encoding_error(self):
        """Test gestion d'erreur d'encodage"""
        config_file = os.path.join(self.test_dir, "bad_encoding.tsv")

        # Simuler une erreur d'encodage
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')):
            with self.assertRaises(UnicodeDecodeError):
                Config(config_file)

    @patch('os.path.isfile', return_value=False)
    def test_file_disappeared_during_init(self, mock_isfile):
        """Test quand le fichier disparaît pendant l'initialisation"""
        # Le fichier n'existe pas selon os.path.isfile
        with self.assertRaises(FileNotFoundError):
            Config("/nonexistent/file.tsv")


class TestConfigIntegration(unittest.TestCase):
    """Tests d'intégration pour la configuration"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_real_config_file_format(self):
        """Test avec un format de fichier de configuration réaliste"""
        config_file = os.path.join(self.test_dir, "realistic_config.tsv")
        config_content = """# Configuration pour GAD Pipeline
# Créé le: 2024-01-01
# Auteur: Test

# Chemin de base du pipeline
pipelinebase	/work/work/shared/s-neomics/pipeline/2.11.0

# Liste des cibles pour l'analyse
targetlist	/work/work/shared/s-neomics/pipeline/2.11.0/common/target_lists/exome_v7.bed

# Autres paramètres
reference_genome	/work/work/shared/s-neomics/refs/human/GRCh38
tmp_dir	/tmp/pipeline

# Paramètres avancés
max_memory	64GB
max_threads	16
"""
        with open(config_file, 'w') as f:
            f.write(config_content)

        config = Config(config_file)

        # Vérifier que les paramètres importants sont chargés
        self.assertEqual(config.pipeline_base, "/work/work/shared/s-neomics/pipeline/2.11.0")
        self.assertEqual(config.target_list, "/work/work/shared/s-neomics/pipeline/2.11.0/common/target_lists/exome_v7.bed")

        # Vérifier que les valeurs par défaut sont conservées
        self.assertEqual(config.mail_bioinfo, "gad-astreinte-bioinfo@u-bourgogne.fr")

    def test_config_with_relative_paths(self):
        """Test configuration avec chemins relatifs"""
        config_file = os.path.join(self.test_dir, "relative_config.tsv")
        config_content = """pipelinebase	./relative/pipeline
targetlist	../target/list.txt
"""
        with open(config_file, 'w') as f:
            f.write(config_content)

        config = Config(config_file)

        # Les chemins relatifs doivent être conservés tels quels
        self.assertEqual(config.pipeline_base, "./relative/pipeline")
        self.assertEqual(config.target_list, "../target/list.txt")

    def test_config_multiple_instances(self):
        """Test création de multiples instances de configuration"""
        config_file1 = os.path.join(self.test_dir, "config1.tsv")
        config_file2 = os.path.join(self.test_dir, "config2.tsv")

        with open(config_file1, 'w') as f:
            f.write("pipelinebase\t/config1/pipeline\n")

        with open(config_file2, 'w') as f:
            f.write("pipelinebase\t/config2/pipeline\n")

        config1 = Config(config_file1)
        config2 = Config(config_file2)

        # Chaque instance doit avoir sa propre configuration
        self.assertEqual(config1.pipeline_base, "/config1/pipeline")
        self.assertEqual(config2.pipeline_base, "/config2/pipeline")
        self.assertNotEqual(config1.pipeline_base, config2.pipeline_base)


if __name__ == '__main__':
    unittest.main(verbosity=2)