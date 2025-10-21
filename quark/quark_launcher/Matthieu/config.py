#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration centralisée pour l'autolauncher.
Charge les paramètres depuis le fichier de configuration.
"""

import os
from typing import Dict, Any

class Config:
    """Classe de configuration pour l'autolauncher."""
    
    # Valeurs par défaut
    DEFAULT_LOG_FILE = "autolauncher.log"
    DEFAULT_EVENT_FILE = "autolauncher.events"
    DEFAULT_MAIL_FILE = "autolauncher_mailing.sh"
    
    def __init__(self, config_file: str = None):
        """
        Initialise la configuration.
        
        Args:
            config_file: Chemin vers le fichier de configuration
        """
        # Chemins et adresses
        self.config_file = config_file or "/work/work/shared/s-neomics/pipeline/2.11.0/common/analysis_config_mesobfc.tsv"
        self.mail_bioinfo = "gad-astreinte-bioinfo@u-bourgogne.fr"
        self.labkey_address = "translad.chu-dijon.fr"
        
        # Répertoires de sortie
        self.concat_out_dir = "/work/work/shared/s-neomics/data/incoming/"
        self.analysis_out_dir = "/work/work/shared/s-neomics/data/analyse/"
        
        # Variables chargées depuis le fichier de config
        self.pipeline_base = None
        self.target_list = None
        
        # Chargement de la configuration
        self._load_config()
    
    def _load_config(self) -> None:
        """Charge la configuration depuis le fichier TSV."""
        if not os.path.isfile(self.config_file):
            raise FileNotFoundError(f"Fichier de configuration introuvable: {self.config_file}")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("pipelinebase\t"):
                    self.pipeline_base = line.split("\t")[1]
                elif line.startswith("targetlist\t"):
                    self.target_list = line.split("\t")[1]
        
        if not self.pipeline_base or not self.target_list:
            raise ValueError("Configuration incomplète: pipelinebase ou targetlist manquant")
    
    def get_script_path(self, script_name: str) -> str:
        """
        Retourne le chemin complet vers un script du pipeline.
        
        Args:
            script_name: Nom relatif du script (ex: "common/fastq/wrapper_concat_fastq.sh")
        
        Returns:
            Chemin complet vers le script
        """
        return os.path.join(self.pipeline_base, script_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Retourne la configuration sous forme de dictionnaire."""
        return {
            'config_file':      self.config_file,
            'mail_bioinfo':     self.mail_bioinfo,
            'labkey_address':   self.labkey_address,
            'concat_out_dir':   self.concat_out_dir,
            'analysis_out_dir': self.analysis_out_dir,
            'pipeline_base':    self.pipeline_base,
            'target_list':      self.target_list
        }