#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fonctions utilitaires génériques pour l'autolauncher.
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional


def file_exists(file_path: str, comment: str = "", log: bool = True) -> bool:
    """
    Vérifie si un fichier existe.
    
    Args:
        file_path: Chemin vers le fichier
        comment: Commentaire à logger si le fichier existe
        log: Activer le logging
    
    Returns:
        True si le fichier existe
    """
    exists = os.path.isfile(file_path)
    
    if log:
        if exists:
            msg = f"Fichier trouvé: {file_path}"
            if comment:
                msg += f" - {comment}"
            logging.info(msg)
        else:
            logging.warning(f"Fichier introuvable: {file_path}")
    
    return exists


def ensure_directory(directory: str) -> None:
    """
    Crée un répertoire s'il n'existe pas.
    
    Args:
        directory: Chemin du répertoire
    """
    if not os.path.isdir(directory):
        os.makedirs(directory, mode=0o770, exist_ok=True)
        logging.info(f"Répertoire créé: {directory}")


def string_in_file(string: str, file_name: str, log: bool = True) -> bool:
    """
    Vérifie si une string existe dans un fichier (ligne complète).
    
    Args:
        string: String à rechercher
        file_name: Chemin du fichier
        log: Activer le logging
    
    Returns:
        True si la string est trouvée
    """
    try:
        with open(file_name, 'r') as f:
            matches = []
            for line in f:
                if re.match(f"^{re.escape(string)}$", line.strip()):
                    matches.append(line)
            
            if log:
                if len(matches) == 1:
                    logging.debug(f"String trouvée dans {file_name}: {string}")
                elif len(matches) > 1:
                    logging.error(
                        f"String trouvée {len(matches)} fois dans {file_name}: {string}"
                    )
                else:
                    logging.debug(f"String non trouvée dans {file_name}: {string}")
            
            return len(matches) > 0
    
    except FileNotFoundError:
        logging.error(f"Fichier introuvable pour recherche: {file_name}")
        return False


def get_or_create_file(
    arg_path: str,
    default_filename: str,
    input_dir: str,
    file_category: str
) -> str:
    """
    Récupère le chemin d'un fichier ou le crée s'il n'existe pas.
    
    Args:
        arg_path: Chemin passé en argument
        default_filename: Nom de fichier par défaut
        input_dir: Répertoire d'entrée
        file_category: Catégorie du fichier (pour logging)
    
    Returns:
        Chemin du fichier
    """
    if not arg_path or arg_path == default_filename:
        file_path = os.path.join(input_dir, default_filename)
    else:
        file_path = arg_path
    
    logging.debug("%s sera écrit dans: %s", file_category, file_path)
    
    # Créer le répertoire parent si nécessaire
    parent_dir = os.path.dirname(file_path)
    if parent_dir:
        os.makedirs(parent_dir, mode=0o770, exist_ok=True)
    
    if not os.path.isfile(file_path):
        Path(file_path).touch(mode=0o770, exist_ok=False)
        os.chmod(file_path, mode=0o770)
        logging.debug("Fichier %s créé: %s", file_category, file_path)
    
    return file_path


def get_file_size_mb(file_path: str) -> float:
    """
    Retourne la taille d'un fichier en Mo.
    
    Args:
        file_path: Chemin du fichier
    
    Returns:
        Taille en Mo
    """
    try:
        size_bytes = os.stat(file_path).st_size
        return size_bytes / (1024 * 1024)
    except FileNotFoundError:
        logging.error(f"Impossible de déterminer la taille de {file_path}")
        return 0


def find_paired_fastq(fastq_file: str, files_list: list) -> Optional[str]:
    """
    Trouve le fichier pair d'un FASTQ (R1 <-> R2).
    
    Args:
        fastq_file: Nom du fichier FASTQ
        files_list: Liste des fichiers disponibles
    
    Returns:
        Nom du fichier pair ou None si non trouvé
    """
    if "R1" in fastq_file:
        paired = fastq_file.replace("R1", "R2")
    elif "R2" in fastq_file:
        paired = fastq_file.replace("R2", "R1")
    else:
        return None
    
    return paired if paired in files_list else None


def get_flowcell_folders(directory: str) -> list:
    """
    Récupère les dossiers de flowcells (commençant par '2').
    
    Args:
        directory: Répertoire à scanner
    
    Returns:
        Liste des chemins des flowcells
    """
    import glob
    flowcells = [
        folder for folder in glob.glob(os.path.join(directory, "2*"))
        if os.path.isdir(folder) and not folder.endswith("logs")
    ]
    return flowcells


def parse_status_file(status_file: str) -> dict:
    """
    Parse un fichier status.tsv pour détecter les échecs.
    
    Args:
        status_file: Chemin du fichier status
    
    Returns:
        Dict avec 'has_failures' (bool) et 'failed_processes' (list)
    """
    result = {
        'has_failures': False,
        'failed_processes': []
    }
    
    try:
        with open(status_file, 'r') as f:
            content = f.read()
        
        status_lines = re.split(r'\n+', content)
        fail_pattern = re.compile(r'^.*FAIL\t?')
        
        for line in status_lines:
            if fail_pattern.match(line):
                result['has_failures'] = True
                process_name = line.split('\t')[0]
                result['failed_processes'].append(process_name)
        
    except Exception as e:
        logging.error(f"Erreur lors du parsing de {status_file}: {e}")
    
    return result