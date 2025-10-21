#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gestion des fichiers de verrouillage pour éviter l'exécution simultanée.
"""

import os
import logging
from pathlib import Path


class LockManager:
    """
    Gestionnaire de fichiers de verrouillage.
    Empêche l'exécution simultanée de l'autolauncher.
    """
    
    LOCK_FILENAME = "autolaunch.lock"
    
    def __init__(self, directory: str):
        """
        Initialise le gestionnaire de verrou.
        
        Args:
            directory: Répertoire où placer le fichier de verrou
        """
        self.directory = directory
        self.base_dir = directory
        self.lock_file = os.path.join(directory, self.LOCK_FILENAME)
        self.is_locked = False
    
    def acquire(self) -> bool:
        """
        Tente d'acquérir le verrou.
        
        Returns:
            True si le verrou a été acquis, False s'il existait déjà
        """
        if os.path.isfile(self.lock_file):
            logging.warning(
                "Fichier de verrou trouvé: %s. Une opération est déjà en cours.",
                self.lock_file
            )
            return False
        
        try:
            with open(self.lock_file, 'w', encoding='utf-8') as f:
                f.write("1")
            self.is_locked = True
            logging.debug("Verrou acquis: %s", self.lock_file)
            return True
        except Exception as e:
            logging.error(f"Erreur lors de l'acquisition du verrou: %s", e)
            return False
    
    def release(self) -> bool:  # Modifier pour retourner bool
        """Libère le verrou en supprimant le fichier."""
        if self.is_locked and os.path.isfile(self.lock_file):
            try:
                os.remove(self.lock_file)
                self.is_locked = False
                logging.debug(f"Verrou libéré: {self.lock_file}")
                return True
            except Exception as e:
                logging.error(f"Erreur lors de la libération du verrou: {e}")
                return False
        return True  # Retourner True même si déjà libéré
    
    def __enter__(self):
        """Support du context manager (with statement)."""
        if not self.acquire():
            raise RuntimeError(f"Impossible d'acquérir le verrou dans {self.directory}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Libère le verrou automatiquement à la sortie du context."""
        self.release()
        return False