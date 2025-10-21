#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests simples pour vérifier la découvrabilité des tests de Matthieu
"""

import unittest
import os
import sys

# Ajouter le chemin du module parent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestSimpleDiscovery(unittest.TestCase):
    """Tests basiques pour vérifier que pytest/unittest peuvent découvrir les tests"""

    def test_basic_assertion(self):
        """Test assertion basique"""
        self.assertTrue(True)
        self.assertEqual(1 + 1, 2)

    def test_string_operations(self):
        """Test opérations sur chaînes"""
        test_string = "autolauncher"
        self.assertIn("auto", test_string)
        self.assertEqual(len(test_string), 12)

    def test_list_operations(self):
        """Test opérations sur listes"""
        test_list = [1, 2, 3, 4, 5]
        self.assertEqual(len(test_list), 5)
        self.assertIn(3, test_list)

    def test_file_path_operations(self):
        """Test opérations sur chemins de fichiers"""
        test_path = "/work/test/file.txt"
        self.assertTrue(test_path.endswith(".txt"))
        self.assertIn("test", test_path)


class TestEnvironmentSetup(unittest.TestCase):
    """Tests pour vérifier l'environnement de test"""

    def test_python_version(self):
        """Test version Python"""
        self.assertGreaterEqual(sys.version_info.major, 3)

    def test_current_directory(self):
        """Test répertoire courant"""
        current_dir = os.getcwd()
        self.assertIsInstance(current_dir, str)
        self.assertGreater(len(current_dir), 0)

    def test_imports_available(self):
        """Test que les imports de base sont disponibles"""
        import tempfile
        import pathlib
        import unittest.mock

        self.assertTrue(hasattr(tempfile, 'mkdtemp'))
        self.assertTrue(hasattr(pathlib, 'Path'))
        self.assertTrue(hasattr(unittest.mock, 'Mock'))


if __name__ == '__main__':
    unittest.main(verbosity=2)