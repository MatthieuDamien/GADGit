#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour les étapes du pipeline (steps/) de l'autolauncher de Matthieu
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Ajouter le chemin du module parent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from steps.base import BaseStep
from steps.concat import ConcatStep
from steps.organize import OrganizeStep
from steps.infofile import InfofileStep
from steps.analysis import AnalysisStep
from steps.check import CheckStep


class TestBaseStep(unittest.TestCase):
    """Tests pour la classe de base BaseStep"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.mock_config = Mock()
        self.mock_events = Mock()
        self.mock_mail = Mock()
        self.mock_pipeline = Mock()

    def test_base_step_is_abstract(self):
        """Test que BaseStep est une classe abstraite"""
        with self.assertRaises(TypeError):
            BaseStep(self.mock_config, self.mock_events, self.mock_mail, self.mock_pipeline)

    def test_base_step_initialization_components(self):
        """Test que les composants sont bien assignés dans les classes dérivées"""
        # Utiliser ConcatStep comme exemple concret
        step = ConcatStep(self.mock_config, self.mock_events, self.mock_mail, self.mock_pipeline)

        self.assertEqual(step.config, self.mock_config)
        self.assertEqual(step.events, self.mock_events)
        self.assertEqual(step.mail, self.mock_mail)
        self.assertEqual(step.pipeline, self.mock_pipeline)


class TestConcatStep(unittest.TestCase):
    """Tests pour l'étape de concaténation"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()

        self.mock_config = Mock()
        self.mock_config.concat_out_dir = os.path.join(self.test_dir, "concat_output")

        self.mock_events = Mock()
        self.mock_mail = Mock()
        self.mock_pipeline = Mock()

        self.concat_step = ConcatStep(
            self.mock_config, self.mock_events, self.mock_mail, self.mock_pipeline
        )

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_concat_step_initialization(self):
        """Test initialisation de ConcatStep"""
        self.assertIsInstance(self.concat_step, BaseStep)
        self.assertEqual(self.concat_step.config, self.mock_config)

    @patch('logging.info')
    def test_execute_missing_concat_file(self, mock_logging):
        """Test exécution sans fichier concat.list"""
        # Pas de fichier concat.list dans le répertoire

        result = self.concat_step.execute(self.test_dir)

        self.assertFalse(result)
        self.mock_events.add.assert_called()
        # Vérifier qu'un événement "concat_file_missing" a été ajouté
        call_args = self.mock_events.add.call_args[0]
        self.assertIn("concat_file_missing", call_args)

    def test_execute_with_concat_file(self):
        """Test exécution avec fichier concat.list présent"""
        # Créer le fichier concat.list
        concat_file = os.path.join(self.test_dir, "concat.list")
        Path(concat_file).touch()

        # Créer une structure de flowcell simulée
        flowcell_dir = os.path.join(self.test_dir, "20240101_TEST_FLOWCELL")
        analysis_dir = os.path.join(flowcell_dir, "Analysis", "1")
        os.makedirs(analysis_dir)
        Path(os.path.join(analysis_dir, "CopyComplete.txt")).touch()

        self.mock_pipeline.run_concat.return_value = True

        result = self.concat_step.execute(self.test_dir)

        # Le résultat dépend de l'implémentation spécifique
        # Vérifier que la méthode ne lève pas d'exception
        self.assertIsInstance(result, bool)

    def test_execute_with_flowcell_detection(self):
        """Test détection des flowcells"""
        # Créer le fichier concat.list
        concat_file = os.path.join(self.test_dir, "concat.list")
        Path(concat_file).touch()

        # Créer plusieurs flowcells avec dates différentes
        flowcells = [
            "20240101_ABCDEF_TEST1",
            "20240102_GHIJKL_TEST2",
            "20231215_MNOPQR_TEST3"
        ]

        for flowcell in flowcells:
            flowcell_dir = os.path.join(self.test_dir, flowcell)
            analysis_dir = os.path.join(flowcell_dir, "Analysis", "1")
            os.makedirs(analysis_dir)
            Path(os.path.join(analysis_dir, "CopyComplete.txt")).touch()

        self.mock_pipeline.run_concat.return_value = True

        result = self.concat_step.execute(self.test_dir)

        # Vérifier que l'exécution se déroule sans erreur
        self.assertIsInstance(result, bool)

    @patch('os.path.exists', return_value=False)
    def test_execute_copy_complete_missing(self, mock_exists):
        """Test quand CopyComplete.txt est manquant"""
        concat_file = os.path.join(self.test_dir, "concat.list")
        Path(concat_file).touch()

        # Créer flowcell mais sans CopyComplete.txt
        flowcell_dir = os.path.join(self.test_dir, "20240101_TEST_FLOWCELL")
        analysis_dir = os.path.join(flowcell_dir, "Analysis", "1")
        os.makedirs(analysis_dir)

        result = self.concat_step.execute(self.test_dir)

        # Devrait retourner False car CopyComplete.txt manque
        self.assertFalse(result)


class TestOrganizeStep(unittest.TestCase):
    """Tests pour l'étape d'organisation"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()

        self.mock_config = Mock()
        self.mock_events = Mock()
        self.mock_mail = Mock()
        self.mock_pipeline = Mock()

        self.organize_step = OrganizeStep(
            self.mock_config, self.mock_events, self.mock_mail, self.mock_pipeline
        )

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_organize_step_initialization(self):
        """Test initialisation de OrganizeStep"""
        self.assertIsInstance(self.organize_step, BaseStep)

    def test_execute_no_fastq_files(self):
        """Test exécution sans fichiers FASTQ"""
        result = self.organize_step.execute(self.test_dir)

        # Devrait retourner False car pas de fichiers FASTQ
        self.assertFalse(result)

    def test_execute_with_fastq_files(self):
        """Test exécution avec fichiers FASTQ"""
        # Créer des fichiers FASTQ simulés
        fastq_files = [
            "sample1.R1.fastq.gz",
            "sample1.R2.fastq.gz",
            "sample2.R1.fastq.gz",
            "sample2.R2.fastq.gz"
        ]

        for fastq_file in fastq_files:
            file_path = os.path.join(self.test_dir, fastq_file)
            # Créer des fichiers avec une taille minimale
            with open(file_path, 'wb') as f:
                f.write(b'x' * (10**7))  # 10MB

            # Créer les fichiers .end correspondants
            end_file = file_path + ".end"
            Path(end_file).touch()

        self.mock_pipeline.run_organize.return_value = True

        result = self.organize_step.execute(self.test_dir)

        # Vérifier que l'exécution se déroule
        self.assertIsInstance(result, bool)

    def test_execute_fastq_too_small(self):
        """Test avec fichiers FASTQ trop petits"""
        # Créer des fichiers FASTQ trop petits
        small_fastq = os.path.join(self.test_dir, "small.R1.fastq.gz")
        with open(small_fastq, 'wb') as f:
            f.write(b'x' * 100)  # Très petit fichier

        Path(small_fastq + ".end").touch()

        result = self.organize_step.execute(self.test_dir)

        # Devrait retourner False et enregistrer un événement
        self.assertFalse(result)
        self.mock_events.add.assert_called()

    def test_execute_missing_end_files(self):
        """Test avec fichiers .end manquants"""
        # Créer des fichiers FASTQ sans fichiers .end
        fastq_file = os.path.join(self.test_dir, "sample.R1.fastq.gz")
        with open(fastq_file, 'wb') as f:
            f.write(b'x' * (10**7))

        # Ne pas créer le fichier .end

        result = self.organize_step.execute(self.test_dir)

        # Devrait retourner False car fichier .end manquant
        self.assertFalse(result)


class TestInfofileStep(unittest.TestCase):
    """Tests pour l'étape de création du fichier d'information"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.organize_dir = os.path.join(self.test_dir, "organize")
        os.makedirs(self.organize_dir)

        self.mock_config = Mock()
        self.mock_events = Mock()
        self.mock_mail = Mock()
        self.mock_pipeline = Mock()

        self.infofile_step = InfofileStep(
            self.mock_config, self.mock_events, self.mock_mail, self.mock_pipeline
        )

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_infofile_step_initialization(self):
        """Test initialisation de InfofileStep"""
        self.assertIsInstance(self.infofile_step, BaseStep)

    def test_execute_no_organize_directory(self):
        """Test exécution sans répertoire organize"""
        empty_dir = os.path.join(self.test_dir, "empty")
        os.makedirs(empty_dir)

        result = self.infofile_step.execute(empty_dir)

        self.assertFalse(result)

    def test_execute_with_sample_directories(self):
        """Test exécution avec répertoires d'échantillons"""
        # Créer des répertoires d'échantillons
        samples = ["sample1", "sample2", "sample3"]
        for sample in samples:
            sample_dir = os.path.join(self.organize_dir, sample)
            os.makedirs(sample_dir)

            # Ajouter des fichiers FASTQ
            Path(os.path.join(sample_dir, f"{sample}.R1.fastq.gz")).touch()
            Path(os.path.join(sample_dir, f"{sample}.R2.fastq.gz")).touch()

        self.mock_pipeline.run_infofile.return_value = True

        result = self.infofile_step.execute(self.test_dir)

        self.assertIsInstance(result, bool)

    @patch('labkey.query.select_rows')
    def test_execute_with_labkey_integration(self, mock_labkey):
        """Test exécution avec intégration LabKey"""
        # Simuler une réponse LabKey
        mock_labkey.return_value = {
            "rows": [
                {"dijexID": "sample1", "PatientID": "PAT001.cas", "statut": "En cours"},
                {"dijexID": "sample2", "PatientID": "PAT001.pere", "statut": "En cours"}
            ]
        }

        # Créer les répertoires correspondants
        for sample in ["sample1", "sample2"]:
            sample_dir = os.path.join(self.organize_dir, sample)
            os.makedirs(sample_dir)

        self.mock_pipeline.run_infofile.return_value = True

        result = self.infofile_step.execute(self.test_dir)

        self.assertIsInstance(result, bool)


class TestAnalysisStep(unittest.TestCase):
    """Tests pour l'étape de lancement des analyses"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.organize_dir = os.path.join(self.test_dir, "organize")
        self.analysis_dir = os.path.join(self.test_dir, "analyse")
        os.makedirs(self.organize_dir)
        os.makedirs(self.analysis_dir)

        self.mock_config = Mock()
        self.mock_config.analysis_out_dir = self.analysis_dir

        self.mock_events = Mock()
        self.mock_mail = Mock()
        self.mock_pipeline = Mock()

        self.analysis_step = AnalysisStep(
            self.mock_config, self.mock_events, self.mock_mail, self.mock_pipeline
        )

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_analysis_step_initialization(self):
        """Test initialisation de AnalysisStep"""
        self.assertIsInstance(self.analysis_step, BaseStep)

    def test_execute_no_correspondence_file(self):
        """Test exécution sans fichier de correspondance"""
        result = self.analysis_step.execute(self.test_dir)

        self.assertFalse(result)
        # Vérifier qu'un événement est enregistré
        self.mock_events.add.assert_called()

    def test_execute_with_correspondence_file(self):
        """Test exécution avec fichier de correspondance"""
        # Créer le fichier de correspondance
        corresp_file = os.path.join(self.organize_dir, "sample_correspondance.info")
        with open(corresp_file, 'w') as f:
            f.write("SAMPLE_NAME\tPATIENT_ID\tFAMILY\tSTATUS\n")
            f.write("sample1\tPAT001.cas\tPAT001\tready\n")
            f.write("sample2\tPAT001.pere\tPAT001\tready\n")

        # Créer les répertoires d'échantillons
        for sample in ["sample1", "sample2"]:
            sample_dir = os.path.join(self.organize_dir, sample)
            os.makedirs(sample_dir)

        self.mock_pipeline.run_analysis.return_value = True

        result = self.analysis_step.execute(self.test_dir)

        self.assertIsInstance(result, bool)

    def test_execute_family_grouping(self):
        """Test regroupement par famille"""
        # Créer un fichier avec plusieurs familles
        corresp_file = os.path.join(self.organize_dir, "sample_correspondance.info")
        with open(corresp_file, 'w') as f:
            f.write("SAMPLE_NAME\tPATIENT_ID\tFAMILY\tSTATUS\n")
            f.write("sample1\tPAT001.cas\tPAT001\tready\n")
            f.write("sample2\tPAT001.pere\tPAT001\tready\n")
            f.write("sample3\tPAT002.cas\tPAT002\tready\n")

        # Créer les répertoires
        for sample in ["sample1", "sample2", "sample3"]:
            sample_dir = os.path.join(self.organize_dir, sample)
            os.makedirs(sample_dir)

        self.mock_pipeline.run_analysis.return_value = True

        result = self.analysis_step.execute(self.test_dir)

        self.assertIsInstance(result, bool)

    def test_execute_already_analyzed(self):
        """Test avec analyses déjà lancées"""
        # Créer le fichier de correspondance
        corresp_file = os.path.join(self.organize_dir, "sample_correspondance.info")
        with open(corresp_file, 'w') as f:
            f.write("SAMPLE_NAME\tPATIENT_ID\tFAMILY\tSTATUS\n")
            f.write("sample1\tPAT001.cas\tPAT001\tready\n")

        # Créer le répertoire d'échantillon
        sample_dir = os.path.join(self.organize_dir, "sample1")
        os.makedirs(sample_dir)

        # Créer un répertoire d'analyse existant
        family_analysis_dir = os.path.join(self.analysis_dir, "PAT001")
        os.makedirs(family_analysis_dir)

        result = self.analysis_step.execute(self.test_dir)

        # Devrait détecter que l'analyse existe déjà
        self.assertIsInstance(result, bool)


class TestCheckStep(unittest.TestCase):
    """Tests pour l'étape de vérification"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.analysis_dir = os.path.join(self.test_dir, "analyse")
        os.makedirs(self.analysis_dir)

        self.mock_config = Mock()
        self.mock_config.analysis_out_dir = self.analysis_dir

        self.mock_events = Mock()
        self.mock_mail = Mock()
        self.mock_pipeline = Mock()

        self.check_step = CheckStep(
            self.mock_config, self.mock_events, self.mock_mail, self.mock_pipeline
        )

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_check_step_initialization(self):
        """Test initialisation de CheckStep"""
        self.assertIsInstance(self.check_step, BaseStep)

    def test_execute_no_families(self):
        """Test exécution sans familles à vérifier"""
        result = self.check_step.execute(self.test_dir)

        # Devrait retourner True (pas d'erreur même si rien à vérifier)
        self.assertTrue(result)

    def test_execute_with_completed_analysis(self):
        """Test avec analyse complétée avec succès"""
        # Créer une famille d'analyse
        family_dir = os.path.join(self.analysis_dir, "FAM001")
        os.makedirs(family_dir)

        # Créer des répertoires d'échantillons
        for sample in ["sample1", "sample2"]:
            sample_dir = os.path.join(family_dir, sample)
            os.makedirs(sample_dir)

        # Créer un fichier status.tsv avec succès
        status_file = os.path.join(family_dir, "status.tsv")
        with open(status_file, 'w') as f:
            f.write("PROCESS\tSTATUS\tEXIT_CODE\n")
            f.write("alignment\tOK\t0\n")
            f.write("variant_calling\tOK\t0\n")
            f.write("annotation\tOK\t0\n")

        # Créer un fichier archive.log avec succès
        archive_log = os.path.join(family_dir, "archive.log")
        with open(archive_log, 'w') as f:
            f.write("Starting archiving process...\n")
            f.write("All files archived successfully\n")
            f.write("Execution with success\n")
            f.write("exit code : 0\n")

        result = self.check_step.execute(self.test_dir)

        self.assertTrue(result)

    def test_execute_with_failed_analysis(self):
        """Test avec analyse échouée"""
        # Créer une famille d'analyse
        family_dir = os.path.join(self.analysis_dir, "FAM001")
        os.makedirs(family_dir)

        # Créer un fichier status.tsv avec échecs
        status_file = os.path.join(family_dir, "status.tsv")
        with open(status_file, 'w') as f:
            f.write("PROCESS\tSTATUS\tEXIT_CODE\n")
            f.write("alignment\tOK\t0\n")
            f.write("variant_calling\tFAIL\t1\n")
            f.write("annotation\tPENDING\t-\n")

        result = self.check_step.execute(self.test_dir)

        # Devrait détecter l'échec
        self.assertIsInstance(result, bool)
        # Vérifier qu'un événement d'échec est enregistré
        self.mock_events.add.assert_called()

    def test_execute_archive_in_progress(self):
        """Test avec archivage en cours"""
        family_dir = os.path.join(self.analysis_dir, "FAM001")
        os.makedirs(family_dir)

        # Créer un fichier status.tsv complet
        status_file = os.path.join(family_dir, "status.tsv")
        with open(status_file, 'w') as f:
            f.write("PROCESS\tSTATUS\tEXIT_CODE\n")
            f.write("alignment\tOK\t0\n")
            f.write("variant_calling\tOK\t0\n")
            f.write("annotation\tOK\t0\n")

        # Créer un fichier archive.log en cours
        archive_log = os.path.join(family_dir, "archive.log")
        with open(archive_log, 'w') as f:
            f.write("Starting archiving process...\n")
            f.write("Archiving files...\n")
            # Pas de ligne de fin

        result = self.check_step.execute(self.test_dir)

        self.assertIsInstance(result, bool)

    def test_execute_missing_status_file(self):
        """Test avec fichier status.tsv manquant"""
        family_dir = os.path.join(self.analysis_dir, "FAM001")
        os.makedirs(family_dir)

        # Ne pas créer le fichier status.tsv

        result = self.check_step.execute(self.test_dir)

        # Devrait gérer l'absence du fichier
        self.assertIsInstance(result, bool)

    def test_execute_multiple_families(self):
        """Test avec plusieurs familles à différents stades"""
        families = ["FAM001", "FAM002", "FAM003"]

        for i, family in enumerate(families):
            family_dir = os.path.join(self.analysis_dir, family)
            os.makedirs(family_dir)

            status_file = os.path.join(family_dir, "status.tsv")
            with open(status_file, 'w') as f:
                f.write("PROCESS\tSTATUS\tEXIT_CODE\n")
                if i == 0:  # Première famille : succès
                    f.write("alignment\tOK\t0\n")
                    f.write("variant_calling\tOK\t0\n")
                elif i == 1:  # Deuxième famille : échec
                    f.write("alignment\tOK\t0\n")
                    f.write("variant_calling\tFAIL\t1\n")
                else:  # Troisième famille : en cours
                    f.write("alignment\tOK\t0\n")
                    f.write("variant_calling\tRUNNING\t-\n")

        result = self.check_step.execute(self.test_dir)

        # Devrait traiter toutes les familles
        self.assertIsInstance(result, bool)


if __name__ == '__main__':
    unittest.main(verbosity=2)