#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Point d'entrée principal de l'autolauncher.
Orchestre les différentes étapes du pipeline bioinformatique.
"""

import sys
import os

import argparse
import logging
import signal
import atexit

# pylint: disable=E0401
from config import Config
from events import create_events_register
from mail import MailManager
from lock import LockManager
from utils import get_or_create_file
from subproccess_runner import PipelineRunner

# Imports des steps en dernier
from steps.concat import ConcatStep
from steps.organize import OrganizeStep
from steps.infofile import InfofileStep
from steps.analysis import AnalysisStep
from steps.check import CheckStep

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


class AutoLauncher:
    """
    Orchestrateur principal de l'autolauncher.
    Gère le cycle de vie et l'exécution des différentes étapes.
    """
    
    def __init__(self, args):
        """
        Initialise l'autolauncher.
        
        Args:
            args: Arguments de la ligne de commande
        """
        self.args = args
        self.input_dir = args.in_dir
        self.current_step = "autolauncher_setup"
        self.need_unlock = True
        
        # Initialisation du logging
        self._setup_logging()
        
        # Chargement de la configuration
        self.config = Config()
        
        # Préparation des fichiers
        self.event_file = self._prepare_file(
            args.eventFile, Config.DEFAULT_EVENT_FILE, "événements"
        )
        self.mail_file = self._prepare_file(
            args.mailFile, Config.DEFAULT_MAIL_FILE, "notifications mail"
        )
        
        # Initialisation des composants
        self.events = create_events_register(self.event_file)
        self.mail = MailManager(self.mail_file, self.config.mail_bioinfo)
        self.lock = LockManager(self.input_dir)
        self.pipeline = PipelineRunner(self.config)
        
        # Enregistrement des handlers de sortie
        self._register_exit_handlers()
    
    def _setup_logging(self):
        """Configure le système de logging."""
        logging.basicConfig(
            filename=self.args.logFile,
            filemode='a',
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s - %(message)s'
        )
        logging.info("=== DÉBUT DU CYCLE AUTOLAUNCHER ===")
    
    def _prepare_file(self, arg_path: str, default: str, category: str) -> str:
        """
        Prépare un fichier (création si nécessaire).
        
        Args:
            arg_path: Chemin passé en argument
            default: Nom par défaut
            category: Catégorie du fichier
        
        Returns:
            Chemin du fichier
        """
        return get_or_create_file(arg_path, default, self.input_dir, category)
    
    def _register_exit_handlers(self):
        """Enregistre les handlers de sortie propre du programme."""
        atexit.register(self._cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, _):     # _ = frame
        """Handler pour les signaux d'interruption."""
        msg = (
            f"Signal d'interruption SIGTERM ({sig}) reçu pendant l'étape "
            f"{self.current_step}. Arrêt prématuré."
        )
        logging.error(msg)
        self.mail.send_error("signal_interruption", self.current_step, msg)
        sys.exit(1)
    
    def _cleanup(self):
        """Nettoyage en fin d'exécution."""
        logging.debug("Procédure de sortie...")
        
        # Vérification et sauvegarde du registre d'événements
        if hasattr(self, 'events'):
            self.events.test_integrity()
            
            if self.events.registration_fail:
                msg = (
                    "Problème avec le registre d'événements. "
                    "Des erreurs peuvent ne pas être enregistrées correctement."
                )
                logging.error(msg)
                
                count_before = self.events.count(
                    "registration_fail", "-", "registration_fail"
                )
                if count_before == 0:
                    self.mail.send_error(
                        "autolauncher_events",
                        "registration",
                        msg
                    )
            
            self.events.save()
        
        # Libération du verrou
        if self.need_unlock and hasattr(self, 'lock'):
            self.lock.release()
        
        logging.info("=== FIN DU CYCLE AUTOLAUNCHER ===")
    
    def run(self) -> int:
        """
        Exécute l'autolauncher selon l'étape demandée.
        
        Returns:
            Code de sortie (0 = succès, 1 = erreur)
        """
        try:
            # Acquisition du verrou
            if not self.lock.acquire():
                logging.warning("Un autre processus est en cours. Arrêt.")
                self.events.add(self.input_dir, "autolaunch.lock", "lockfile_found")
                self.need_unlock = False
                return 0
            
            self.events.delete(self.input_dir, "autolaunch.lock", "lockfile_found")
            
            # Exécution de l'étape demandée
            success = self._execute_step()
            
            return 0 if success else 1
        
        except (OSError, ValueError) as e:
            logging.exception("Erreur attendue: %s", e)
            return 1
        # Removed general Exception catch to avoid catching too broad exceptions.
    
    def _execute_step(self) -> bool:
        """
        Exécute l'étape spécifiée en ligne de commande.
        
        Returns:
            True si succès
        """
        if self.args.concat:
            self.current_step = "concat"
            step = ConcatStep(self.config, self.events, self.mail, self.pipeline)
            return step.execute(self.input_dir)
        
        elif self.args.organize:
            self.current_step = "organize"
            step = OrganizeStep(self.config, self.events, self.mail, self.pipeline)
            return step.execute(self.input_dir)
        
        elif self.args.infofile:
            self.current_step = "infofile"
            step = InfofileStep(self.config, self.events, self.mail, self.pipeline)
            return step.execute(self.input_dir)
        
        elif self.args.analysis:
            self.current_step = "analysis"
            step = AnalysisStep(self.config, self.events, self.mail, self.pipeline)
            return step.execute(self.input_dir)
        
        elif self.args.check:
            self.current_step = "check"
            step = CheckStep(self.config, self.events, self.mail, self.pipeline)
            return step.execute(self.input_dir)
        
        else:
            logging.error("Aucune étape spécifiée")
            return False


def parse_arguments():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description=(
            "Lance automatiquement les différentes étapes du pipeline GAD "
            "(pour données NovaSeq X) selon les conditions requises."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Arguments requis
    parser.add_argument(
        "-d", "--directory",
        dest="in_dir",
        required=True,
        help="Chemin complet du répertoire à examiner sur le cluster"
    )
    
    # Arguments avec valeurs par défaut
    parser.add_argument(
        "-s", "--server",
        dest="labkeyserver",
        nargs='?',
        help="Adresse du serveur LabKey (optionnel, surchargé par config)"
    )
    
    parser.add_argument(
        "-l", "--log",
        dest="logFile",
        default=Config.DEFAULT_LOG_FILE,
        help="Fichier de log de l'autolauncher"
    )
    
    parser.add_argument(
        "-e", "--events",
        dest="eventFile",
        default=Config.DEFAULT_EVENT_FILE,
        help="Fichier d'enregistrement des événements"
    )
    
    parser.add_argument(
        "-m", "--mail",
        dest="mailFile",
        default=Config.DEFAULT_MAIL_FILE,
        help="Fichier script shell pour les notifications mail"
    )
    
    # Flags mutuellement exclusifs (obligatoire)
    flags_group = parser.add_mutually_exclusive_group(required=True)
    
    flags_group.add_argument(
        "--concat",
        action="store_const",
        const=1,
        help="Étape de concaténation des FASTQ"
    )
    
    flags_group.add_argument(
        "--organize",
        action="store_const",
        const=1,
        help="Étape de création des dossiers d'échantillons"
    )
    
    flags_group.add_argument(
        "--infofile",
        action="store_const",
        const=1,
        help="Étape de création du fichier d'information"
    )
    
    flags_group.add_argument(
        "--analysis",
        action="store_const",
        const=1,
        help="Étape de lancement des analyses"
    )
    
    flags_group.add_argument(
        "--check",
        action="store_const",
        const=1,
        help="Étape de vérification et suivi des analyses"
    )
    
    return parser.parse_args()


def main():
    """Point d'entrée principal."""
    args = parse_arguments()
    launcher = AutoLauncher(args)
    sys.exit(launcher.run())


if __name__ == "__main__":
    main()