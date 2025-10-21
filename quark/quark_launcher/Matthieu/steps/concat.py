#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Étape de concaténation des fichiers FASTQ des flowcells.
Concatène les fichiers FASTQ par lane pour chaque échantillon.
"""


import os
import glob
import logging
from datetime import datetime

from .base import BaseStep
# pylint: disable-next=E0401
from utils import file_exists, ensure_directory, string_in_file

class ConcatStep(BaseStep):
    """
    Étape de concaténation des FASTQ.
    Traite les flowcells NovaSeq X et lance la concaténation.
    """
    
    def execute(self, input_dir: str) -> bool:
        """
        Exécute la concaténation des FASTQ.
        
        Args:
            input_dir: Répertoire contenant les flowcells
        
        Returns:
            True si au moins une flowcell a été traitée
        """
        self.log_start(input_dir)
        
        # Vérification du fichier concat.list
        concat_file = os.path.join(input_dir, "concat.list")
        if not self._check_concat_file(concat_file, input_dir):
            self.log_end(False)
            return False
        
        # Récupération des flowcells
        flowcells = self._get_flowcells(input_dir)
        if not flowcells:
            logging.info("Aucune flowcell trouvée")
            self.log_end(True)
            return True
        
        # Traitement de chaque flowcell
        success_count = 0
        for flowcell_path in flowcells:
            flowcell_name = os.path.basename(flowcell_path)
            
            if self._is_already_concatenated(flowcell_name, concat_file):
                logging.info(f"Flowcell {flowcell_name} déjà concaténée")
                continue
            
            if self._process_flowcell(flowcell_path, flowcell_name, concat_file, input_dir):
                success_count += 1
        
        self.log_end(True)
        return success_count > 0
    
    def _check_concat_file(self, concat_file: str, input_dir: str) -> bool:
        """
        Vérifie l'existence du fichier concat.list.
        
        Args:
            concat_file: Chemin du fichier concat.list
            input_dir: Répertoire d'entrée
        
        Returns:
            True si le fichier existe
        """
        if not file_exists(concat_file):
            error_msg = f"Fichier {concat_file} introuvable. Ce fichier est requis."
            logging.error(error_msg)
            self.handle_event(
                input_dir, concat_file, "concat_file_missing", error_msg
            )
            return False
        
        self.clear_event(input_dir, concat_file, "concat_file_missing")
        return True
    
    def _get_flowcells(self, input_dir: str) -> list:
        """
        Récupère la liste des flowcells à traiter.
        
        Args:
            input_dir: Répertoire contenant les flowcells
        
        Returns:
            Liste des chemins des flowcells
        """
        flowcells = [
            folder for folder in glob.glob(os.path.join(input_dir, "2*"))
            if os.path.isdir(folder) and not folder.endswith("logs")
        ]
        
        for flowcell in flowcells:
            logging.info(f"Flowcell trouvée: {os.path.basename(flowcell)}")
        
        return flowcells
    
    def _is_already_concatenated(self, flowcell_name: str, concat_file: str) -> bool:
        """
        Vérifie si une flowcell a déjà été concaténée.
        
        Args:
            flowcell_name: Nom de la flowcell
            concat_file: Fichier concat.list
        
        Returns:
            True si déjà concaténée
        """
        return string_in_file(flowcell_name, concat_file)
    
    def _process_flowcell(
        self,
        flowcell_path: str,
        flowcell_name: str,
        concat_file: str,
        input_dir: str
    ) -> bool:
        """
        Traite une flowcell (vérifications et lancement concaténation).
        
        Args:
            flowcell_path: Chemin de la flowcell
            flowcell_name: Nom de la flowcell
            concat_file: Fichier concat.list
            input_dir: Répertoire d'entrée
        
        Returns:
            True si traitement réussi
        """
        # Vérification de l'ambiguïté (plusieurs runs dans Analysis)
        run_folders = [
            folder for folder in glob.glob(os.path.join(flowcell_path, "Analysis", "*"))
            if os.path.isdir(folder)
        ]
        
        if not self._check_run_ambiguity(run_folders, flowcell_name, input_dir):
            return False
        
        # Vérification du fichier CopyComplete.txt
        run_folder = run_folders[0]
        completion_file = os.path.join(run_folder, "CopyComplete.txt")
        
        if not file_exists(completion_file, "Lancement de la concaténation"):
            logging.warning(
                f"Séquençage non terminé pour {flowcell_name} "
                "(pas de CopyComplete.txt). En attente."
            )
            return False
        
        # Lancement de la concaténation
        return self._launch_concatenation(
            run_folder, flowcell_name, concat_file, input_dir
        )
    
    def _check_run_ambiguity(
        self,
        run_folders: list,
        flowcell_name: str,
        input_dir: str
    ) -> bool:
        """
        Vérifie qu'il n'y a pas plusieurs runs dans Analysis.
        
        Args:
            run_folders: Liste des dossiers de runs
            flowcell_name: Nom de la flowcell
            input_dir: Répertoire d'entrée
        
        Returns:
            True si pas d'ambiguïté
        """
        if len(run_folders) > 1:
            error_msg = (
                f"Plusieurs runs trouvés dans Analysis pour {flowcell_name}. "
                "Désambiguïsation requise."
            )
            logging.error(error_msg)
            self.handle_event(
                input_dir, flowcell_name, "concat_ambiguity", error_msg
            )
            return False
        
        self.clear_event(input_dir, flowcell_name, "concat_ambiguity")
        return True
    
    def _launch_concatenation(
        self,
        run_folder: str,
        flowcell_name: str,
        concat_file: str,
        input_dir: str
    ) -> bool:
        """
        Lance le script de concaténation.
        
        Args:
            run_folder: Dossier du run
            flowcell_name: Nom de la flowcell
            concat_file: Fichier concat.list
            input_dir: Répertoire d'entrée
        
        Returns:
            True si succès
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        fastq_dir = os.path.join(run_folder, "Data", "BCLConvert", "fastq")
        output_dir = self.config.concat_out_dir
        
        # Préparation des répertoires
        ensure_directory(output_dir)
        ensure_directory(os.path.join(output_dir, "logs"))
        ensure_directory(os.path.join(output_dir, "logs", "concat"))
        
        log_file = os.path.join(
            output_dir, "logs", "concat", f"{flowcell_name}.concat.{current_date}.log"
        )
        
        # Lancement du subprocess
        try:
            self.pipeline.run_concat_wrapper(fastq_dir, output_dir, log_file)
            
            # Ajout au fichier concat.list
            with open(concat_file, 'a') as f:
                f.write(f"{flowcell_name}\n")
            
            logging.info(f"Concaténation lancée avec succès pour {flowcell_name}")
            self.clear_event(input_dir, flowcell_name, "concat_subprocess_fail")
            self.mail.send_success(
                flowcell_name,
                "concatenation",
                "Lancé avec succès"
            )
            return True
            
        except Exception as e:
            error_msg = f"Échec de la concaténation: {str(e)}"
            logging.error(error_msg)
            self.handle_event(
                input_dir,
                flowcell_name,
                "concat_subprocess_fail",
                error_msg
            )
            return False