#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
config.py

Description:
Configuration centralisée pour l'autolauncher.
Charge les paramètres depuis le fichier de configuration.

Auteur: Matthieu Damien
Creation Date: 2025-10-07
Dernière modification: 2025-10-31
Commentaires:
- Voir pour déplacer les chemins par défaut dans un fichier séparé / 
    meilleure evolutivité pour DEFAULT_CONFIG_FILE
- 56-63
    for row in reader:
        if len(row) == 2:
            key, value = row
    Problème : Si une ligne a 3 colonnes (comme ligne 1 avec "comment"), 
    elle est silencieusement ignorée. Les lignes vides cassent aussi le parsing
"""

import os
import csv
from typing import Dict, Any, Optional

class Config:
    """Classe de configuration pour l'autolauncher."""

    DEFAULT_LOG_FILE = "autolauncher.log"
    DEFAULT_EVENT_FILE = "autolauncher.events"
    DEFAULT_MAIL_FILE = "autolauncher_mailing.sh"
    DEFAULT_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.csv")
    DEFAULT_CONFIG_DEV_FILE = os.path.join(os.path.dirname(__file__), "config_dev.csv")

    def __init__(
        self,
        config_file: Optional[str] = None,
        labkey_server_override: Optional[str] = None,
        test_mode: bool = False
    ):
        """
        Initialise la configuration.

        Args:
            config_file: Chemin vers le fichier de configuration
            labkey_server_override: Override CLI pour l'adresse du serveur LabKey (optionnel)
            test_mode: Si True, utilise config_dev.csv au lieu de config.csv
        """
        # Si test_mode est activé et aucun fichier spécifique fourni, utiliser config_dev.csv
        if test_mode and config_file is None:
            self.config_file = self.DEFAULT_CONFIG_DEV_FILE
        else:
            self.config_file = config_file or self.DEFAULT_CONFIG_FILE

        self.labkey_server_override = labkey_server_override
        self.test_mode = test_mode

        # Attributs qui seront chargés depuis le fichier de configuration
        # Ces attributs sont garantis non-None après _load_config() (sinon ValueError)
        self.mail_bioinfo: str
        self.labkey_address: str
        self.concat_out_dir: str
        self.analysis_out_dir: str
        self.pipeline_base: str
        self.pipeline_config: str
        self.target_list: str

        # Attributs optionnels
        self.main_dir: Optional[str] = None
        self.concat_in_dir: Optional[str] = None
        self.logs_autolauncher: Optional[str] = None

        self._load_config()

        # Surcharger labkey_address si l'override CLI est fourni
        if self.labkey_server_override:
            self.labkey_address = self.labkey_server_override

    def _load_config(self) -> None:
        """Charge la configuration depuis le fichier CSV."""
        if not os.path.isfile(self.config_file):
            raise FileNotFoundError(f"Fichier de configuration introuvable: {self.config_file}")

        config_data: Dict[str, str] = {}
        with open(self.config_file, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Ignorer l'en-tête (key,value,comment)
            for row in reader:
                # Ignorer les lignes vides ou trop courtes
                if not row or len(row) < 2:
                    continue

                # Extraire key et value (ignorer le commentaire en 3ème colonne si présent)
                key = row[0].strip()
                value = row[1].strip()

                # Ignorer les lignes de commentaire (key vide)
                if not key:
                    continue

                config_data[key] = value

        # Liste des clés de configuration requises
        required_keys = [
            'mail_bioinfo', 'labkey_address', 'concat_out_dir',
            'analysis_out_dir', 'pipeline_base', 'pipeline_config', 'target_list'
        ]

        # Clés optionnelles
        optional_keys = ['main_dir', 'concat_in_dir', 'logs_autolauncher']

        # Charger les clés requises
        missing_keys = []
        for key in required_keys:
            value_str = config_data.get(key)
            if value_str:
                # Gestion intelligente des chemins
                is_path = key.endswith(('_dir', '_list', '_base', '_config'))

                # Si la valeur est un chemin, la rendre absolue.
                # Les chemins commençant par '~' sont étendus.
                # Les chemins relatifs sont résolus par rapport au dossier du fichier de config.
                if is_path:
                    expanded_path = os.path.expanduser(value_str)
                    if not os.path.isabs(expanded_path):
                        config_dir = os.path.dirname(self.config_file)
                        value = os.path.abspath(os.path.join(config_dir, expanded_path))
                    else:
                        value = expanded_path
                else:
                    value = value_str

                setattr(self, key, value) # type: ignore
            else:
                missing_keys.append(key)

        if missing_keys:
            raise ValueError( "Configuration incomplète. \n"
                             f"Clés manquantes dans {self.config_file}: {', '.join(missing_keys)}")

        # Charger les clés optionnelles
        for key in optional_keys:
            value_str = config_data.get(key)
            if value_str:
                is_path = key.endswith(('_dir', '_list', '_base', '_config'))
                if is_path:
                    expanded_path = os.path.expanduser(value_str)
                    if not os.path.isabs(expanded_path):
                        config_dir = os.path.dirname(self.config_file)
                        value = os.path.abspath(os.path.join(config_dir, expanded_path))
                    else:
                        value = expanded_path
                else:
                    value = value_str
                setattr(self, key, value) # type: ignore

    def get_script_path(self, script_name: str) -> str:
        """
        Retourne le chemin complet vers un script du pipeline.

        Args:
            script_name: Nom relatif du script (ex: "common/fastq/wrapper_concat_fastq.sh")

        Returns:
            Chemin complet vers le script

        Raises:
            FileNotFoundError: Si le script n'existe pas
        """
        # pipeline_base est garanti non-None après __init__
        full_path = os.path.join(self.pipeline_base, script_name)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"Script introuvable: {full_path}")
        return full_path

    def to_dict(self) -> Dict[str, Any]:
        """Retourne la configuration sous forme de dictionnaire."""
        config_dict = {
            'config_file':      self.config_file,
            'test_mode':        self.test_mode,
            'mail_bioinfo':     self.mail_bioinfo,
            'labkey_address':   self.labkey_address,
            'concat_out_dir':   self.concat_out_dir,
            'analysis_out_dir': self.analysis_out_dir,
            'pipeline_base':    self.pipeline_base,
            'pipeline_config':  self.pipeline_config,
            'target_list':      self.target_list
        }

        # Ajouter les clés optionnelles si elles existent
        if self.main_dir:
            config_dict['main_dir'] = self.main_dir
        if self.concat_in_dir:
            config_dict['concat_in_dir'] = self.concat_in_dir
        if self.logs_autolauncher:
            config_dict['logs_autolauncher'] = self.logs_autolauncher

        return config_dict
