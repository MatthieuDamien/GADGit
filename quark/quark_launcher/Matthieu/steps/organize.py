#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Étape d'organisation des fichiers FASTQ en dossiers d'échantillons.
Vérifie la structure familiale via LabKey avant d'organiser.
"""

import os
import glob
import logging
import labkey
# pylint: disable=E1101
from labkey.utils import create_server_context
from datetime import datetime

from .base import BaseStep
# pylint: disable-next=E0401
from utils import file_exists, ensure_directory, get_file_size_mb, find_paired_fastq


class OrganizeStep(BaseStep):
    """
    Étape d'organisation des échantillons.
    Vérifie les paires FASTQ, interroge LabKey pour la structure familiale,
    et lance l'organisation des dossiers.
    """
    
    MIN_FASTQ_SIZE_MB = 10  # Taille minimale d'un FASTQ en Mo
    
    def execute(self, input_dir: str) -> bool:
        """
        Exécute l'organisation des échantillons.
        
        Args:
            input_dir: Répertoire contenant les FASTQ concaténés
        
        Returns:
            True si succès
        """
        self.log_start(input_dir)
        
        # Récupération des FASTQ
        fastq_files = self._get_fastq_files(input_dir)
        if not fastq_files:
            logging.info("Aucun fichier FASTQ trouvé")
            self.log_end(True)
            return True
        
        # Validation des paires et tailles
        valid_samples, invalid_samples = self._validate_fastq_files(
            fastq_files, input_dir
        )
        
        if not valid_samples:
            logging.info("Aucun échantillon valide pour organisation")
            self.log_end(True)
            return True
        
        # Interrogation LabKey et vérification structure familiale
        samples_ready, samples_waiting = self._check_family_structure(
            valid_samples, input_dir
        )
        
        if not samples_ready:
            logging.info("Aucun échantillon prêt (en attente de famille)")
            self.log_end(True)
            return True
        
        # Lancement de l'organisation
        success = self._launch_organization(samples_ready, input_dir)
        
        self.log_end(success)
        return success
    
    def _get_fastq_files(self, input_dir: str) -> list:
        """
        Récupère la liste des fichiers FASTQ.
        
        Args:
            input_dir: Répertoire à scanner
        
        Returns:
            Liste des noms de fichiers FASTQ
        """
        files = os.listdir(input_dir)
        fastq_files = [f for f in files if f.endswith(".fastq.gz")]
        fastq_files = sorted(list(set(fastq_files)))
        
        logging.info(f"Trouvé {len(fastq_files)} fichiers FASTQ dans {input_dir}")
        return fastq_files
    
    def _validate_fastq_files(self, fastq_files: list, input_dir: str) -> tuple:
        """
        Valide les fichiers FASTQ (paires R1/R2 et taille).
        
        Args:
            fastq_files: Liste des fichiers FASTQ
            input_dir: Répertoire contenant les FASTQ
        
        Returns:
            Tuple (samples_valides, samples_invalides)
        """
        valid_samples = []
        invalid_files = []
        
        files_in_dir = os.listdir(input_dir)
        
        for fastq in fastq_files:
            if fastq in invalid_files:
                continue
            
            sample_name = fastq.split(".")[0]
            
            # Vérification de la paire R1/R2
            paired_file = find_paired_fastq(fastq, files_in_dir)
            if not paired_file:
                logging.warning(f"Fichier pair introuvable pour {fastq}")
                self.handle_event(
                    input_dir,
                    fastq,
                    "paired_not_found",
                    f"Fichier pair introuvable"
                )
                invalid_files.extend([fastq, paired_file] if paired_file else [fastq])
                continue
            
            # Vérification du fichier .end (concaténation terminée)
            end_file = os.path.join(input_dir, f"{fastq}.end")
            if not file_exists(end_file, log=False):
                logging.warning(
                    f"Concaténation non terminée pour {sample_name} "
                    f"(pas de {fastq}.end)"
                )
                invalid_files.extend([fastq, paired_file])
                continue
            
            # Vérification de la taille
            file_path = os.path.join(input_dir, fastq)
            size_mb = get_file_size_mb(file_path)
            
            if size_mb < self.MIN_FASTQ_SIZE_MB:
                error_msg = (
                    f"Fichier {fastq} trop petit ({size_mb:.2f} Mo < {self.MIN_FASTQ_SIZE_MB} Mo)"
                )
                logging.error(error_msg)
                self.handle_event(
                    input_dir,
                    fastq,
                    "fastq_too_small",
                    error_msg
                )
                invalid_files.extend([fastq, paired_file])
                continue
            
            # Fichier valide
            self.clear_event(input_dir, fastq, "fastq_too_small")
            self.clear_event(input_dir, fastq, "paired_not_found")
            valid_samples.append(sample_name)
        
        valid_samples = sorted(list(set(valid_samples)))
        invalid_samples = sorted(list(set([f.split(".")[0] for f in invalid_files])))
        
        if invalid_samples:
            logging.info(f"Échantillons invalides: {', '.join(invalid_samples)}")
        logging.info(f"Échantillons valides: {', '.join(valid_samples)}")
        
        return valid_samples, invalid_samples
    
    def _check_family_structure(self, samples: list, input_dir: str) -> tuple:
        """
        Vérifie la structure familiale via LabKey.
        
        Args:
            samples: Liste des échantillons à vérifier
            input_dir: Répertoire d'entrée
        
        Returns:
            Tuple (samples_prêts, samples_en_attente)
        """
        # Interrogation LabKey
        try:
            server_context = labkey.utils.create_server_context(
                domain=self.config.labkey_address,
                container_path="home/GAD/Génétique moléculaire",
                context_path="labkey"
            )
            
            logging.info("Interrogation LabKey...")
            all_exome = labkey.query.select_rows(
                server_context,
                schema_name="study",
                query_name="Suivi exomes",
                timeout=120
            )
            all_exome = all_exome["rows"]
            logging.info("LabKey interrogé avec succès")
            
        except labkey.exceptions.ServerContextError as e:
            error_msg = f"Échec connexion LabKey: {e}"
            logging.error(error_msg)
            self.mail.send_error("labkey", "organize", error_msg)
            return [], samples
        
        # Analyse de chaque échantillon
        samples_ready = []
        samples_waiting = {}
        bad_samples = []
        
        for sample in samples:
            status = self._check_sample_in_labkey(sample, all_exome, input_dir)
            
            if status['ready']:
                samples_ready.append(sample)
            elif status['waiting_for']:
                ped_id = status['ped_id']
                if ped_id not in samples_waiting:
                    samples_waiting[ped_id] = []
                samples_waiting[ped_id].append(sample)
            elif status['invalid']:
                bad_samples.append(sample)
        
        # Logging récapitulatif
        if bad_samples:
            logging.info(
                f"Échantillons exclus (statut LabKey): {', '.join(bad_samples)}"
            )
        
        for ped_id, waiting_samples in samples_waiting.items():
            logging.warning(
                f"Famille {ped_id}: échantillons {', '.join(waiting_samples)} "
                f"en attente d'autres membres"
            )
        
        if samples_ready:
            logging.info(f"Échantillons prêts: {', '.join(samples_ready)}")
        
        return samples_ready, samples_waiting
    
    def _check_sample_in_labkey(
        self,
        sample: str,
        all_exome: list,
        input_dir: str
    ) -> dict:
        """
        Vérifie un échantillon dans LabKey.
        
        Args:
            sample: Nom de l'échantillon
            all_exome: Données LabKey
            input_dir: Répertoire d'entrée
        
        Returns:
            Dict avec statut de l'échantillon
        """
        result = {
            'ready': False,
            'waiting_for': [],
            'ped_id': None,
            'invalid': False
        }
        
        # Récupération du PED ID
        ped_ids = [
            line["PatientID"] for line in all_exome
            if line["dijexID"] == sample
        ]
        
        if not ped_ids:
            error_msg = f"PED ID introuvable pour {sample}"
            logging.error(error_msg)
            self.handle_event(input_dir, sample, "no_ped_id", error_msg)
            result['invalid'] = True
            return result
        
        self.clear_event(input_dir, sample, "no_ped_id")
        
        strict_ped = ped_ids[0]
        ped_id = strict_ped.split(".")[0]
        result['ped_id'] = ped_id
        
        # Vérification du statut LabKey
        dijex_ids = [line["dijexID"] for line in all_exome]
        bad_status = [
            line["dijexID"] for line in all_exome
            if str(line["statut"]) in ["Annulé", "Echec CQ", "Echec séquençage"]
        ]
        
        if sample not in dijex_ids:
            error_msg = f"{sample} introuvable dans LabKey"
            logging.error(error_msg)
            self.handle_event(input_dir, sample, "missing_dijex_id", error_msg)
            result['invalid'] = True
            return result
        
        self.clear_event(input_dir, sample, "missing_dijex_id")
        
        if sample in bad_status:
            error_msg = f"{sample} : statut LabKey invalide (annulé ou échec QC)"
            logging.warning(error_msg)
            self.handle_event(input_dir, sample, "labkey_status_bad", error_msg)
            result['invalid'] = True
            return result
        
        # Recherche des autres membres de la famille
        # (logique simplifiée - à adapter selon besoins)
        result['ready'] = True
        return result
    
    def _launch_organization(self, samples: list, input_dir: str) -> bool:
        """
        Lance l'organisation des dossiers d'échantillons.
        
        Args:
            samples: Liste des échantillons à organiser
            input_dir: Répertoire d'entrée
        
        Returns:
            True si succès
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Préparation
        sample_list_file = os.path.join(input_dir, "samples_to_organize.list")
        with open(sample_list_file, 'w') as f:
            f.write("\n".join(samples) + "\n")
        
        output_dir = os.path.join(input_dir, "organize")
        ensure_directory(output_dir)
        ensure_directory(os.path.join(output_dir, "logs"))
        
        log_file = os.path.join(
            output_dir, "logs", f"organize_data_folder.{current_date}.log"
        )
        
        # Lancement
        try:
            self.pipeline.run_organize_data_folder(
                input_dir,
                output_dir,
                sample_list_file,
                log_file
            )
            
            logging.info(
                f"Organisation lancée avec succès pour {len(samples)} échantillons"
            )
            self.clear_event(input_dir, "organize-subprocess", "organize_subprocess_fail")
            self.mail.send_success(
                "novaseq-samples",
                "organize",
                f"Organisation lancée pour {', '.join(samples)}"
            )
            return True
            
        except Exception as e:
            error_msg = f"Échec de l'organisation: {str(e)}"
            logging.error(error_msg)
            self.handle_event(
                input_dir,
                "organize-subprocess",
                "organize_subprocess_fail",
                error_msg
            )
            return False