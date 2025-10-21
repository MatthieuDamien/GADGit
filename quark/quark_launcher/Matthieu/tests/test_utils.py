#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour utils.py - Fonctions utilitaires de l'autolauncher de Matthieu
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

# pylint: disable-next=E0401
from utils import get_or_create_file


class TestGetOrCreateFile(unittest.TestCase):
    """Tests pour la fonction get_or_create_file"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_get_existing_file(self):
        """Test récupération d'un fichier existant"""
        existing_file = os.path.join(self.test_dir, "existing.txt")
        Path(existing_file).touch()

        result = get_or_create_file(
            arg_path=existing_file,
            default="default.txt",
            base_dir=self.test_dir,
            category="test"
        )

        self.assertEqual(result, existing_file)
        self.assertTrue(os.path.exists(result))

    def test_create_file_with_default_name(self):
        """Test création d'un fichier avec nom par défaut"""
        default_name = "default.txt"

        result = get_or_create_file(
            arg_path=None,
            default=default_name,
            base_dir=self.test_dir,
            category="test"
        )

        expected_path = os.path.join(self.test_dir, default_name)
        self.assertEqual(result, expected_path)
        self.assertTrue(os.path.exists(result))

    def test_create_file_with_empty_arg_path(self):
        """Test création avec arg_path vide"""
        default_name = "empty_arg.txt"

        result = get_or_create_file(
            arg_path="",
            default=default_name,
            base_dir=self.test_dir,
            category="test"
        )

        expected_path = os.path.join(self.test_dir, default_name)
        self.assertEqual(result, expected_path)
        self.assertTrue(os.path.exists(result))

    def test_create_file_absolute_path(self):
        """Test création avec chemin absolu fourni"""
        absolute_path = os.path.join(self.test_dir, "absolute.txt")

        result = get_or_create_file(
            arg_path=absolute_path,
            default="default.txt",
            base_dir="/different/dir",
            category="test"
        )

        self.assertEqual(result, absolute_path)
        self.assertTrue(os.path.exists(result))

    def test_create_file_relative_path(self):
        """Test création avec chemin relatif"""
        relative_path = "relative.txt"

        result = get_or_create_file(
            arg_path=relative_path,
            default="default.txt",
            base_dir=self.test_dir,
            category="test"
        )

        expected_path = os.path.join(self.test_dir, relative_path)
        self.assertEqual(result, expected_path)
        self.assertTrue(os.path.exists(result))

    def test_create_file_in_nested_directory(self):
        """Test création dans répertoire imbriqué"""
        nested_path = os.path.join("nested", "dir", "file.txt")

        result = get_or_create_file(
            arg_path=nested_path,
            default="default.txt",
            base_dir=self.test_dir,
            category="test"
        )

        expected_path = os.path.join(self.test_dir, nested_path)
        self.assertEqual(result, expected_path)
        self.assertTrue(os.path.exists(result))
        # Vérifier que les répertoires parents ont été créés
        self.assertTrue(os.path.exists(os.path.dirname(result)))

    def test_create_file_with_executable_permission(self):
        """Test que les fichiers .sh sont créés avec permissions d'exécution"""
        shell_file = "script.sh"

        result = get_or_create_file(
            arg_path=shell_file,
            default="default.sh",
            base_dir=self.test_dir,
            category="script"
        )

        expected_path = os.path.join(self.test_dir, shell_file)
        self.assertEqual(result, expected_path)
        self.assertTrue(os.path.exists(result))

        # Vérifier les permissions (sur Unix/Linux)
        if os.name != 'nt':  # Pas Windows
            file_stat = os.stat(result)
            # Vérifier que le fichier a des permissions d'exécution
            self.assertTrue(file_stat.st_mode & 0o111)  # Au moins une permission d'exécution

    def test_different_file_extensions(self):
        """Test avec différentes extensions de fichier"""
        extensions = [".log", ".txt", ".sh", ".py", ".events"]

        for ext in extensions:
            filename = f"test{ext}"

            result = get_or_create_file(
                arg_path=filename,
                default=f"default{ext}",
                base_dir=self.test_dir,
                category="test"
            )

            expected_path = os.path.join(self.test_dir, filename)
            self.assertEqual(result, expected_path)
            self.assertTrue(os.path.exists(result))

    @patch('pathlib.Path.touch')
    @patch('logging.error')
    def test_create_file_permission_error(self, mock_logging, mock_touch):
        """Test gestion d'erreur de permission lors de la création"""
        mock_touch.side_effect = PermissionError("Permission denied")

        with self.assertRaises(PermissionError):
            get_or_create_file(
                arg_path="test.txt",
                default="default.txt",
                base_dir=self.test_dir,
                category="test"
            )

        mock_logging.assert_called()

    @patch('pathlib.Path.mkdir')
    @patch('logging.error')
    def test_create_directory_error(self, mock_logging, mock_mkdir):
        """Test gestion d'erreur lors de la création de répertoire"""
        mock_mkdir.side_effect = OSError("Cannot create directory")

        with self.assertRaises(OSError):
            get_or_create_file(
                arg_path=os.path.join("nested", "dir", "file.txt"),
                default="default.txt",
                base_dir=self.test_dir,
                category="test"
            )

    def test_create_file_with_special_characters(self):
        """Test création avec caractères spéciaux dans le nom"""
        special_names = [
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file with spaces.txt",
            "file.with.dots.txt"
        ]

        for filename in special_names:
            result = get_or_create_file(
                arg_path=filename,
                default="default.txt",
                base_dir=self.test_dir,
                category="test"
            )

            expected_path = os.path.join(self.test_dir, filename)
            self.assertEqual(result, expected_path)
            self.assertTrue(os.path.exists(result))

    def test_create_file_unicode_name(self):
        """Test création avec nom Unicode"""
        unicode_names = [
            "fichier_éàç.txt",
            "archivo_ñoël.txt",
            "文件_测试.txt"
        ]

        for filename in unicode_names:
            try:
                result = get_or_create_file(
                    arg_path=filename,
                    default="default.txt",
                    base_dir=self.test_dir,
                    category="test"
                )

                expected_path = os.path.join(self.test_dir, filename)
                self.assertEqual(result, expected_path)
                self.assertTrue(os.path.exists(result))
            except (UnicodeEncodeError, OSError):
                # Certains systèmes peuvent ne pas supporter certains caractères Unicode
                # C'est acceptable
                pass

    def test_file_creation_logging(self):
        """Test que la création de fichier est bien loggée"""
        with patch('logging.info') as mock_logging:
            get_or_create_file(
                arg_path="test.txt",
                default="default.txt",
                base_dir=self.test_dir,
                category="test_category"
            )

            # Vérifier qu'un message de log a été émis
            mock_logging.assert_called()
            # Vérifier que le message contient la catégorie
            call_args = mock_logging.call_args[0][0]
            self.assertIn("test_category", call_args)

    def test_file_already_exists_no_recreation(self):
        """Test qu'un fichier existant n'est pas recréé"""
        existing_file = os.path.join(self.test_dir, "existing.txt")

        # Créer le fichier avec un contenu spécifique
        with open(existing_file, 'w') as f:
            f.write("original content")

        # Obtenir le temps de modification original
        original_mtime = os.path.getmtime(existing_file)

        # Appeler get_or_create_file
        result = get_or_create_file(
            arg_path=existing_file,
            default="default.txt",
            base_dir=self.test_dir,
            category="test"
        )

        # Vérifier que le fichier n'a pas été modifié
        new_mtime = os.path.getmtime(result)
        self.assertEqual(original_mtime, new_mtime)

        # Vérifier que le contenu est intact
        with open(result, 'r') as f:
            content = f.read()
        self.assertEqual(content, "original content")

    def test_base_dir_creation(self):
        """Test création du répertoire de base si inexistant"""
        nonexistent_base = os.path.join(self.test_dir, "new_base_dir")

        result = get_or_create_file(
            arg_path="test.txt",
            default="default.txt",
            base_dir=nonexistent_base,
            category="test"
        )

        # Vérifier que le répertoire de base a été créé
        self.assertTrue(os.path.exists(nonexistent_base))
        self.assertTrue(os.path.isdir(nonexistent_base))

        # Vérifier que le fichier a été créé
        expected_path = os.path.join(nonexistent_base, "test.txt")
        self.assertEqual(result, expected_path)
        self.assertTrue(os.path.exists(result))

    def test_empty_default_name(self):
        """Test avec nom par défaut vide"""
        with self.assertRaises((ValueError, OSError)):
            get_or_create_file(
                arg_path=None,
                default="",
                base_dir=self.test_dir,
                category="test"
            )

    def test_none_base_dir(self):
        """Test avec base_dir None"""
        with self.assertRaises((TypeError, OSError)):
            get_or_create_file(
                arg_path="test.txt",
                default="default.txt",
                base_dir=None,
                category="test"
            )

    def test_empty_category(self):
        """Test avec catégorie vide"""
        # Ne devrait pas lever d'erreur, juste ne pas mentionner la catégorie dans les logs
        result = get_or_create_file(
            arg_path="test.txt",
            default="default.txt",
            base_dir=self.test_dir,
            category=""
        )

        expected_path = os.path.join(self.test_dir, "test.txt")
        self.assertEqual(result, expected_path)
        self.assertTrue(os.path.exists(result))

    def test_very_long_filename(self):
        """Test avec nom de fichier très long"""
        long_name = "very_long_filename_" + "x" * 200 + ".txt"

        try:
            result = get_or_create_file(
                arg_path=long_name,
                default="default.txt",
                base_dir=self.test_dir,
                category="test"
            )

            # Si ça réussit, vérifier que le fichier existe
            self.assertTrue(os.path.exists(result))
        except OSError:
            # Nom trop long pour le système de fichiers, acceptable
            pass

    def test_path_traversal_protection(self):
        """Test protection contre traversée de répertoire"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32\\config"
        ]

        for malicious_path in malicious_paths:
            result = get_or_create_file(
                arg_path=malicious_path,
                default="default.txt",
                base_dir=self.test_dir,
                category="test"
            )

            # Le fichier devrait être créé dans ou sous le répertoire de test
            # et pas dans un répertoire système
            self.assertTrue(result.startswith(self.test_dir) or
                           os.path.commonpath([result, self.test_dir]) == self.test_dir)


if __name__ == '__main__':
    unittest.main(verbosity=2)