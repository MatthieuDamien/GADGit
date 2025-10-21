#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classe de base pour toutes les étapes de l'autolauncher.
Définit l'interface commune et les méthodes utilitaires.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

class BaseStep(ABC):
    """
    Classe abstraite de base pour les étapes du pipeline.
    Chaque étape hérite de cette classe et implémente sa logique spécifique.
    """
    
    def __init__(self, config, events, mail_manager, pipeline_runner):
        """
        Initialise l'étape.
        
        Args:
            config: Instance de Config
            events: Instance de EventsRegister
            mail_manager: Instance de MailManager
            pipeline_runner: Instance de PipelineRunner
        """
        self.config = config
        self.events = events
        self.mail = mail_manager
        self.pipeline = pipeline_runner
        self.step_name = self.__class__.__name__.lower()
    
    @abstractmethod
    def execute(self, input_dir: str) -> bool:
        """
        Exécute l'étape du pipeline.
        
        Args:
            input_dir: Répertoire d'entrée pour cette étape
        
        Returns:
            True si l'étape s'est exécutée avec succès
        """
        pass
    
    def log_start(self, input_dir: str) -> None:
        """Log le début de l'étape."""
        logging.info(f"=== Début de l'étape: {self.step_name} ===")
        logging.info(f"Répertoire d'entrée: {input_dir}")
    
    def log_end(self, success: bool) -> None:
        """Log la fin de l'étape."""
        status = "succès" if success else "échec"
        logging.info(f"=== Fin de l'étape: {self.step_name} ({status}) ===")
    
    def handle_event(
        self,
        location: str,
        sample: str,
        event_type: str,
        error_msg: Optional[str] = None,
        send_mail: bool = True
    ) -> int:
        """
        Gère un événement (ajout au registre et notification éventuelle).
        
        Args:
            location: Localisation de l'événement
            sample: Échantillon concerné
            event_type: Type d'événement
            error_msg: Message d'erreur (si applicable)
            send_mail: Envoyer une notification mail
        
        Returns:
            Nombre de fois que l'événement s'est déjà produit
        """
        count_before = self.events.add_and_count(location, sample, event_type)
        
        # N'envoyer le mail que la première fois
        if send_mail and count_before == 0 and error_msg:
            self.mail.send_error(sample, self.step_name, error_msg)
        
        return count_before
    
    def clear_event(self, location: str, sample: str, event_type: str) -> None:
        """
        Supprime un événement du registre (problème résolu).
        
        Args:
            location: Localisation de l'événement
            sample: Échantillon concerné
            event_type: Type d'événement
        """
        self.events.delete(location, sample, event_type)
    
    def run_with_error_handling(
        self,
        func,
        location: str,
        sample: str,
        event_type: str,
        error_context: str
    ) -> bool:
        """
        Exécute une fonction avec gestion d'erreur standardisée.
        
        Args:
            func: Fonction à exécuter
            location: Localisation pour l'événement
            sample: Échantillon pour l'événement
            event_type: Type d'événement en cas d'erreur
            error_context: Contexte de l'erreur pour le message
        
        Returns:
            True si succès, False sinon
        """
        try:
            func()
            self.clear_event(location, sample, event_type)
            return True
        except Exception as e:
            error_msg = f"{error_context}: {str(e)}"
            logging.error(error_msg)
            self.handle_event(location, sample, event_type, error_msg)
            return False