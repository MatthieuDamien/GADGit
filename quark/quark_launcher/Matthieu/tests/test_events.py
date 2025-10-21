#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour events.py - Gestion des événements de l'autolauncher de Matthieu
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Ajouter le chemin du module parent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from events import EventsRegister, create_events_register


class TestEventsRegisterCreation(unittest.TestCase):
    """Tests pour la création et l'initialisation de EventsRegister"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.event_file = os.path.join(self.test_dir, "test_events.txt")

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_events_register_new_file(self):
        """Test création d'un registre avec fichier inexistant"""
        events = create_events_register(self.event_file)

        self.assertIsInstance(events, EventsRegister)
        self.assertTrue(os.path.exists(self.event_file))
        self.assertTrue(events.loaded)
        self.assertEqual(len(events.location_list), 0)

    def test_create_events_register_existing_file(self):
        """Test création d'un registre avec fichier existant"""
        # Créer un fichier avec du contenu
        with open(self.event_file, 'w') as f:
            f.write("loc1\tsample1\ttype1\t5\n")
            f.write("loc2\tsample2\ttype2\t3\n")

        events = create_events_register(self.event_file)

        self.assertTrue(events.loaded)
        self.assertEqual(len(events.location_list), 2)
        self.assertEqual(events.location_list[0], "loc1")
        self.assertEqual(events.sample_list[0], "sample1")
        self.assertEqual(events.type_list[0], "type1")
        self.assertEqual(events.counter_list[0], 5)

    def test_events_register_initialization(self):
        """Test initialisation directe de EventsRegister"""
        events = EventsRegister(self.event_file)

        self.assertEqual(events.event_file, self.event_file)
        self.assertFalse(events.loaded)
        self.assertFalse(events.registration_fail)
        self.assertEqual(len(events.location_list), 0)
        self.assertEqual(len(events.sample_list), 0)
        self.assertEqual(len(events.type_list), 0)
        self.assertEqual(len(events.counter_list), 0)


class TestEventsRegisterLoading(unittest.TestCase):
    """Tests pour le chargement des événements depuis un fichier"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.event_file = os.path.join(self.test_dir, "test_events.txt")

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_load_empty_file(self):
        """Test chargement d'un fichier vide"""
        Path(self.event_file).touch()

        events = EventsRegister(self.event_file)
        events.load()

        self.assertTrue(events.loaded)
        self.assertEqual(len(events.location_list), 0)

    def test_load_file_with_valid_data(self):
        """Test chargement d'un fichier avec données valides"""
        with open(self.event_file, 'w') as f:
            f.write("location1\tsample1\tanalysis_ok\t1\n")
            f.write("location2\tsample2\tarchive_success\t3\n")
            f.write("location3\tsample3\tconcat_file_missing\t10\n")

        events = EventsRegister(self.event_file)
        events.load()

        self.assertTrue(events.loaded)
        self.assertEqual(len(events.location_list), 3)

        # Vérifier le premier événement
        self.assertEqual(events.location_list[0], "location1")
        self.assertEqual(events.sample_list[0], "sample1")
        self.assertEqual(events.type_list[0], "analysis_ok")
        self.assertEqual(events.counter_list[0], 1)

        # Vérifier le troisième événement
        self.assertEqual(events.counter_list[2], 10)

    def test_load_file_with_invalid_lines(self):
        """Test chargement avec des lignes invalides"""
        with open(self.event_file, 'w') as f:
            f.write("location1\tsample1\tanalysis_ok\t1\n")
            f.write("ligne_invalide\n")  # Ligne sans assez de colonnes
            f.write("location2\tsample2\tarchive_success\tinvalid_count\n")  # Compteur invalide
            f.write("location3\tsample3\tconcat_file_missing\t5\n")

        events = EventsRegister(self.event_file)
        events.load()

        self.assertTrue(events.loaded)
        # Seules les lignes valides doivent être chargées
        self.assertEqual(len(events.location_list), 2)
        self.assertEqual(events.location_list[0], "location1")
        self.assertEqual(events.location_list[1], "location3")

    @patch('builtins.open', side_effect=IOError("Cannot read file"))
    @patch('logging.error')
    def test_load_file_io_error(self, mock_logging, mock_open):
        """Test gestion d'erreur lors du chargement"""
        events = EventsRegister(self.event_file)
        events.load()

        self.assertFalse(events.loaded)
        self.assertTrue(events.registration_fail)
        mock_logging.assert_called()


class TestEventsRegisterOperations(unittest.TestCase):
    """Tests pour les opérations sur les événements"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.event_file = os.path.join(self.test_dir, "test_events.txt")

        # Créer un registre avec des données initiales
        with open(self.event_file, 'w') as f:
            f.write("loc1\tsample1\tanalysis_ok\t2\n")
            f.write("loc2\tsample2\tarchive_success\t1\n")

        self.events = EventsRegister(self.event_file)
        self.events.load()

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_add_new_event(self):
        """Test ajout d'un nouvel événement"""
        initial_count = len(self.events.location_list)

        self.events.add("loc3", "sample3", "concat_file_missing")

        self.assertEqual(len(self.events.location_list), initial_count + 1)
        self.assertEqual(self.events.location_list[-1], "loc3")
        self.assertEqual(self.events.sample_list[-1], "sample3")
        self.assertEqual(self.events.type_list[-1], "concat_file_missing")
        self.assertEqual(self.events.counter_list[-1], 1)

    def test_add_existing_event_increments_counter(self):
        """Test ajout d'un événement existant (incrémente le compteur)"""
        initial_count = len(self.events.location_list)
        initial_counter = self.events.counter_list[0]

        self.events.add("loc1", "sample1", "analysis_ok")

        # Le nombre d'événements ne change pas
        self.assertEqual(len(self.events.location_list), initial_count)
        # Le compteur est incrémenté
        self.assertEqual(self.events.counter_list[0], initial_counter + 1)

    def test_count_existing_event(self):
        """Test comptage d'un événement existant"""
        count = self.events.count("loc1", "sample1", "analysis_ok")
        self.assertEqual(count, 2)

    def test_count_nonexistent_event(self):
        """Test comptage d'un événement inexistant"""
        count = self.events.count("nonexistent", "sample", "type")
        self.assertEqual(count, 0)

    def test_delete_existing_event(self):
        """Test suppression d'un événement existant"""
        initial_count = len(self.events.location_list)

        self.events.delete("loc1", "sample1", "analysis_ok")

        self.assertEqual(len(self.events.location_list), initial_count - 1)
        # Vérifier que l'événement n'existe plus
        count = self.events.count("loc1", "sample1", "analysis_ok")
        self.assertEqual(count, 0)

    def test_delete_nonexistent_event(self):
        """Test suppression d'un événement inexistant"""
        initial_count = len(self.events.location_list)

        # Ne devrait pas lever d'erreur
        self.events.delete("nonexistent", "sample", "type")

        # Le nombre d'événements ne change pas
        self.assertEqual(len(self.events.location_list), initial_count)

    def test_listing_events(self):
        """Test listing des événements"""
        event_list = self.events.listing()

        self.assertEqual(len(event_list), 2)
        self.assertIn("loc1\tsample1\tanalysis_ok", event_list)
        self.assertIn("loc2\tsample2\tarchive_success", event_list)


class TestEventsRegisterSaving(unittest.TestCase):
    """Tests pour la sauvegarde des événements"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.event_file = os.path.join(self.test_dir, "test_events.txt")
        self.output_file = os.path.join(self.test_dir, "output_events.txt")

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_to_original_file(self):
        """Test sauvegarde dans le fichier original"""
        events = EventsRegister(self.event_file)
        events.add("loc1", "sample1", "analysis_ok")
        events.add("loc2", "sample2", "archive_success")

        events.save()

        self.assertTrue(os.path.exists(self.event_file))

        # Vérifier le contenu sauvegardé
        with open(self.event_file, 'r') as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)
        self.assertIn("loc1\tsample1\tanalysis_ok\t1", lines[0])
        self.assertIn("loc2\tsample2\tarchive_success\t1", lines[1])

    def test_save_to_custom_file(self):
        """Test sauvegarde dans un fichier personnalisé"""
        events = EventsRegister(self.event_file)
        events.add("loc1", "sample1", "analysis_ok")

        events.save(self.output_file)

        self.assertTrue(os.path.exists(self.output_file))

        # Vérifier le contenu
        with open(self.output_file, 'r') as f:
            content = f.read()

        self.assertIn("loc1\tsample1\tanalysis_ok\t1", content)

    @patch('builtins.open', side_effect=IOError("Cannot write file"))
    @patch('logging.error')
    def test_save_io_error(self, mock_logging, mock_open):
        """Test gestion d'erreur lors de la sauvegarde"""
        events = EventsRegister(self.event_file)
        events.add("loc1", "sample1", "analysis_ok")

        events.save()

        self.assertTrue(events.registration_fail)
        mock_logging.assert_called()


class TestEventsRegisterIntegrity(unittest.TestCase):
    """Tests pour la vérification d'intégrité du registre"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.event_file = os.path.join(self.test_dir, "test_events.txt")

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_test_integrity_consistent_data(self):
        """Test vérification d'intégrité avec données cohérentes"""
        events = EventsRegister(self.event_file)
        events.add("loc1", "sample1", "analysis_ok")
        events.add("loc2", "sample2", "archive_success")

        # Ne devrait pas lever d'erreur
        events.test_integrity()
        self.assertFalse(events.registration_fail)

    def test_test_integrity_inconsistent_lists(self):
        """Test vérification d'intégrité avec listes incohérentes"""
        events = EventsRegister(self.event_file)

        # Créer des listes de tailles différentes (inconsistance)
        events.location_list = ["loc1", "loc2"]
        events.sample_list = ["sample1"]  # Taille différente
        events.type_list = ["type1", "type2"]
        events.counter_list = [1, 2]

        with patch('logging.error') as mock_logging:
            events.test_integrity()

            self.assertTrue(events.registration_fail)
            mock_logging.assert_called()

    def test_event_types_validation(self):
        """Test validation des types d'événements"""
        # Vérifier que tous les types sont des chaînes non vides
        for event_type in EventsRegister.EVENT_TYPES:
            self.assertIsInstance(event_type, str)
            self.assertGreater(len(event_type), 0)

        # Vérifier quelques types spécifiques attendus
        expected_types = [
            "lockfile_found", "concat_file_missing", "analysis_ok",
            "archive_success", "analysis_launched"
        ]

        for expected_type in expected_types:
            self.assertIn(expected_type, EventsRegister.EVENT_TYPES)


class TestEventsRegisterEdgeCases(unittest.TestCase):
    """Tests pour les cas limites et situations exceptionnelles"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.event_file = os.path.join(self.test_dir, "test_events.txt")

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_add_event_with_special_characters(self):
        """Test ajout d'événement avec caractères spéciaux"""
        events = EventsRegister(self.event_file)

        # Tester avec des caractères qui pourraient poser problème
        events.add("loc/with/slash", "sample-with-dash", "type_with_underscore")

        self.assertEqual(len(events.location_list), 1)
        self.assertEqual(events.location_list[0], "loc/with/slash")

    def test_count_with_empty_parameters(self):
        """Test comptage avec paramètres vides"""
        events = EventsRegister(self.event_file)
        events.add("", "", "")

        count = events.count("", "", "")
        self.assertEqual(count, 1)

    def test_multiple_identical_adds(self):
        """Test ajouts multiples identiques"""
        events = EventsRegister(self.event_file)

        # Ajouter le même événement plusieurs fois
        for i in range(5):
            events.add("loc", "sample", "type")

        self.assertEqual(len(events.location_list), 1)
        self.assertEqual(events.counter_list[0], 5)

    def test_operations_without_loading(self):
        """Test opérations sans chargement préalable"""
        events = EventsRegister(self.event_file)
        # Ne pas appeler load()

        # Les opérations devraient fonctionner
        events.add("loc", "sample", "type")
        count = events.count("loc", "sample", "type")

        self.assertEqual(count, 1)
        self.assertEqual(len(events.location_list), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)