#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
quark_launcher/Matthieu/steps/organize.py

Description:
Étape d'organisation des fichiers FASTQ en dossiers d'échantillons.
Vérifie la structure familiale via LabKey avant d'organiser.

Auteur: Matthieu Damien
Creation Date: 2025-10-07
Dernière modification: 2025-10-31
Commentaires:
- Vérifier si, à la ligne 136, ceci n'est pas plus efficace :
    f"{fastq}.end" -> f"{sample_name}.end"
- Voir si le reload d'un job en erreur est à mettre ici ou dans une étape dédiée.
"""

import os
import logging
from datetime import datetime
# Le paquet pip à installer est 'labkey' (version 1.4.0), voir https://github.com/LabKey/labkey-api-python
# Il fournit le module 'labkey.api_wrapper'.
from labkey.api_wrapper import APIWrapper

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
            logging.error(
                "ÉCHEC ORGANIZE: Aucun fichier FASTQ trouvé dans %s",
                input_dir
            )
            self.log_end(False)
            return False

        # Validation des paires et tailles
        valid_samples, invalid_samples = self._validate_fastq_files(
            fastq_files, input_dir
        )

        if not valid_samples:
            logging.error(
                "ÉCHEC ORGANIZE: Aucun échantillon valide pour organisation. "
                "Échantillons rejetés: %s",
                ', '.join(invalid_samples) if invalid_samples else "Aucun"
            )
            self.log_end(False)
            return False

        # Interrogation LabKey et vérification structure familiale
        samples_ready, samples_waiting = self._check_family_structure(
            valid_samples, input_dir
        )

        if not samples_ready:
            # Générer un message récapitulatif détaillé
            waiting_details = []
            for ped_id, waiting_samples in samples_waiting.items():
                waiting_details.append(
                    f"Famille {ped_id}: {', '.join(waiting_samples)}"
                )

            if waiting_details:
                logging.error(
                    "ÉCHEC ORGANIZE: Tous les échantillons sont en attente de membres "
                    "de famille manquants. Détails: %s",
                    ' | '.join(waiting_details)
                )
            else:
                logging.error(
                    "ÉCHEC ORGANIZE: Aucun échantillon prêt pour organisation "
                    "(statuts LabKey invalides ou autres problèmes)"
                )

            self.log_end(False)
            return False

        # Lancement de l'organisation
        success = self._launch_organization(samples_ready, input_dir)

        if success:
            logging.info(
                "SUCCÈS ORGANIZE: Organisation lancée avec succès pour %d échantillon(s): %s",
                len(samples_ready), ', '.join(samples_ready)
            )
        else:
            logging.error(
                "ÉCHEC ORGANIZE: Échec du subprocess d'organisation pour %d échantillon(s): %s",
                len(samples_ready), ', '.join(samples_ready)
            )

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

        logging.info("Trouvé %d fichiers FASTQ dans %s", len(fastq_files), input_dir)
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
                logging.warning("Fichier pair introuvable pour %s", fastq)
                self.handle_event(
                    input_dir,
                    fastq,
                    "paired_not_found",
                    f"Fichier pair introuvable : {fastq}"
                )
                invalid_files.extend([fastq, paired_file] if paired_file else [fastq])
                continue

            # Vérification du fichier .end (concaténation terminée)
            end_file = os.path.join(input_dir, f"{fastq}.end") #fastq.gz.end
            if not file_exists(end_file, log=False):
                logging.warning(
                    "Concaténation non terminée pour %s (pas de %s.end)",
                    sample_name, fastq
                )
                invalid_files.extend([fastq, paired_file])
                continue

            # Vérification de la taille
            file_path = os.path.join(input_dir, fastq)
            size_mb = get_file_size_mb(file_path)

            if size_mb < self.MIN_FASTQ_SIZE_MB:
                error_msg = (
                    f"Fichier {fastq} trop petit ({size_mb:.2f} Mo < "
                    f"{self.MIN_FASTQ_SIZE_MB} Mo)"
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
            logging.info("Échantillons invalides: %s", ', '.join(invalid_samples))
        logging.info("Échantillons valides: %s", ', '.join(valid_samples))

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
        # Interrogation LabKey via APIWrapper
        try:
            labkey_server = self.config.labkey_address
            container_path = "home/GAD/Génétique moléculaire"
            context_path = "labkey"

            api = APIWrapper(labkey_server, container_path, context_path, use_ssl=True)

            logging.info("Interrogation LabKey...")
            res = api.query.select_rows(schema_name="study",
                                        query_name="Suivi exomes") #type: ignore

            if not isinstance(res, dict) or "rows" not in res:
                logging.error("LabKey a renvoyé une réponse vide ou inattendue")
                self.mail.send_error("labkey",
                                     "organize",
                                     "Réponse vide de LabKey lors de select_rows")
                return [], samples

            all_exome = res.get("rows", [])
            logging.info("LabKey interrogé avec succès (lignes récupérées: %d)", len(all_exome))

        except (IOError, ValueError) as e:
            error_msg = f"Échec connexion/interrogation LabKey: {type(e).__name__}: {str(e)}"
            logging.error(error_msg)
            try:
                self.mail.send_error("labkey", "organize", error_msg)
            except Exception as mail_e:
                logging.exception("Impossible d'envoyer le mail d'erreur : %s", mail_e)
            return [], samples

        # Analyse de chaque échantillon
        samples_ready = []
        samples_waiting = {}
        bad_samples = []

        for sample in samples:
            # Passage de 'samples' comme 4ème paramètre pour détecter les membres
            # de famille manquants qui ne sont pas dans le batch courant
            status = self._check_sample_in_labkey(sample, all_exome, input_dir, samples)

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
                "Échantillons exclus (statut LabKey): %s", ', '.join(bad_samples)
            )

        for ped_id, waiting_samples in samples_waiting.items():
            logging.warning(
                "Famille %s: échantillons %s en attente d'autres membres",
                ped_id, ', '.join(waiting_samples)
            )

        if samples_ready:
            logging.info("Échantillons prêts: %s", ', '.join(samples_ready))

        return samples_ready, samples_waiting

    def _check_sample_in_labkey(
        self,
        sample: str,
        all_exome: list,
        input_dir: str,
        all_samples_in_batch: list
    ) -> dict:
        """
        Vérifie un échantillon dans LabKey et sa structure familiale.

        Args:
            sample: Nom de l'échantillon
            all_exome: Données LabKey (liste de dicts)
            input_dir: Répertoire d'entrée
            all_samples_in_batch: Liste de tous les échantillons du batch actuel

        Returns:
            Dict avec statut de l'échantillon :
            {
                'ready': bool,              # Prêt pour organisation
                'waiting_for': list,        # Membres famille manquants
                'dismissed_members': list,  # Membres famille avec mauvais statut
                'ped_id': str,              # ID de la famille
                'invalid': bool             # Échantillon invalide (à exclure)
            }
        """
        result = {
            'ready': False,
            'waiting_for': [],
            'dismissed_members': [],
            'ped_id': None,
            'invalid': False
        }

        # ====================================================================
        # ÉTAPE 1 : Récupération et validation du PED ID (identifiant patient)
        # ====================================================================
        ped_ids = [
            line.get("PatientID") for line in all_exome
            if line.get("dijexID") == sample
        ]

        if not ped_ids:
            error_msg = f"PED ID introuvable pour {sample} dans LabKey"
            logging.error(error_msg)
            self.handle_event(input_dir, sample, "no_ped_id", error_msg)
            result['invalid'] = True
            return result

        self.clear_event(input_dir, sample, "no_ped_id")

        # strict_ped = PED complet (ex: "PED001.cas")
        # ped_id = PED famille (ex: "PED001")
        strict_ped = ped_ids[0]
        ped_id = str(strict_ped).split('.', maxsplit=1)[0]
        result['ped_id'] = ped_id

        logging.debug(f"{sample} - PED complet: {strict_ped}, Famille: {ped_id}")

        # ===============================================================
        # ÉTAPE 2 : Vérification du statut LabKey de l'échantillon actuel
        # ===============================================================
        dijex_ids = [line.get("dijexID") for line in all_exome if line.get("dijexID")]

        # Échantillons déjà analysés (date_analyse remplie)
        analyzed = [
            line.get("dijexID") for line in all_exome
            if line.get("date_analyse")
        ]

        # Échantillons avec mauvais statut
        bad_status = [
            line.get("dijexID") for line in all_exome
            if str(line.get("statut")) in ["Annulé", "Echec CQ", "Echec séquençage"]
        ]

        # Vérification existence dans LabKey
        if sample not in dijex_ids:
            error_msg = f"{sample} introuvable dans LabKey"
            logging.error(error_msg)
            self.handle_event(input_dir, sample, "missing_dijex_id", error_msg)
            result['invalid'] = True
            return result

        self.clear_event(input_dir, sample, "missing_dijex_id")

        # Vérification "déjà analysé" (warning mais pas bloquant)
        if sample in analyzed:
            logging.warning(
                "%s déjà analysé (date_analyse remplie dans LabKey)",
                sample
            )
            happened = self.handle_event(
                input_dir,
                sample,
                "already_analyzed",
                f"{sample} déjà analysé",
                send_mail=False  # Juste un warning, pas de mail
            )
            if happened == 0:
                self.mail.send_success(
                    sample,
                    "organize",
                    f"Échantillon déjà analysé (date_analyse remplie)",
                )

        # Vérification statut invalide (BLOQUANT)
        if sample in bad_status:
            error_msg = f"{sample} : statut LabKey invalide (annulé ou échec QC)"
            logging.warning(error_msg)
            self.handle_event(input_dir, sample, "labkey_status_bad", error_msg)
            result['invalid'] = True
            return result

        self.clear_event(input_dir, sample, "labkey_status_bad")

        # =======================================================
        # ÉTAPE 3 : RECHERCHE DES MEMBRES DE LA FAMILLE MANQUANTS
        # Logique critique pour éviter analyses incomplètes
        # =======================================================
        missing_samples = []
        dismissed_samples = []

        # Parcourir TOUTE la base LabKey pour trouver les membres de la même famille
        for line in all_exome:
            line_dijex = line.get("dijexID")
            line_patient_id = line.get("PatientID")

            # Ignorer lignes sans dijexID valide
            if not line_dijex or line_dijex in [None, "Non renseigné", "None", ""]:
                continue

            # Extraire le PED famille de cette ligne
            if not line_patient_id:
                continue
            line_ped = str(line_patient_id).split('.', maxsplit=1)[0]

            # === CAS 1 : Itération multiple du MÊME patient (ne pas attendre) ===
            # Ex: si on a PED001.cas, on ne veut pas attendre un autre PED001.cas
            if (line_patient_id == strict_ped) and (line_dijex != sample):
                logging.info(
                    "%s - Autre itération du même patient trouvée : %s (%s), "
                    "ne sera pas attendue",
                    sample, line_dijex, strict_ped
                )
                continue

            # === CAS 2 : Membre de la même FAMILLE mais patient différent ===
            # Conditions :
            # - Même PED famille (ex: PED001)
            # - Pas dans le batch actuel (sinon déjà traité ensemble)
            # - Patient différent (ex: PED001.pere != PED001.cas)
            if (line_ped == ped_id and
                line_dijex not in all_samples_in_batch and
                line_patient_id != strict_ped):

                # Vérifier si ce membre a un mauvais statut
                line_status = str(line.get("statut", ""))
                if line_status in ["Annulé", "Echec CQ", "Echec séquençage"]:
                    logging.warning(
                        "%s - Membre famille trouvé : %s, mais statut invalide (%s), "
                        "sera ignoré",
                        sample, line_dijex, line_status
                    )
                    dismissed_samples.append(line_dijex)
                else:
                    # Membre famille valide mais absent du batch
                    logging.debug(
                        "%s - Membre famille manquant : %s",
                        sample, line_dijex
                    )
                    missing_samples.append(line_dijex)

        # =================================================
        # ÉTAPE 4 : GESTION DES MEMBRES EXCLUS (mauvais QC)
        # =================================================
        if dismissed_samples:
            # Retirer les membres exclus de la liste des manquants
            missing_samples_cleaned = [
                s for s in missing_samples if s not in dismissed_samples
            ]

            # Enregistrer événement + notification
            happened = self.handle_event(
                input_dir,
                sample,
                "dismissed_family_members",
                (f"{sample} - Membres famille avec mauvais statut ignorés : "
                 f"{', '.join(dismissed_samples)}")
            )

            logging.info(
                "%s - Membres famille exclus (mauvais QC) : %s",
                sample, ', '.join(dismissed_samples)
            )

            missing_samples = missing_samples_cleaned
            result['dismissed_members'] = dismissed_samples

        # =========================
        # ÉTAPE 5 : DÉCISION FINALE
        # =========================
        if missing_samples:
            # Famille incomplète : mettre en attente
            logging.warning(
                "%s - En attente des membres famille : %s",
                sample, ', '.join(missing_samples)
            )

            # Enregistrer événement "family_missing"
            self.handle_event(
                input_dir,
                sample,
                "family_missing",
                f"En attente de : {', '.join(missing_samples)}",
                send_mail=False  # Pas de mail immédiat, juste enregistrement
            )

            result['ready'] = False
            result['waiting_for'] = missing_samples
        else:
            # Famille complète : prêt pour organisation
            logging.info(
                "%s - Famille complète, prêt pour organisation",
                sample
            )
            self.clear_event(input_dir, sample, "family_missing")
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
        with open(sample_list_file, 'w', encoding='utf-8') as f:
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
                "Organisation lancée avec succès pour %d échantillons", len(samples)
            )
            self.clear_event(input_dir, "organize-subprocess", "organize_subprocess_fail")
            self.mail.send_success(
                "novaseq-samples",
                "organize",
                f"Organisation lancée pour {len(samples)} échantillons"
            )
            return True

        except (OSError, ValueError, RuntimeError) as e:
            error_msg = f"Échec de l'organisation: {str(e)}"
            logging.error(error_msg)
            self.handle_event(
                input_dir,
                "organize-subprocess",
                "organize_subprocess_fail",
                error_msg
            )
            return False
