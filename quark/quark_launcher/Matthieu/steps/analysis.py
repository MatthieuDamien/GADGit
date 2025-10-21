#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Étape de lancement des analyses bioinformatiques.
Dispatche les échantillons vers le système de calcul (SLURM).
"""

import sys
import os
import logging
from datetime import datetime

from .base import BaseStep
# pylint: disable-next=E0401
from utils import file_exists, ensure_directory


class AnalysisStep(BaseStep):
    """
    Étape de dispatch et lancement des analyses.
    Lit le fichier sample_correspondance.info et lance les analyses.
    """
    
    def execute(self, input_dir: str) -> bool:
        """
        Exécute le lancement des analyses.
        
        Args:
            input_dir: Répertoire contenant le fichier de correspondance
        
        Returns:
            True si succès
        """
        self.log_start(input_dir)
        
        # Vérification du fichier de correspondance
        correspondance_file = os.path.join(input_dir, "sample_correspondance.info")
        
        if not self._check_correspondance_file(correspondance_file, input_dir):
            self.log_end(False)
            return False
        
        # Récupération des échantillons
        samples = self._read_sample_list(correspondance_file)
        
        if not samples:
            logging.info("Aucun échantillon enregistré dans le fichier de correspondance")
            self.log_end(True)
            return True
        
        # Lancement des analyses
        success = self._launch_analyses(correspondance_file, samples, input_dir)
        
        self.log_end(success)
        return success
    
    def _check_correspondance_file(self, file_path: str, input_dir: str) -> bool:
        """
        Vérifie l'existence du fichier de correspondance.
        
        Args:
            file_path: Chemin du fichier
            input_dir: Répertoire d'entrée
        
        Returns:
            True si le fichier existe
        """
        if not file_exists(file_path, log=False):
            error_msg = (
                f"Fichier {file_path} introuvable. "
                "Ce fichier est requis pour lancer les analyses."
            )
            logging.error(error_msg)
            self.handle_event(
                input_dir,
                "spl_correspondance_file",
                "spl_corresp_file_missing",
                error_msg
            )
            return False
        
        self.clear_event(input_dir, "spl_correspondance_file", "spl_corresp_file_missing")
        return True
    
    def _read_sample_list(self, correspondance_file: str) -> list:
        """
        Lit la liste des échantillons depuis le fichier de correspondance.
        
        Args:
            correspondance_file: Chemin du fichier
        
        Returns:
            Liste des noms d'échantillons
        """
        try:
            with open(correspondance_file, 'r', encoding='utf-8') as f:
                samples = [
                    line.split("\t")[0] for line in f
                    if not line.startswith("SAMPLE_NAME")
                ]
            
            samples = [s.strip() for s in samples if s.strip()]
            return samples
            
        except (OSError, ValueError) as e:
            logging.error("Erreur lecture fichier de correspondance: %s", e)
            return []
    
    def _launch_analyses(
        self,
        correspondance_file: str,
        samples: list,
        input_dir: str
    ) -> bool:
        """
        Lance le dispatch et les analyses.
        
        Args:
            correspondance_file: Fichier de correspondance
            samples: Liste des échantillons
            input_dir: Répertoire d'entrée
        
        Returns:
            True si succès
        """
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Préparation
        ensure_directory(os.path.join(input_dir, "logs"))
        log_file = os.path.join(
            input_dir, "logs", f"dispatch_sample.{current_time}.log"
        )
        
        output_dir = self.config.analysis_out_dir
        
        # Lancement
        try:
            self.pipeline.run_dispatch_sample(
                correspondance_file,
                input_dir,
                output_dir,
                log_file
            )
            
            logging.info(
                "Analyses lancées avec succès pour %d échantillons. "
                "Note: cela ne garantit pas que tous ont été dispatchés "
                "(dépend des ressources disponibles).",
                len(samples)
            )
            
            self.clear_event(input_dir, "analysis_subprocess", "analysis_launch_fail")
            
            # Enregistrement des événements
            self.events.add_and_count(
                input_dir,
                ", ".join(samples),
                "analysis_launched"
            )
            
            # Événement par échantillon pour tracking
            for sample in samples:
                self.events.add(input_dir, sample, "found_in_organize")
            
            self.mail.send_success(
                "novaseq-samples",
                "analysis",
                f"Programme lancé pour {', '.join(samples)}"
            )
            return True
            
        except (OSError, ValueError) as e:
            error_msg = f"Échec du dispatch (erreur système ou valeur): {str(e)}"
            logging.error(error_msg)
            self.handle_event(
                input_dir,
                "analysis_subprocess",
                "analysis_launch_fail",
                error_msg
            )
            return False
        except RuntimeError as e:
            error_msg = f"Échec du dispatch (RuntimeError): {str(e)}"
            logging.error(error_msg)
            self.handle_event(
                input_dir,
                "analysis_subprocess",
                "analysis_launch_fail",
                error_msg
            )
            return False
        # D'autres types d'erreurs ?