#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests unitaires pour main.py - Point d'entrée principal de l'autolauncher
"""

import unittest
import logging
from unittest.mock import Mock, patch, MagicMock, call
import os
import sys
import tempfile
import shutil
import argparse
from pathlib import Path

# Ajouter le chemin du module parent pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Maintenant on peut importer sans problème

import main # pylint: disable=E0401
from main import parse_arguments, AutoLauncher # pylint: disable=E0401


class TestArgumentParsing(unittest.TestCase):
    """Tests pour l'analyse des arguments de ligne de commande"""

    def test_parse_arguments_concat(self):
        """Test parsing des arguments pour l'étape concat"""
        test_args = ['main.py', '-d', '/test/dir', '--concat']
        with patch('sys.argv', test_args):
            args = parse_arguments()
            self.assertEqual(args.in_dir, '/test/dir')
            self.assertEqual(args.concat, 1)
            self.assertIsNone(args.organize)
            self.assertIsNone(args.infofile)
            self.assertIsNone(args.analysis)
            self.assertIsNone(args.check)

    def test_parse_arguments_organize(self):
        """Test parsing des arguments pour l'étape organize"""
        test_args = ['main.py', '-d', '/test/dir', '--organize']
        with patch('sys.argv', test_args):
            args = parse_arguments()
            self.assertEqual(args.in_dir, '/test/dir')
            self.assertIsNone(args.concat)
            self.assertEqual(args.organize, 1)

    def test_parse_arguments_infofile(self):
        """Test parsing des arguments pour l'étape infofile"""
        test_args = ['main.py', '-d', '/test/dir', '--infofile']
        with patch('sys.argv', test_args):
            args = parse_arguments()
            self.assertEqual(args.in_dir, '/test/dir')
            self.assertEqual(args.infofile, 1)

    def test_parse_arguments_analysis(self):
        """Test parsing des arguments pour l'étape analysis"""
        test_args = ['main.py', '-d', '/test/dir', '--analysis']
        with patch('sys.argv', test_args):
            args = parse_arguments()
            self.assertEqual(args.in_dir, '/test/dir')
            self.assertEqual(args.analysis, 1)

    def test_parse_arguments_check(self):
        """Test parsing des arguments pour l'étape check"""
        test_args = ['main.py', '-d', '/test/dir', '--check']
        with patch('sys.argv', test_args):
            args = parse_arguments()
            self.assertEqual(args.in_dir, '/test/dir')
            self.assertEqual(args.check, 1)

    def test_parse_arguments_custom_log(self):
        """Test parsing avec fichier de log personnalisé"""
        test_args = ['main.py', '-d', '/test/dir', '--concat', '-l', 'custom.log']
        with patch('sys.argv', test_args):
            args = parse_arguments()
            self.assertEqual(args.logFile, 'custom.log')

    def test_parse_arguments_all_optional(self):
        """Test parsing avec tous les arguments optionnels"""
        test_args = [
            'main.py', '-d', '/test/dir', '--concat',
            '-l', 'test.log', '-e', 'test.events', '-m', 'test.sh',
            '-s', 'test.server'
        ]
        with patch('sys.argv', test_args):
            args = parse_arguments()
            self.assertEqual(args.in_dir, '/test/dir')
            self.assertEqual(args.logFile, 'test.log')
            self.assertEqual(args.eventFile, 'test.events')
            self.assertEqual(args.mailFile, 'test.sh')
            self.assertEqual(args.labkeyserver, 'test.server')


class TestAutoLauncherInitialization(unittest.TestCase):
    """Tests pour l'initialisation de la classe AutoLauncher"""

    def setUp(self):
        logging.basicConfig(
            level=logging.ERROR,  # Seulement les erreurs pour ne pas polluer
            format='%(levelname)s - %(message)s'
        )
        
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.mock_args = Mock()
        self.mock_args.in_dir = self.test_dir
        self.mock_args.logFile = os.path.join(self.test_dir, "test.log")
        self.mock_args.eventFile = os.path.join(self.test_dir, "test.events")
        self.mock_args.mailFile = os.path.join(self.test_dir, "test_mail.sh")
        self.mock_args.labkeyserver = None
        self.mock_args.concat = 1
        self.mock_args.organize = None
        self.mock_args.infofile = None
        self.mock_args.analysis = None
        self.mock_args.check = None

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_autolauncher_initialization(self, mock_config, mock_events, mock_mail,
                                        mock_lock, mock_pipeline, *_):
        """Test initialisation de AutoLauncher"""
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        mock_events_instance = Mock()
        mock_events.return_value = mock_events_instance
        
        launcher = AutoLauncher(self.mock_args)

        self.assertEqual(launcher.input_dir, self.test_dir)
        self.assertEqual(launcher.current_step, "autolauncher_setup")
        self.assertTrue(launcher.need_unlock)
        
        mock_config.assert_called_once()
        mock_events.assert_called_once()
        mock_mail.assert_called_once()
        mock_lock.assert_called_once()
        mock_pipeline.assert_called_once()

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    @patch('logging.basicConfig')
    def test_setup_logging(self, mock_logging, mock_config, mock_events, mock_mail,
                          mock_lock, mock_pipeline, *_):
        """Test configuration du logging"""
        launcher = AutoLauncher(self.mock_args)

        mock_logging.assert_called_once()
        call_kwargs = mock_logging.call_args[1]
        self.assertEqual(call_kwargs['filename'], self.mock_args.logFile)
        self.assertEqual(call_kwargs['filemode'], 'a')
        self.assertEqual(call_kwargs['level'], logging.DEBUG)


class TestAutoLauncherExecution(unittest.TestCase):
    """Tests pour l'exécution des étapes de AutoLauncher"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.mock_args = Mock()
        self.mock_args.in_dir = self.test_dir
        self.mock_args.logFile = os.path.join(self.test_dir, "test.log")
        self.mock_args.eventFile = os.path.join(self.test_dir, "test.events")
        self.mock_args.mailFile = os.path.join(self.test_dir, "test_mail.sh")
        self.mock_args.labkeyserver = None

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _set_step(self, step_name):
        """Configure les args pour une étape donnée"""
        for step in ['concat', 'organize', 'infofile', 'analysis', 'check']:
            setattr(self.mock_args, step, 1 if step == step_name else None)

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_execute_concat_step(self, mock_config, mock_events, mock_mail,
                                 mock_lock, mock_pipeline, mock_concat_step, *_):
        """Test exécution de l'étape concat"""
        self._set_step('concat')
        
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        mock_lock_instance.acquire.return_value = True
        
        mock_step_instance = Mock()
        mock_concat_step.return_value = mock_step_instance
        mock_step_instance.execute.return_value = True

        launcher = AutoLauncher(self.mock_args)
        result = launcher.run()

        self.assertEqual(result, 0)
        self.assertEqual(launcher.current_step, "concat")
        mock_lock_instance.acquire.assert_called_once()
        mock_concat_step.assert_called_once()
        mock_step_instance.execute.assert_called_once_with(self.test_dir)

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_execute_organize_step(self, mock_config, mock_events, mock_mail,
                                   mock_lock, mock_pipeline, mock_concat, mock_organize, *_):
        """Test exécution de l'étape organize"""
        self._set_step('organize')
        
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        mock_lock_instance.acquire.return_value = True
        
        mock_step_instance = Mock()
        mock_organize.return_value = mock_step_instance
        mock_step_instance.execute.return_value = True

        launcher = AutoLauncher(self.mock_args)
        result = launcher.run()

        self.assertEqual(result, 0)
        self.assertEqual(launcher.current_step, "organize")
        mock_organize.assert_called_once()

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_execute_infofile_step(self, mock_config, mock_events, mock_mail,
                                   mock_lock, mock_pipeline, mock_concat, mock_organize,
                                   mock_infofile, *_):
        """Test exécution de l'étape infofile"""
        self._set_step('infofile')
        
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        mock_lock_instance.acquire.return_value = True
        
        mock_step_instance = Mock()
        mock_infofile.return_value = mock_step_instance
        mock_step_instance.execute.return_value = True

        launcher = AutoLauncher(self.mock_args)
        result = launcher.run()

        self.assertEqual(result, 0)
        self.assertEqual(launcher.current_step, "infofile")
        mock_infofile.assert_called_once()

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_execute_analysis_step(self, mock_config, mock_events, mock_mail,
                                   mock_lock, mock_pipeline, mock_concat, mock_organize,
                                   mock_infofile, mock_analysis, *_):
        """Test exécution de l'étape analysis"""
        self._set_step('analysis')
        
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        mock_lock_instance.acquire.return_value = True
        
        mock_step_instance = Mock()
        mock_analysis.return_value = mock_step_instance
        mock_step_instance.execute.return_value = True

        launcher = AutoLauncher(self.mock_args)
        result = launcher.run()

        self.assertEqual(result, 0)
        self.assertEqual(launcher.current_step, "analysis")
        mock_analysis.assert_called_once()

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_execute_check_step(self, mock_config, mock_events, mock_mail,
                                mock_lock, mock_pipeline, mock_concat, mock_organize,
                                mock_infofile, mock_analysis, mock_check):
        """Test exécution de l'étape check"""
        self._set_step('check')
        
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        mock_lock_instance.acquire.return_value = True
        
        mock_step_instance = Mock()
        mock_check.return_value = mock_step_instance
        mock_step_instance.execute.return_value = True

        launcher = AutoLauncher(self.mock_args)
        result = launcher.run()

        self.assertEqual(result, 0)
        self.assertEqual(launcher.current_step, "check")
        mock_check.assert_called_once()

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_lock_already_acquired(self, mock_config, mock_events, mock_mail,
                                   mock_lock, mock_pipeline, *_):
        """Test quand le verrou est déjà acquis"""
        self._set_step('concat')
        
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        mock_lock_instance.acquire.return_value = False
        
        mock_events_instance = Mock()
        mock_events.return_value = mock_events_instance

        launcher = AutoLauncher(self.mock_args)
        result = launcher.run()

        self.assertEqual(result, 0)
        self.assertFalse(launcher.need_unlock)
        mock_events_instance.add.assert_called_once()
        # Vérifier que delete a été appelé après
        mock_events_instance.delete.assert_not_called()

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_execute_step_failure(self, mock_config, mock_events, mock_mail,
                                  mock_lock, mock_pipeline, mock_concat_step, *_):
        """Test échec de l'exécution d'une étape"""
        self._set_step('concat')
        
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        mock_lock_instance.acquire.return_value = True
        
        mock_step_instance = Mock()
        mock_concat_step.return_value = mock_step_instance
        mock_step_instance.execute.return_value = False  # Échec

        launcher = AutoLauncher(self.mock_args)
        result = launcher.run()

        self.assertEqual(result, 1)  # Code d'erreur

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_no_step_specified(self, mock_config, mock_events, mock_mail,
                               mock_lock, mock_pipeline, *_):
        """Test sans étape spécifiée"""
        # Toutes les étapes à None
        for step in ['concat', 'organize', 'infofile', 'analysis', 'check']:
            setattr(self.mock_args, step, None)
        
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        mock_lock_instance.acquire.return_value = True

        launcher = AutoLauncher(self.mock_args)
        result = launcher.run()

        self.assertEqual(result, 1)  # Échec


class TestAutoLauncherCleanup(unittest.TestCase):
    """Tests pour le nettoyage et la gestion des erreurs"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.mock_args = Mock()
        self.mock_args.in_dir = self.test_dir
        self.mock_args.logFile = os.path.join(self.test_dir, "test.log")
        self.mock_args.eventFile = os.path.join(self.test_dir, "test.events")
        self.mock_args.mailFile = os.path.join(self.test_dir, "test_mail.sh")
        self.mock_args.labkeyserver = None
        self.mock_args.concat = 1
        for step in ['organize', 'infofile', 'analysis', 'check']:
            setattr(self.mock_args, step, None)

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_cleanup_with_registration_fail(self, mock_config, mock_events, mock_mail,
                                           mock_lock, mock_pipeline, *_):
        """Test nettoyage quand il y a un échec d'enregistrement"""
        mock_events_instance = Mock()
        mock_events.return_value = mock_events_instance
        mock_events_instance.registration_fail = True
        mock_events_instance.count.return_value = 0
        
        mock_mail_instance = Mock()
        mock_mail.return_value = mock_mail_instance

        launcher = AutoLauncher(self.mock_args)
        launcher._cleanup()

        mock_events_instance.test_integrity.assert_called_once()
        mock_events_instance.save.assert_called_once()
        mock_mail_instance.send_error.assert_called_once()

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    @patch('sys.exit')
    def test_signal_handler(self, mock_exit, mock_config, mock_events, mock_mail,
                           mock_lock, mock_pipeline, *_):
        """Test gestionnaire de signaux"""
        mock_mail_instance = Mock()
        mock_mail.return_value = mock_mail_instance

        launcher = AutoLauncher(self.mock_args)
        launcher._signal_handler(15, None)

        mock_mail_instance.send_error.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_cleanup_releases_lock(self, mock_config, mock_events, mock_mail,
                                   mock_lock, mock_pipeline, *_):
        """Test que le cleanup libère le verrou"""
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        
        mock_events_instance = Mock()
        mock_events.return_value = mock_events_instance
        mock_events_instance.registration_fail = False

        launcher = AutoLauncher(self.mock_args)
        launcher.need_unlock = True
        launcher._cleanup()

        mock_lock_instance.release.assert_called_once()

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_cleanup_doesnt_release_lock_when_not_needed(self, mock_config, mock_events,
                                                         mock_mail, mock_lock, mock_pipeline, *_):
        """Test que le cleanup ne libère pas le verrou si need_unlock est False"""
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        
        mock_events_instance = Mock()
        mock_events.return_value = mock_events_instance
        mock_events_instance.registration_fail = False

        launcher = AutoLauncher(self.mock_args)
        launcher.need_unlock = False
        launcher._cleanup()

        mock_lock_instance.release.assert_not_called()


class TestMainFunction(unittest.TestCase):
    """Tests pour la fonction main()"""

    @patch('main.AutoLauncher')
    @patch('main.parse_arguments')
    @patch('sys.exit')
    def test_main_success(self, mock_exit, mock_parse, mock_launcher_class):
        """Test fonction main avec succès"""
        mock_args = Mock()
        mock_parse.return_value = mock_args
        
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher
        mock_launcher.run.return_value = 0

        main.main()

        mock_parse.assert_called_once()
        mock_launcher_class.assert_called_once_with(mock_args)
        mock_launcher.run.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('main.AutoLauncher')
    @patch('main.parse_arguments')
    @patch('sys.exit')
    def test_main_failure(self, mock_exit, mock_parse, mock_launcher_class):
        """Test fonction main avec échec"""
        mock_args = Mock()
        mock_parse.return_value = mock_args
        
        mock_launcher = Mock()
        mock_launcher_class.return_value = mock_launcher
        mock_launcher.run.return_value = 1

        main.main()

        mock_exit.assert_called_once_with(1)


class TestPrepareFile(unittest.TestCase):
    """Tests pour la méthode _prepare_file"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.mock_args = Mock()
        self.mock_args.in_dir = self.test_dir
        self.mock_args.logFile = "test.log"
        self.mock_args.eventFile = "test.events"
        self.mock_args.mailFile = "test_mail.sh"
        self.mock_args.labkeyserver = None
        self.mock_args.concat = 1
        for step in ['organize', 'infofile', 'analysis', 'check']:
            setattr(self.mock_args, step, None)

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    @patch('main.get_or_create_file')
    def test_prepare_file_with_default(self, mock_get_file, mock_config, mock_events,
                                       mock_mail, mock_lock, mock_pipeline, *_):
        """Test préparation d'un fichier avec nom par défaut"""
        mock_get_file.return_value = os.path.join(self.test_dir, "test.log")
        
        launcher = AutoLauncher(self.mock_args)
        
        # Vérifier que get_or_create_file a été appelé
        self.assertTrue(mock_get_file.called)


class TestErrorHandling(unittest.TestCase):
    """Tests pour la gestion d'erreurs"""

    def setUp(self):
        """Préparation avant chaque test"""
        self.test_dir = tempfile.mkdtemp()
        self.mock_args = Mock()
        self.mock_args.in_dir = self.test_dir
        self.mock_args.logFile = os.path.join(self.test_dir, "test.log")
        self.mock_args.eventFile = os.path.join(self.test_dir, "test.events")
        self.mock_args.mailFile = os.path.join(self.test_dir, "test_mail.sh")
        self.mock_args.labkeyserver = None
        self.mock_args.concat = 1
        for step in ['organize', 'infofile', 'analysis', 'check']:
            setattr(self.mock_args, step, None)

    def tearDown(self):
        """Nettoyage après chaque test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_oserror_handling(self, mock_config, mock_events, mock_mail,
                              mock_lock, mock_pipeline, mock_concat, *_):
        """Test gestion des OSError"""
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        mock_lock_instance.acquire.return_value = True
        
        mock_step_instance = Mock()
        mock_concat.return_value = mock_step_instance
        mock_step_instance.execute.side_effect = OSError("Test error")

        launcher = AutoLauncher(self.mock_args)
        result = launcher.run()

        self.assertEqual(result, 1)

    @patch('main.CheckStep')
    @patch('main.AnalysisStep')
    @patch('main.InfofileStep')
    @patch('main.OrganizeStep')
    @patch('main.ConcatStep')
    @patch('main.PipelineRunner')
    @patch('main.LockManager')
    @patch('main.MailManager')
    @patch('main.create_events_register')
    @patch('main.Config')
    def test_valueerror_handling(self, mock_config, mock_events, mock_mail,
                                 mock_lock, mock_pipeline, mock_concat, *_):
        """Test gestion des ValueError"""
        mock_lock_instance = Mock()
        mock_lock.return_value = mock_lock_instance
        mock_lock_instance.acquire.return_value = True
        
        mock_step_instance = Mock()
        mock_concat.return_value = mock_step_instance
        mock_step_instance.execute.side_effect = ValueError("Test error")

        launcher = AutoLauncher(self.mock_args)
        result = launcher.run()

        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)