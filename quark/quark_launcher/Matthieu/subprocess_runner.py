#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
subproccess_runner.py

Description:
Gestion de l'exécution des sous-processus (scripts du pipeline).
Factorise la logique commune d'exécution et de gestion d'erreurs.

Auteur: Matthieu Damien
Creation Date: 2025-10-07
Dernière modification: 2025-10-31
Commentaires:
"""

import os
import logging
import subprocess
from typing import Dict, Any, Optional


class SubprocessRunner:
    """
    Exécuteur de sous-processus avec gestion d'erreurs standardisée.
    """
    timeout: Optional[int] = 3600 # 1h par défaut
    
    def __init__(self, timeout: Optional[int] = None):
        """
        Initialise le runner.
        
        Args:
            timeout: Timeout en secondes (None = pas de timeout)
        """
        self.timeout = timeout

    def run_bash_script(
        self,
        script_path: str,
        env_vars: Optional[Dict[str, str]] = None,
        check_output: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Exécute un script bash avec des variables d'environnement.
        
        Args:
            script_path: Chemin vers le script bash
            env_vars: Variables d'environnement à exporter
            check_output: Capturer stdout/stderr
        
        Returns:
            CompletedProcess avec le résultat
        
        Raises:
            subprocess.CalledProcessError: Si le script échoue
        """
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"Script introuvable: {script_path}")

        # Prépare l'environnement
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Construit la commande
        cmd = ["bash", script_path]

        # Log de la commande
        env_str = ", ".join([f"{k}={v}" for k, v in (env_vars or {}).items()])
        logging.debug("Exécution: %s", ' '.join(cmd))
        if env_str:
            logging.debug("Variables exportées: %s", env_str)

        # Exécution
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=check_output,
                text=True,
                encoding="utf-8",
                timeout=self.timeout,
                check=False
            )

            # Log des outputs
            if result.stdout and result.stdout.strip():
                logging.debug("Sortie standard: %s", result.stdout.strip())

            if result.returncode != 0:
                error_msg = f"Échec avec code de sortie: {result.returncode}"
                if result.stderr and result.stderr.strip():
                    error_msg += f"\nErreur: {result.stderr.strip()}"
                logging.error(error_msg)
                raise subprocess.CalledProcessError(
                    result.returncode, cmd, result.stdout, result.stderr
                )

            return result

        except subprocess.TimeoutExpired as e:
            logging.error("Timeout atteint (%ss) pour: %s", self.timeout, ' '.join(cmd))
            raise e
        except Exception as e:
            logging.error("Erreur lors de l'exécution: %s", e)
            raise

    def run_python_script(
        self,
        script_path: str,
        args: Optional[Dict[str, Any]] = None,
        check_output: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Exécute un script Python avec des arguments.
        
        Args:
            script_path: Chemin vers le script Python
            args: Arguments à passer (format: {"-d": value, "-s": value})
            check_output: Capturer stdout/stderr
        
        Returns:
            CompletedProcess avec le résultat
        
        Raises:
            subprocess.CalledProcessError: Si le script échoue
        """
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"Script introuvable: {script_path}")

        # Construit la commande
        cmd = ["python3", script_path]

        if args:
            for key, value in args.items():
                if value is False:
                    # Flag booléen False = ne pas l'ajouter
                    continue
                elif value is True:
                    # Flag booléen True = ajouter juste la clé
                    cmd.append(key)
                else:
                    # Argument avec valeur
                    cmd.extend([key, str(value)])

        # Log de la commande
        logging.info("Exécution: %s", ' '.join(cmd))

        # Exécution
        try:
            result = subprocess.run(
                cmd,
                capture_output=check_output,
                text=True,
                encoding="UTF-8",
                timeout=self.timeout,
                check=False
            )

            # Log des outputs
            if result.stdout and result.stdout.strip():
                logging.debug("Sortie standard: %s", result.stdout.strip())

            if result.returncode != 0:
                error_msg = f"Échec avec code de sortie: {result.returncode}"
                if result.stderr and result.stderr.strip():
                    error_msg += f"\nErreur: {result.stderr.strip()}"
                logging.error(error_msg)
                raise subprocess.CalledProcessError(
                    result.returncode, cmd, result.stdout, result.stderr
                )

            return result

        except subprocess.TimeoutExpired as e:
            logging.error("Timeout atteint (%ss) pour: %s", self.timeout, ' '.join(cmd))
            raise e
        except Exception as e:
            logging.error("Erreur lors de l'exécution: %s", e)
            raise


class PipelineRunner:
    """
    Runner spécialisé pour les scripts du pipeline bioinformatique.
    """

    def __init__(self, config, subprocess_runner: Optional[SubprocessRunner] = None):
        """
        Initialise le runner de pipeline.
        
        Args:
            config: Instance de Config
            subprocess_runner: Runner de subprocess (créé par défaut si None)
        """
        self.config = config
        self.runner = subprocess_runner or SubprocessRunner()

    def run_concat_wrapper(
        self,
        input_dir: str,
        output_dir: str,
        log_file: str
    ) -> subprocess.CompletedProcess:
        """
        Exécute le wrapper de concaténation FASTQ.
        
        Args:
            input_dir: Répertoire d'entrée
            output_dir: Répertoire de sortie
            log_file: Fichier de log
        
        Returns:
            Résultat de l'exécution
        """
        script_path = self.config.get_script_path(
            "common/fastq/wrapper_concat_fastq.sh"
        )

        env_vars = {
            "INPUTDIR": input_dir,
            "OUTPUTDIR": output_dir,
            "CLUSTER": "slurm",
            "LOGFILE": log_file,
            "CONFIGFILE": self.config.pipeline_config
        }

        return self.runner.run_bash_script(script_path, env_vars)

    def run_organize_data_folder(
        self,
        input_dir: str,
        output_dir: str,
        sample_list_file: str,
        log_file: str
    ) -> subprocess.CompletedProcess:
        """
        Exécute l'organisation des dossiers d'échantillons.
        
        Args:
            input_dir: Répertoire d'entrée
            output_dir: Répertoire de sortie
            sample_list_file: Fichier liste des échantillons
            log_file: Fichier de log
        
        Returns:
            Résultat de l'exécution
        """
        script_path = self.config.get_script_path(
            "common/fastq/organize_data_folder.py"
        )

        args = {
            "-d": input_dir,
            "-b": self.config.labkey_address,
            "-p": self.config.pipeline_base,
            "-e": log_file,
            "-s": sample_list_file,
            "-t": self.config.target_list,
            "-c": False,
            "-u": output_dir
        }

        return self.runner.run_python_script(script_path, args)

    def run_create_sample_info(
        self,
        sample_list_file: str,
        output_file: str,
        input_dir: str,
        log_file: str
    ) -> subprocess.CompletedProcess:
        """
        Exécute la création du fichier d'informations d'échantillons.
        
        Args:
            sample_list_file: Fichier liste des échantillons
            output_file: Fichier de sortie
            input_dir: Répertoire d'entrée
            log_file: Fichier de log
        
        Returns:
            Résultat de l'exécution
        """
        script_path = self.config.get_script_path(
            "common/fastq/wrapper_create_sample_information_file.sh"
        )

        env_vars = {
            "INPUTFILE": sample_list_file,
            "OUTPUTFILE": output_file,
            "LOGFILE": log_file,
            "CONFIGFILE": self.config.pipeline_config,
            "INPUTDIR": input_dir
        }

        return self.runner.run_bash_script(script_path, env_vars)

    def run_dispatch_sample(
        self,
        correspondance_file: str,
        input_dir: str,
        output_dir: str,
        log_file: str
    ) -> subprocess.CompletedProcess:
        """
        Exécute le dispatch et lancement d'analyses.
        
        Args:
            correspondance_file: Fichier de correspondance des échantillons
            input_dir: Répertoire d'entrée
            output_dir: Répertoire de sortie
            log_file: Fichier de log
        
        Returns:
            Résultat de l'exécution
        """
        script_path = self.config.get_script_path(
            "common/fastq/dispatch_sample_and_mv.py"
        )

        args = {
            "-i": correspondance_file,
            "-d": input_dir,
            "-n": "gpu",
            "-q": "neomics",
            "-r": "gpu",
            "-b": self.config.labkey_address,
            "-s": "slurm",
            "-t": output_dir,
            "-e": log_file
        }

        return self.runner.run_python_script(script_path, args)
