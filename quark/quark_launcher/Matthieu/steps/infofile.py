#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Étape de création/mise à jour du fichier d'information des échantillons.
Génère le fichier sample_correspondance.info nécessaire au dispatch.
"""

import os
import glob
import logging
from datetime import datetime

from .base import BaseStep
# pylint: disable-next=E0401
from utils import ensure_directory


class InfofileStep(BaseStep):
    """
    Étape de création du fichier d'information.
    Génère sample_correspondance.info avec les métadonnées des échantillons.
    """
    
    def execute(self, input_dir: str) -> bool:
        """
        Exécute la création du fichier d'information.
        
        Args:
            input_dir: Répertoire contenant les dossiers d'échantillons
        
        Returns:
            True si succès
        """
        self.log_start(input_dir)
        
        # Récupération des dossiers d'échantillons
        sample_dirs = self._get_sample_directories(input_dir)
        
        if not sample_dirs:
            logging.info("Aucun dossier d'échantillon trouvé")
            self.log_end(True)
            return True
        
        # Lancement de la création du fichier info
        success = self._create_info_file(sample_dirs, input_dir)
        
        self.log_end(success)
        return success
    
    def _get_sample_directories(self, input_dir: str) -> list:
        """
        Récupère les dossiers d'échantillons.
        
        Args:
            input_dir: Répertoire à scanner
        
        Returns:
            Liste des noms d'échantillons
        """
        sample_paths = [
            sample for sample in glob.glob(os.path.join(input_dir, "*"))
            if os.path.isdir(sample) and not sample.endswith("logs")
        ]
        
        sample_names = [os.path.basename(path) for path in sample_paths]
        sample_names = sorted(sample_names)
        
        if sample_names:
            logging.info("Échantillons détectés: %s", ", ".join(sample_names))
        
        return sample_names
    
    def _create_info_file(self, samples: list, input_dir: str) -> bool:
        """
        Lance la création du fichier d'information.
        
        Args:
            samples: Liste des échantillons
            input_dir: Répertoire d'entrée
        
        Returns:
            True si succès
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Préparation
        output_file = os.path.join(input_dir, "sample_correspondance.info")
        sample_list_file = os.path.join(input_dir, "samples_to_infofile.list")
        
        with open(sample_list_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(samples))
        
        ensure_directory(os.path.join(input_dir, "logs"))
        log_file = os.path.join(
            input_dir, "logs", f"create_sample_information_file.{current_date}.log"
        )
        
        # Lancement
        try:
            self.pipeline.run_create_sample_info(
                sample_list_file,
                output_file,
                input_dir,
                log_file
            )
            
            logging.info(
                "Fichier d'information créé avec succès pour %d échantillons",
                len(samples)
            )
            self.clear_event(input_dir, "infofile_subprocess", "infofile_subprocess_fail")
            
            # Enregistrement de l'événement de succès
            self.events.add_and_count(
                input_dir,
                ", ".join(samples),
                "infofile_sucess"
            )
            
            self.mail.send_success(
                "novaseq-samples",
                "infofile",
                f"Fichier info créé pour {', '.join(samples)}"
            )
            return True
        
        
        # Erreurs        
        except (OSError, IOError) as e:
            error_msg = f"Échec création fichier info (erreur fichier): {str(e)}"
            logging.error(error_msg)
            self.handle_event(
                input_dir,
                "infofile_subprocess",
                "infofile_subprocess_fail",
                error_msg
            )
            return False
        except RuntimeError as e:
            error_msg = f"Échec création fichier info (erreur pipeline): {str(e)}"
            logging.error(error_msg)
            self.handle_event(
                input_dir,
                "infofile_subprocess",
                "infofile_subprocess_fail",
                error_msg
            )
            return False