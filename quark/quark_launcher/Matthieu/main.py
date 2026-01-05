#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
main.py

Description:
Point d'entrée principal de l'autolauncher.
Orchestre les différentes étapes du pipeline bioinformatique.

Auteur: Matthieu Damien
Creation Date: 2025-10-07
Dernière modification: 2025-10-31
Commentaires:
- OSError: [Errno 30] Read-only file system: '/app/autolauncher.log' 
    Cause : Le conteneur Singularity monte /app/ en lecture seule, 
    donc impossible de créer des fichiers de log
"""

import sys
import os
import traceback

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
from subprocess_runner import PipelineRunner

# Imports des steps en dernier
from steps.concat import ConcatStep
from steps.organize import OrganizeStep
from steps.infofile import InfofileStep
from steps.analysis import AnalysisStep
from steps.check import CheckStep

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


# ============================================================================
# Gestion globale des exceptions non gérées
# ============================================================================
def _global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Capture et logue toutes les exceptions non gérées.
    Inspiré de l'ancien code (auto_launcher_novaseqx.py lignes 114-119).

    Args:
        exc_type: Type de l'exception
        exc_value: Valeur de l'exception
        exc_traceback: Traceback de l'exception
    """
    # Ne pas intercepter KeyboardInterrupt (Ctrl+C)
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Formater le traceback
    tb = traceback.extract_tb(exc_traceback)
    tb_formatted = "".join(traceback.format_list(tb))

    # Logger l'exception
    logging.error(
        "Une exception inattendue de classe \"%s\" s'est produite. "
        "Traceback:\n%s%s",
        exc_type.__name__,
        tb_formatted,
        exc_value
    )

# Installer le gestionnaire d'exceptions global
sys.excepthook = _global_exception_handler


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

        # Chargement de la configuration EN PREMIER (avec override CLI pour LabKey si fourni)
        labkey_override = args.labkeyserver if hasattr(args, 'labkeyserver') and args.labkeyserver else None
        test_mode = args.test if hasattr(args, 'test') else False

        self.config = Config(
            args.configFile,
            labkey_server_override=labkey_override,
            test_mode=test_mode
        )

        # Déterminer le répertoire de base pour les logs
        # Si main_dir est défini dans config, créer un dossier logs dedans
        # Sinon, utiliser input_dir comme avant (fallback)
        if hasattr(self.config, 'main_dir') and self.config.main_dir:
            logs_base_dir = os.path.join(self.config.main_dir, 'logs')
            os.makedirs(logs_base_dir, mode=0o770, exist_ok=True)
        else:
            logs_base_dir = self.input_dir

        # Résoudre le chemin du fichier de log
        # Si le chemin est relatif (défaut), le placer dans logs_base_dir
        # Si le chemin est absolu, l'utiliser tel quel
        if not os.path.isabs(args.logFile):
            log_file = os.path.join(logs_base_dir, args.logFile)
        else:
            log_file = args.logFile

        # Initialisation du logging (avec verbose si demandé)
        self._setup_logging(log_file, verbose=args.verbose)

        # Log si mode test activé
        if test_mode:
            logging.info("Mode TEST activé - Utilisation de: %s", self.config.config_file)

        # Log si override LabKey utilisé
        if labkey_override:
            logging.info("Override CLI LabKey activé: %s (config=%s)",
                        self.config.labkey_address, labkey_override)

        # Préparation des fichiers (events et mail) dans logs_base_dir
        self.event_file = get_or_create_file(
            args.eventFile, Config.DEFAULT_EVENT_FILE, logs_base_dir, "événements"
        )
        self.mail_file = get_or_create_file(
            args.mailFile, Config.DEFAULT_MAIL_FILE, logs_base_dir, "notifications mail"
        )

        # Initialisation des composants
        self.events = create_events_register(self.event_file)
        self.mail = MailManager(self.mail_file, self.config.mail_bioinfo) #type: ignore
        self.lock = LockManager(self.input_dir)
        self.pipeline = PipelineRunner(self.config)

        # Enregistrement des handlers de sortie
        self._register_exit_handlers()

    def _setup_logging(self, log_file: str, verbose: bool = False):
        """
        Configure le système de logging.

        Args:
            log_file: Chemin absolu vers le fichier de log
            verbose: Si True, affiche également les logs sur la console
        """
        # Créer le répertoire parent si nécessaire
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, mode=0o770, exist_ok=True)

        # Configuration du logger root
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Handler pour le fichier (toujours actif)
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Handler pour la console (seulement si --verbose)
        if verbose:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)  # Console : INFO et plus
            console_formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

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

        # Le fichier de script mail est prêt pour exécution externe
        # (comme dans l'approche de Valentin - auto_launcher_novaseqx.py)
        if hasattr(self, 'mail') and os.path.exists(self.mail_file):
            logging.info("Fichier de script mail préparé: %s (à exécuter manuellement)", self.mail_file)

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

        except Exception as e:
            logging.exception("Erreur inattendue: %s", e)
            self.mail.send_error("critical", self.current_step, f"Crash inattendu: {e}")
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
        help="Adresse du serveur LabKey (surcharge la valeur dans config.csv si fourni)"
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

    parser.add_argument(
        "-cf", "--configfile",
        dest="configFile",
        default=None,
        help="Fichier de configuration (si non fourni, utilise config.csv ou config_dev.csv selon le mode)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        dest="verbose",
        help="Afficher les logs sur la console en plus du fichier"
    )

    parser.add_argument(
        "-t", "--test",
        action="store_true",
        dest="test",
        help="Mode TEST : utilise config_dev.csv au lieu de config.csv"
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
