#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour lock.py - Gestion des verrous de l'autolauncher de Matthieu
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

from lock import LockManager


class TestLockManagerInitialization(unittest.TestCase):
    """Tests pour l'initialisation du gestionnaire de verrous"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_lock_manager_initialization(self):
        """Test initialisation du LockManager"""
        lock_manager = LockManager(self.test_dir)

        self.assertEqual(lock_manager.base_dir, self.test_dir)
        self.assertEqual(lock_manager.lock_file, os.path.join(self.test_dir, "autolaunch.lock"))
        self.assertFalse(lock_manager.is_locked)

    def test_lock_manager_with_nonexistent_directory(self):
        """Test initialisation avec répertoire inexistant"""
        nonexistent_dir = os.path.join(self.test_dir, "nonexistent")

        # Ne devrait pas lever d'erreur lors de l'initialisation
        lock_manager = LockManager(nonexistent_dir)

        self.assertEqual(lock_manager.base_dir, nonexistent_dir)
        self.assertEqual(lock_manager.lock_file, os.path.join(nonexistent_dir, "autolaunch.lock"))

    def test_lock_file_path_construction(self):
        """Test construction du chemin du fichier de verrou"""
        test_path = "/test/custom/path"
        lock_manager = LockManager(test_path)

        expected_lock_file = os.path.join(test_path, "autolaunch.lock")
        self.assertEqual(lock_manager.lock_file, expected_lock_file)


class TestLockAcquisition(unittest.TestCase):
    """Tests pour l'acquisition de verrous"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.lock_manager = LockManager(self.test_dir)

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_acquire_lock_success(self):
        """Test acquisition réussie du verrou"""
        result = self.lock_manager.acquire()

        self.assertTrue(result)
        self.assertTrue(self.lock_manager.is_locked)
        self.assertTrue(os.path.exists(self.lock_manager.lock_file))

        # Vérifier le contenu du fichier de verrou
        with open(self.lock_manager.lock_file, 'r') as f:
            content = f.read().strip()
            self.assertEqual(content, "1")

    def test_acquire_lock_already_exists(self):
        """Test acquisition quand le verrou existe déjà"""
        # Créer manuellement le fichier de verrou
        Path(self.lock_manager.lock_file).touch()

        result = self.lock_manager.acquire()

        self.assertFalse(result)
        self.assertFalse(self.lock_manager.is_locked)

    def test_acquire_lock_with_existing_content(self):
        """Test acquisition avec fichier de verrou contenant déjà du contenu"""
        # Créer un fichier de verrou avec du contenu
        with open(self.lock_manager.lock_file, 'w') as f:
            f.write("existing content")

        result = self.lock_manager.acquire()

        self.assertFalse(result)
        self.assertFalse(self.lock_manager.is_locked)

    @patch('pathlib.Path.touch')
    @patch('logging.error')
    def test_acquire_lock_permission_error(self, mock_logging, mock_touch):
        """Test gestion d'erreur de permission lors de l'acquisition"""
        mock_touch.side_effect = PermissionError("Permission denied")

        result = self.lock_manager.acquire()

        self.assertFalse(result)
        self.assertFalse(self.lock_manager.is_locked)
        mock_logging.assert_called()

    @patch('builtins.open', side_effect=IOError("Cannot write"))
    @patch('logging.error')
    def test_acquire_lock_io_error(self, mock_logging, mock_open):
        """Test gestion d'erreur I/O lors de l'écriture du verrou"""
        # D'abord créer le fichier pour que Path.exists() retourne False
        with patch('pathlib.Path.exists', return_value=False):
            result = self.lock_manager.acquire()

            self.assertFalse(result)
            self.assertFalse(self.lock_manager.is_locked)
            mock_logging.assert_called()

    def test_acquire_lock_directory_creation(self):
        """Test création du répertoire lors de l'acquisition"""
        # Utiliser un répertoire qui n'existe pas
        nested_dir = os.path.join(self.test_dir, "nested", "directory")
        lock_manager = LockManager(nested_dir)

        result = lock_manager.acquire()

        self.assertTrue(result)
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.exists(lock_manager.lock_file))


class TestLockRelease(unittest.TestCase):
    """Tests pour la libération de verrous"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.lock_manager = LockManager(self.test_dir)

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_release_acquired_lock(self):
        """Test libération d'un verrou acquis"""
        # D'abord acquérir le verrou
        self.lock_manager.acquire()
        self.assertTrue(self.lock_manager.is_locked)

        # Puis le libérer
        result = self.lock_manager.release()

        self.assertTrue(result)
        self.assertFalse(self.lock_manager.is_locked)
        self.assertFalse(os.path.exists(self.lock_manager.lock_file))

    def test_release_non_acquired_lock(self):
        """Test libération sans avoir acquis le verrou"""
        result = self.lock_manager.release()

        # Devrait retourner True même si pas acquis (pas d'erreur)
        self.assertTrue(result)
        self.assertFalse(self.lock_manager.is_locked)

    def test_release_manually_created_lock(self):
        """Test libération d'un verrou créé manuellement"""
        # Créer manuellement un fichier de verrou
        Path(self.lock_manager.lock_file).touch()

        # Marquer comme verrouillé manuellement
        self.lock_manager.is_locked = True

        result = self.lock_manager.release()

        self.assertTrue(result)
        self.assertFalse(self.lock_manager.is_locked)
        self.assertFalse(os.path.exists(self.lock_manager.lock_file))

    @patch('pathlib.Path.unlink')
    @patch('logging.error')
    def test_release_permission_error(self, mock_logging, mock_unlink):
        """Test gestion d'erreur de permission lors de la libération"""
        # Acquérir d'abord le verrou
        self.lock_manager.acquire()

        # Simuler une erreur de permission lors de la suppression
        mock_unlink.side_effect = PermissionError("Permission denied")

        result = self.lock_manager.release()

        self.assertFalse(result)
        self.assertTrue(self.lock_manager.is_locked)  # Reste verrouillé
        mock_logging.assert_called()

    @patch('pathlib.Path.unlink')
    @patch('logging.error')
    def test_release_file_not_found_error(self, mock_logging, mock_unlink):
        """Test gestion quand le fichier de verrou n'existe plus"""
        # Marquer comme verrouillé
        self.lock_manager.is_locked = True

        # Simuler que le fichier n'existe plus
        mock_unlink.side_effect = FileNotFoundError("File not found")

        result = self.lock_manager.release()

        # Devrait réussir car le fichier n'existe plus (objectif atteint)
        self.assertTrue(result)
        self.assertFalse(self.lock_manager.is_locked)
        # Le logging ne devrait pas être appelé pour FileNotFoundError


class TestLockStatus(unittest.TestCase):
    """Tests pour la vérification du statut des verrous"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.lock_manager = LockManager(self.test_dir)

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_is_locked_property_initial_state(self):
        """Test état initial de la propriété is_locked"""
        self.assertFalse(self.lock_manager.is_locked)

    def test_is_locked_after_acquire(self):
        """Test propriété is_locked après acquisition"""
        self.lock_manager.acquire()
        self.assertTrue(self.lock_manager.is_locked)

    def test_is_locked_after_release(self):
        """Test propriété is_locked après libération"""
        self.lock_manager.acquire()
        self.lock_manager.release()
        self.assertFalse(self.lock_manager.is_locked)

    def test_lock_file_exists_detection(self):
        """Test détection de l'existence du fichier de verrou"""
        # Initialement, pas de fichier
        self.assertFalse(os.path.exists(self.lock_manager.lock_file))

        # Créer manuellement le fichier
        Path(self.lock_manager.lock_file).touch()
        self.assertTrue(os.path.exists(self.lock_manager.lock_file))

        # L'acquisition devrait échouer
        result = self.lock_manager.acquire()
        self.assertFalse(result)


class TestLockManagerEdgeCases(unittest.TestCase):
    """Tests pour les cas limites du gestionnaire de verrous"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_multiple_acquire_attempts(self):
        """Test multiples tentatives d'acquisition"""
        lock_manager = LockManager(self.test_dir)

        # Première acquisition
        result1 = lock_manager.acquire()
        self.assertTrue(result1)
        self.assertTrue(lock_manager.is_locked)

        # Deuxième tentative sur la même instance
        result2 = lock_manager.acquire()
        self.assertFalse(result2)  # Devrait échouer car déjà verrouillé
        self.assertTrue(lock_manager.is_locked)

    def test_multiple_release_attempts(self):
        """Test multiples tentatives de libération"""
        lock_manager = LockManager(self.test_dir)

        # Acquérir puis libérer
        lock_manager.acquire()
        result1 = lock_manager.release()
        self.assertTrue(result1)
        self.assertFalse(lock_manager.is_locked)

        # Deuxième libération
        result2 = lock_manager.release()
        self.assertTrue(result2)  # Devrait réussir (pas d'erreur)
        self.assertFalse(lock_manager.is_locked)

    def test_concurrent_lock_managers(self):
        """Test avec plusieurs gestionnaires de verrous sur le même répertoire"""
        lock_manager1 = LockManager(self.test_dir)
        lock_manager2 = LockManager(self.test_dir)

        # Le premier acquiert le verrou
        result1 = lock_manager1.acquire()
        self.assertTrue(result1)
        self.assertTrue(lock_manager1.is_locked)

        # Le second ne peut pas l'acquérir
        result2 = lock_manager2.acquire()
        self.assertFalse(result2)
        self.assertFalse(lock_manager2.is_locked)

        # Libération par le premier
        lock_manager1.release()

        # Maintenant le second peut l'acquérir
        result3 = lock_manager2.acquire()
        self.assertTrue(result3)
        self.assertTrue(lock_manager2.is_locked)

    def test_lock_with_special_characters_in_path(self):
        """Test avec caractères spéciaux dans le chemin"""
        special_dir = os.path.join(self.test_dir, "dir with spaces", "and-dashes", "under_scores")
        os.makedirs(special_dir, exist_ok=True)

        lock_manager = LockManager(special_dir)
        result = lock_manager.acquire()

        self.assertTrue(result)
        self.assertTrue(os.path.exists(lock_manager.lock_file))

    def test_lock_with_unicode_path(self):
        """Test avec caractères Unicode dans le chemin"""
        unicode_dir = os.path.join(self.test_dir, "répertoire_ñoël_测试")
        os.makedirs(unicode_dir, exist_ok=True)

        lock_manager = LockManager(unicode_dir)
        result = lock_manager.acquire()

        self.assertTrue(result)
        self.assertTrue(os.path.exists(lock_manager.lock_file))

    def test_very_long_path(self):
        """Test avec chemin très long"""
        # Créer un chemin très long
        long_path_parts = ["very"] * 50 + ["long", "path"]
        long_dir = os.path.join(self.test_dir, *long_path_parts)

        try:
            os.makedirs(long_dir, exist_ok=True)
            lock_manager = LockManager(long_dir)
            result = lock_manager.acquire()

            # Le test peut réussir ou échouer selon les limites du système
            # Pas d'assertion stricte ici
            if result:
                self.assertTrue(os.path.exists(lock_manager.lock_file))
        except OSError:
            # Chemin trop long pour le système, c'est acceptable
            pass


class TestLockManagerIntegration(unittest.TestCase):
    """Tests d'intégration pour le gestionnaire de verrous"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_context_manager_pattern(self):
        """Test utilisation avec pattern context manager simulé"""
        lock_manager = LockManager(self.test_dir)

        try:
            # Acquisition
            if lock_manager.acquire():
                # Simulation de travail
                self.assertTrue(lock_manager.is_locked)
                self.assertTrue(os.path.exists(lock_manager.lock_file))
        finally:
            # Libération garantie
            lock_manager.release()

        self.assertFalse(lock_manager.is_locked)
        self.assertFalse(os.path.exists(lock_manager.lock_file))

    def test_lock_file_content_verification(self):
        """Test vérification du contenu du fichier de verrou"""
        lock_manager = LockManager(self.test_dir)
        lock_manager.acquire()

        # Vérifier que le contenu est bien "1"
        with open(lock_manager.lock_file, 'r') as f:
            content = f.read().strip()

        self.assertEqual(content, "1")

    def test_lock_file_permissions(self):
        """Test permissions du fichier de verrou"""
        lock_manager = LockManager(self.test_dir)
        lock_manager.acquire()

        # Vérifier que le fichier existe et est lisible
        self.assertTrue(os.path.exists(lock_manager.lock_file))
        self.assertTrue(os.access(lock_manager.lock_file, os.R_OK))

    def test_lock_manager_state_consistency(self):
        """Test cohérence de l'état du gestionnaire"""
        lock_manager = LockManager(self.test_dir)

        # État initial
        self.assertFalse(lock_manager.is_locked)
        self.assertFalse(os.path.exists(lock_manager.lock_file))

        # Après acquisition
        lock_manager.acquire()
        self.assertTrue(lock_manager.is_locked)
        self.assertTrue(os.path.exists(lock_manager.lock_file))

        # Après libération
        lock_manager.release()
        self.assertFalse(lock_manager.is_locked)
        self.assertFalse(os.path.exists(lock_manager.lock_file))


if __name__ == '__main__':
    unittest.main(verbosity=2)