#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Étape de vérification et suivi des analyses.
Vérifie l'état des analyses, détecte les erreurs et surveille l'archivage.
"""

import sys
import os
import glob
import re
import logging

from .base import BaseStep
# pylint: disable-next=E0401
from utils import file_exists, parse_status_file


class CheckStep(BaseStep):
    """
    Étape de vérification des analyses et archivage.
    Vérifie le statut des analyses, détecte les échecs et surveille l'archivage.
    """
    
    EVENT_COUNT_LIMIT = 50  # Limite avant alerte
    EVENT_COUNT_LIMIT_STUCK = 500  # Limite pour analyses bloquées
    
    def execute(self, input_dir: str) -> bool:
        """
        Exécute la vérification des analyses.
        
        Args:
            input_dir: Répertoire contenant les analyses
        
        Returns:
            True si succès
        """
        self.log_start(input_dir)
        
        # Récupération des dossiers d'analyse
        analysis_dirs = self._get_analysis_directories(input_dir)
        
        if not analysis_dirs:
            logging.info("Aucun dossier d'analyse trouvé")
            self.log_end(True)
            return True
        
        # Vérification de chaque analyse
        for analysis_dir in analysis_dirs:
            family = os.path.basename(analysis_dir)
            self._check_analysis(analysis_dir, family)
        
        # Contrôle du nombre d'événements
        self._check_event_counts()
        
        self.log_end(True)
        return True
    
    def _get_analysis_directories(self, input_dir: str) -> list:
        """
        Récupère les dossiers d'analyse (PED* et dij*).
        
        Args:
            input_dir: Répertoire à scanner
        
        Returns:
            Liste des chemins des dossiers d'analyse
        """
        ped_dirs = glob.glob(os.path.join(input_dir, "PED*"))
        dij_dirs = glob.glob(os.path.join(input_dir, "dij*"))
        
        analysis_dirs = [
            d for d in (ped_dirs + dij_dirs)
            if os.path.isdir(d)
        ]
        
        return analysis_dirs
    
    def _check_analysis(self, analysis_dir: str, family: str) -> None:
        """
        Vérifie une analyse complète.
        
        Args:
            analysis_dir: Chemin du dossier d'analyse
            family: Nom de la famille
        """
        logging.info(f"Vérification de l'analyse: {family}")
        
        # Vérification du dispatch
        dispatched_samples = self._check_dispatch(analysis_dir, family)
        
        if not dispatched_samples:
            # Pas d'échantillons dispatchés = analyse pas encore commencée
            return
        
        # Vérification de l'état de l'analyse
        analysis_ended, analysis_failed = self._check_analysis_status(
            analysis_dir, family, dispatched_samples
        )
        
        # Vérification de l'archivage si analyse terminée
        if analysis_ended:
            self._check_archiving(analysis_dir, family, dispatched_samples)
    
    def _check_dispatch(self, analysis_dir: str, family: str) -> list:
        """
        Vérifie le dispatch des échantillons.
        
        Args:
            analysis_dir: Chemin du dossier d'analyse
            family: Nom de la famille
        
        Returns:
            Liste des échantillons dispatchés
        """
        sample_dirs = glob.glob(os.path.join(analysis_dir, "dij*"))
        dispatched = [
            os.path.basename(d) for d in sample_dirs
            if os.path.isdir(d)
        ]
        
        if dispatched:
            logging.info(
                f"{family}: {len(dispatched)} échantillon(s) dispatché(s) - "
                f"{', '.join(dispatched)}"
            )
            
            happened = self.events.add_and_count(
                analysis_dir,
                ", ".join(dispatched),
                "dispatch_ok"
            )
            
            if happened == 0:
                self.mail.send_success(
                    ", ".join(dispatched),
                    "dispatch_check",
                    f"Dispatch réussi dans {analysis_dir}"
                )
        else:
            logging.error(
                f"{family}: aucun échantillon trouvé dans {analysis_dir}. "
                "Vérifier si dispatch en cours."
            )
            
            happened = self.events.add_and_count(
                analysis_dir,
                family,
                "no_dispatch"
            )
            
            if happened == 0:
                self.mail.send_error(
                    family,
                    "dispatch_check",
                    f"Aucun échantillon dans {analysis_dir}"
                )
        
        return dispatched
    
    def _check_analysis_status(
        self,
        analysis_dir: str,
        family: str,
        dispatched_samples: list
    ) -> tuple:
        """
        Vérifie l'état d'avancement de l'analyse.
        
        Args:
            analysis_dir: Chemin du dossier d'analyse
            family: Nom de la famille
            dispatched_samples: Échantillons dispatchés
        
        Returns:
            Tuple (ended, failed)
        """
        status_file = os.path.join(analysis_dir, "status.tsv")
        
        if not file_exists(status_file, log=False):
            logging.info(f"{family}: analyse non terminée (pas de status.tsv)")
            self.events.add(analysis_dir, family, "analysis_not_ended")
            return False, False
        
        # Analyse terminée
        logging.info(f"{family}: analyse terminée (status.tsv trouvé)")
        self.events.add_and_count(analysis_dir, family, "analysis_ended")
        
        # Parse du fichier status pour détecter les échecs
        status_info = parse_status_file(status_file)
        
        if status_info['has_failures']:
            logging.warning(
                f"{family}: échec(s) détecté(s) - "
                f"{', '.join(status_info['failed_processes'])}"
            )
            
            happened = self.events.add_and_count(
                analysis_dir,
                family,
                "analysis_failed"
            )
            
            if happened == 0:
                error_details = "\n".join([
                    f"Processus {proc} a échoué"
                    for proc in status_info['failed_processes']
                ])
                self.mail.send_error(
                    family,
                    "analysis",
                    f"Échec pour {', '.join(dispatched_samples)}\n{error_details}"
                )
            
            return True, True
        
        else:
            # Analyse réussie
            logging.info(f"{family}: analyse réussie")
            
            happened = self.events.add_and_count(
                analysis_dir,
                family,
                "analysis_ok"
            )
            
            if happened == 0:
                self.mail.send_success(
                    family,
                    "analysis_check",
                    f"Analyse OK pour {', '.join(dispatched_samples)}"
                )
            
            return True, False
    
    def _check_archiving(
        self,
        analysis_dir: str,
        family: str,
        dispatched_samples: list
    ) -> None:
        """
        Vérifie l'état de l'archivage.
        
        Args:
            analysis_dir: Chemin du dossier d'analyse
            family: Nom de la famille
            dispatched_samples: Échantillons dispatchés
        """
        archive_log = os.path.join(analysis_dir, "archive.log")
        
        if not file_exists(archive_log, log=False):
            happened = self.events.add_and_count(
                analysis_dir,
                family,
                "no_archive_log"
            )
            logging.info(f"{family}: pas de fichier archive.log")
            return
        
        # Parse du log d'archivage
        try:
            with open(archive_log, 'r') as f:
                log_content = f.read()
        except Exception as e:
            logging.error(f"Erreur lecture {archive_log}: {e}")
            return
        
        # Vérification de l'état
        end_success = re.search(r"[Ee]xecution with success|exit code : 0", log_content)
        end_stop = re.search(r"[Ss]topping execution$|exit code : [^0]", log_content)
        
        if end_success:
            logging.info(f"{family}: archivage terminé avec succès")
            
            happened = self.events.add_and_count(
                analysis_dir,
                family,
                "archive_success"
            )
            
            if happened == 0:
                self.mail.send_success(
                    family,
                    "archiving_check",
                    "Archivage terminé"
                )
            
            # Événement par échantillon pour nettoyage du registre
            for sample in dispatched_samples:
                self.events.add(analysis_dir, sample, "archive_success")
        
        elif end_stop:
            logging.error(f"{family}: archivage arrêté prématurément")
            
            happened = self.events.add_and_count(
                analysis_dir,
                family,
                "archive_fail"
            )
            
            if happened == 0:
                self.mail.send_error(
                    family,
                    "archiving_check",
                    "Archivage arrêté. Vérifier les logs."
                )
        
        else:
            logging.info(f"{family}: archivage en cours")
            self.events.add_and_count(
                analysis_dir,
                family,
                "archive_in_progress"
            )
    
    def _check_event_counts(self) -> None:
        """Vérifie le nombre d'événements et envoie des alertes si nécessaire."""
        all_events = self.events.get_all_events()
        
        for event_str, count in all_events:
            location, sample, event_type = event_str.split("\t")
            
            # Alerte spéciale pour analyses bloquées
            if event_type == "analysis_not_ended" and count % self.EVENT_COUNT_LIMIT_STUCK == 0:
                warning_msg = (
                    f"Alerte: {count} occurrences de 'analysis_not_ended' "
                    f"pour {sample} ({location}). Analyse peut-être bloquée."
                )
                logging.warning(warning_msg)
                self.mail.send_error(
                    sample,
                    "event_control",
                    warning_msg
                )
                # Ajout artificiel pour éviter spam sur le même modulo
                self.events.add(location, sample, event_type)
            
            # Alertes pour autres événements problématiques
            elif count % self.EVENT_COUNT_LIMIT == 0:
                # Types d'événements à ne pas alerter
                success_events = [
                    "archive_success", "analysis_launched", "infofile_sucess",
                    "dispatch_ok", "analysis_ended", "analysis_ok"
                ]
                
                if event_type not in success_events and event_type != "analysis_not_ended":
                    warning_msg = (
                        f"Alerte: {count} occurrences de '{event_type}' "
                        f"pour {sample} ({location}). Autolauncher peut-être bloqué."
                    )
                    logging.warning(warning_msg)
                    self.mail.send_error(
                        sample,
                        "event_control",
                        warning_msg
                    )
                    # Ajout artificiel pour éviter spam
                    self.events.add(location, sample, event_type)