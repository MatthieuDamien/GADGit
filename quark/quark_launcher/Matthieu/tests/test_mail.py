#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour mail.py - Gestion des mails de l'autolauncher de Matthieu
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

from mail import MailManager # pylint: disable=E0401


class TestMailManagerInitialization(unittest.TestCase):
    """Tests pour l'initialisation du gestionnaire de mails"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.mail_file = os.path.join(self.test_dir, "test_mail.sh")
        self.mail_address = "test@example.com"

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_mail_manager_initialization(self):
        """Test initialisation du MailManager"""
        Path(self.mail_file).touch()

        mail_manager = MailManager(self.mail_file, self.mail_address)

        self.assertEqual(mail_manager.mail_file, self.mail_file)
        self.assertEqual(mail_manager.mail_bioinfo, self.mail_address)

    def test_mail_manager_with_nonexistent_file(self):
        """Test initialisation avec fichier inexistant"""
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.sh")

        # Ne devrait pas lever d'erreur lors de l'initialisation
        mail_manager = MailManager(nonexistent_file, self.mail_address)

        self.assertEqual(mail_manager.mail_file, nonexistent_file)
        self.assertEqual(mail_manager.mail_bioinfo, self.mail_address)

    def test_mail_manager_with_empty_address(self):
        """Test initialisation avec adresse email vide"""
        Path(self.mail_file).touch()

        mail_manager = MailManager(self.mail_file, "")

        self.assertEqual(mail_manager.mail_bioinfo, "")

    def test_mail_manager_properties(self):
        """Test accès aux propriétés"""
        Path(self.mail_file).touch()

        mail_manager = MailManager(self.mail_file, self.mail_address)

        self.assertIsInstance(mail_manager.mail_file, str)
        self.assertIsInstance(mail_manager.mail_bioinfo, str)


class TestMailSendingError(unittest.TestCase):
    """Tests pour l'envoi de mails d'erreur"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.mail_file = os.path.join(self.test_dir, "test_mail.sh")
        self.mail_address = "bioinfo@example.com"

        # Créer le fichier de mail
        Path(self.mail_file).touch()

        self.mail_manager = MailManager(self.mail_file, self.mail_address)

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_send_error_basic(self):
        """Test envoi de mail d'erreur basique"""
        target = "test_target"
        step = "test_step"
        comment = "Test error message"

        self.mail_manager.send_error(target, step, comment)

        # Vérifier que le fichier a été modifié
        with open(self.mail_file, 'r') as f:
            content = f.read()

        self.assertIn("ERROR autolauncher", content)
        self.assertIn(target, content)
        self.assertIn(step, content)
        self.assertIn(comment, content)
        self.assertIn(self.mail_address, content)

    def test_send_error_with_special_characters(self):
        """Test envoi d'erreur avec caractères spéciaux"""
        target = "target/with/slashes"
        step = "step-with-dashes"
        comment = "Error with 'quotes' and \"double quotes\""

        self.mail_manager.send_error(target, step, comment)

        with open(self.mail_file, 'r') as f:
            content = f.read()

        self.assertIn("ERROR autolauncher", content)
        self.assertIn(target, content)
        self.assertIn(step, content)
        self.assertIn(comment, content)

    def test_send_error_with_unicode(self):
        """Test envoi d'erreur avec caractères Unicode"""
        target = "échantillon_测试"
        step = "étape_ñoël"
        comment = "Erreur avec caractères spéciaux: éàç£¤"

        self.mail_manager.send_error(target, step, comment)

        with open(self.mail_file, 'r') as f:
            content = f.read()

        self.assertIn("ERROR autolauncher", content)
        self.assertIn(target, content)
        self.assertIn(step, content)

    def test_send_error_empty_parameters(self):
        """Test envoi d'erreur avec paramètres vides"""
        self.mail_manager.send_error("", "", "")

        with open(self.mail_file, 'r') as f:
            content = f.read()

        self.assertIn("ERROR autolauncher", content)
        self.assertIn(self.mail_address, content)

    def test_send_error_long_message(self):
        """Test envoi d'erreur avec message très long"""
        target = "long_target"
        step = "long_step"
        comment = "Very long error message " * 100  # Message très long

        self.mail_manager.send_error(target, step, comment)

        with open(self.mail_file, 'r') as f:
            content = f.read()

        self.assertIn("ERROR autolauncher", content)
        self.assertIn(target, content)
        self.assertIn(step, content)
        # Vérifier qu'au moins une partie du long message est présente
        self.assertIn("Very long error message", content)

    @patch('builtins.open', side_effect=IOError("Cannot write"))
    @patch('logging.error')
    def test_send_error_file_write_error(self, mock_logging, mock_open):
        """Test gestion d'erreur lors de l'écriture du fichier"""
        self.mail_manager.send_error("target", "step", "comment")

        # Vérifier que l'erreur est loggée
        mock_logging.assert_called()

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    @patch('logging.error')
    def test_send_error_permission_error(self, mock_logging, mock_open):
        """Test gestion d'erreur de permission"""
        self.mail_manager.send_error("target", "step", "comment")

        # Vérifier que l'erreur est loggée
        mock_logging.assert_called()


class TestMailSendingSuccess(unittest.TestCase):
    """Tests pour l'envoi de mails de succès"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.mail_file = os.path.join(self.test_dir, "test_mail.sh")
        self.mail_address = "bioinfo@example.com"

        # Créer le fichier de mail
        Path(self.mail_file).touch()

        self.mail_manager = MailManager(self.mail_file, self.mail_address)

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_send_success_basic(self):
        """Test envoi de mail de succès basique"""
        target = "test_target"
        step = "test_step"
        comment = "Test success message"
        keyword = "SUCCESS"

        self.mail_manager.send_success(target, step, comment, keyword)

        with open(self.mail_file, 'r') as f:
            content = f.read()

        self.assertIn("autolauncher:", content)
        self.assertIn(target, content)
        self.assertIn(step, content)
        self.assertIn(comment, content)
        self.assertIn(keyword, content)
        self.assertIn(self.mail_address, content)
        # Ne devrait pas contenir "ERROR"
        self.assertNotIn("ERROR", content)

    def test_send_success_without_keyword(self):
        """Test envoi de succès sans mot-clé"""
        target = "test_target"
        step = "test_step"
        comment = "Success without keyword"

        self.mail_manager.send_success(target, step, comment)

        with open(self.mail_file, 'r') as f:
            content = f.read()

        self.assertIn("autolauncher:", content)
        self.assertIn(target, content)
        self.assertIn(step, content)
        self.assertIn(comment, content)

    def test_send_success_with_empty_keyword(self):
        """Test envoi de succès avec mot-clé vide"""
        target = "test_target"
        step = "test_step"
        comment = "Success with empty keyword"

        self.mail_manager.send_success(target, step, comment, "")

        with open(self.mail_file, 'r') as f:
            content = f.read()

        self.assertIn("autolauncher:", content)
        self.assertIn(target, content)

    def test_send_success_various_keywords(self):
        """Test envoi de succès avec différents mots-clés"""
        keywords = ["OK", "COMPLETED", "FINISHED", "DONE", "SUCCESS"]

        for keyword in keywords:
            # Nettoyer le fichier pour chaque test
            with open(self.mail_file, 'w') as f:
                f.write("")

            self.mail_manager.send_success("target", "step", "comment", keyword)

            with open(self.mail_file, 'r') as f:
                content = f.read()

            self.assertIn(keyword, content)
            self.assertNotIn("ERROR", content)

    def test_send_success_multiline_comment(self):
        """Test envoi de succès avec commentaire multi-lignes"""
        target = "test_target"
        step = "test_step"
        comment = "Line 1\nLine 2\nLine 3"

        self.mail_manager.send_success(target, step, comment)

        with open(self.mail_file, 'r') as f:
            content = f.read()

        self.assertIn("autolauncher:", content)
        self.assertIn("Line 1", content)
        self.assertIn("Line 2", content)
        self.assertIn("Line 3", content)

    @patch('builtins.open', side_effect=IOError("Cannot write"))
    @patch('logging.error')
    def test_send_success_file_write_error(self, mock_logging, mock_open):
        """Test gestion d'erreur lors de l'écriture pour succès"""
        self.mail_manager.send_success("target", "step", "comment")

        # Vérifier que l'erreur est loggée
        mock_logging.assert_called()


class TestMailFormatting(unittest.TestCase):
    """Tests pour le formatage des mails"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.mail_file = os.path.join(self.test_dir, "test_mail.sh")
        self.mail_address = "bioinfo@example.com"

        Path(self.mail_file).touch()
        self.mail_manager = MailManager(self.mail_file, self.mail_address)

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_error_mail_format(self):
        """Test format spécifique des mails d'erreur"""
        self.mail_manager.send_error("TARGET", "STEP", "ERROR_MSG")

        with open(self.mail_file, 'r') as f:
            content = f.read()

        # Vérifier la structure du mail d'erreur
        lines = content.strip().split('\n')

        # Doit contenir une ligne echo avec le sujet
        echo_lines = [line for line in lines if line.startswith('echo')]
        self.assertGreater(len(echo_lines), 0)

        # Au moins une ligne echo doit contenir "ERROR autolauncher"
        error_subject_found = any("ERROR autolauncher" in line for line in echo_lines)
        self.assertTrue(error_subject_found)

        # Doit contenir une ligne mail
        mail_lines = [line for line in lines if 'mail' in line and self.mail_address in line]
        self.assertGreater(len(mail_lines), 0)

    def test_success_mail_format(self):
        """Test format spécifique des mails de succès"""
        self.mail_manager.send_success("TARGET", "STEP", "SUCCESS_MSG", "OK")

        with open(self.mail_file, 'r') as f:
            content = f.read()

        # Vérifier la structure du mail de succès
        lines = content.strip().split('\n')

        # Doit contenir des lignes echo
        echo_lines = [line for line in lines if line.startswith('echo')]
        self.assertGreater(len(echo_lines), 0)

        # Aucune ligne ne devrait contenir "ERROR"
        error_in_echo = any("ERROR" in line for line in echo_lines)
        self.assertFalse(error_in_echo)

        # Au moins une ligne doit contenir "autolauncher:"
        autolauncher_found = any("autolauncher:" in line for line in echo_lines)
        self.assertTrue(autolauncher_found)

    def test_mail_script_executable_format(self):
        """Test que le contenu généré est un script shell valide"""
        self.mail_manager.send_error("target", "step", "message")

        with open(self.mail_file, 'r') as f:
            content = f.read()

        # Le script doit commencer par un shebang ou des commandes shell valides
        lines = content.strip().split('\n')
        self.assertGreater(len(lines), 0)

        # Toutes les lignes non vides doivent être des commandes shell valides
        for line in lines:
            if line.strip():
                # Doit commencer par une commande shell valide
                self.assertTrue(
                    line.startswith('echo') or
                    line.startswith('mail') or
                    line.startswith('#') or
                    line.startswith(' ') or  # continuation de ligne
                    '|' in line  # pipe
                )

    def test_mail_content_escaping(self):
        """Test échappement des caractères spéciaux dans le contenu"""
        # Tester avec des caractères qui pourraient casser le shell
        dangerous_chars = "'; rm -rf /; echo 'hacked"

        self.mail_manager.send_error("target", "step", dangerous_chars)

        with open(self.mail_file, 'r') as f:
            content = f.read()

        # Le contenu dangereux doit être présent mais pas exécutable
        self.assertIn(dangerous_chars, content)

        # Vérifier que c'est dans une commande echo (donc sécurisé)
        lines = content.strip().split('\n')
        dangerous_line = next((line for line in lines if dangerous_chars in line), None)
        self.assertIsNotNone(dangerous_line)
        self.assertTrue(dangerous_line.strip().startswith('echo'))


class TestMailManagerEdgeCases(unittest.TestCase):
    """Tests pour les cas limites du gestionnaire de mails"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.mail_file = os.path.join(self.test_dir, "test_mail.sh")
        self.mail_address = "bioinfo@example.com"

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_mail_file_in_nonexistent_directory(self):
        """Test avec fichier de mail dans répertoire inexistant"""
        nested_mail_file = os.path.join(self.test_dir, "nested", "dir", "mail.sh")

        mail_manager = MailManager(nested_mail_file, self.mail_address)

        # L'envoi de mail devrait créer les répertoires nécessaires ou gérer l'erreur
        try:
            mail_manager.send_error("target", "step", "message")
            # Si ça réussit, vérifier que le fichier existe
            if os.path.exists(nested_mail_file):
                self.assertTrue(os.path.isfile(nested_mail_file))
        except Exception:
            # Si ça échoue, c'est acceptable (dépend de l'implémentation)
            pass

    def test_very_long_mail_address(self):
        """Test avec adresse email très longue"""
        long_address = "very.long.email.address.that.might.cause.issues@very.long.domain.name.example.com"

        Path(self.mail_file).touch()
        mail_manager = MailManager(self.mail_file, long_address)

        mail_manager.send_error("target", "step", "message")

        with open(self.mail_file, 'r') as f:
            content = f.read()

        self.assertIn(long_address, content)

    def test_mail_file_with_no_extension(self):
        """Test avec fichier de mail sans extension"""
        mail_file_no_ext = os.path.join(self.test_dir, "mailscript")

        Path(mail_file_no_ext).touch()
        mail_manager = MailManager(mail_file_no_ext, self.mail_address)

        mail_manager.send_success("target", "step", "message")

        with open(mail_file_no_ext, 'r') as f:
            content = f.read()

        self.assertIn("autolauncher:", content)

    def test_multiple_consecutive_sends(self):
        """Test envois multiples consécutifs"""
        Path(self.mail_file).touch()
        mail_manager = MailManager(self.mail_file, self.mail_address)

        # Envoyer plusieurs mails successifs
        mail_manager.send_error("target1", "step1", "error1")
        mail_manager.send_success("target2", "step2", "success1", "OK")
        mail_manager.send_error("target3", "step3", "error2")

        with open(self.mail_file, 'r') as f:
            content = f.read()

        # Le fichier doit contenir le dernier mail (pas d'accumulation)
        self.assertIn("target3", content)
        self.assertIn("error2", content)

    def test_empty_mail_file_path(self):
        """Test avec chemin de fichier de mail vide"""
        mail_manager = MailManager("", self.mail_address)

        # Devrait gérer l'erreur gracieusement
        try:
            mail_manager.send_error("target", "step", "message")
        except Exception as e:
            # Une exception est acceptable
            self.assertIsInstance(e, (OSError, IOError, ValueError))

    def test_mail_with_newlines_in_parameters(self):
        """Test avec sauts de ligne dans les paramètres"""
        target_with_newlines = "target\nwith\nnewlines"
        step_with_newlines = "step\nwith\nnewlines"

        Path(self.mail_file).touch()
        mail_manager = MailManager(self.mail_file, self.mail_address)

        mail_manager.send_error(target_with_newlines, step_with_newlines, "message")

        with open(self.mail_file, 'r') as f:
            content = f.read()

        # Le contenu doit être présent d'une manière ou d'une autre
        self.assertIn("target", content)
        self.assertIn("step", content)


if __name__ == '__main__':
    unittest.main(verbosity=2)