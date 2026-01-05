#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
lock.py

Description:
Gestion des fichiers de verrouillage pour éviter l'exécution simultanée.

Auteur: Matthieu Damien
Creation Date: 2025-10-07
Dernière modification: 2025-10-31
Commentaires:
"""

import os
import logging

# Import fcntl uniquement sur les systèmes Unix/Linux
try:
    import fcntl  # type: ignore
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    logging.warning("Module fcntl non disponible (Windows). Utilisation de fallback.")

class LockManager:
    """
    Gestionnaire de fichiers de verrouillage.
    Empêche l'exécution simultanée de l'autolauncher.

    Utilise fcntl.flock() sur Linux (verrouillage atomique) et un fallback
    sur Windows (moins robuste mais fonctionnel pour tests locaux).
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
        self._lock_fd = None  # File descriptor pour fcntl

    def acquire(self) -> bool:
        """
        Tente d'acquérir le verrou de manière atomique.

        Sur Linux: utilise fcntl.flock() pour un verrouillage exclusif atomique
        Sur Windows: utilise un fallback basé sur l'existence du fichier (race condition possible)

        Returns:
            True si le verrou a été acquis, False s'il existait déjà
        """
        if HAS_FCNTL:
            # Linux: Verrouillage atomique avec fcntl.flock()
            return self._acquire_with_fcntl()
        else:
            # Windows: Fallback (race condition possible mais acceptable pour tests locaux)
            return self._acquire_fallback()

    def _acquire_with_fcntl(self) -> bool:
        """
        Acquisition atomique du verrou avec fcntl.flock() (Linux).

        Cette méthode est thread-safe et process-safe. Le verrou est exclusif
        et automatiquement libéré si le processus se termine brutalement.

        Returns:
            True si le verrou a été acquis, False sinon
        """
        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(self.lock_file) or '.', exist_ok=True)

            # Ouvrir le fichier de verrou (créé s'il n'existe pas)
            self._lock_fd = open(self.lock_file, 'w', encoding='utf-8')

            # Tenter d'acquérir le verrou exclusif NON-BLOQUANT
            # LOCK_EX = verrou exclusif, LOCK_NB = non-bloquant
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # type: ignore

            # Écrire le PID du processus dans le fichier (pour debug)
            self._lock_fd.write(f"{os.getpid()}\n")
            self._lock_fd.flush()

            self.is_locked = True
            logging.debug("Verrou acquis (fcntl): %s [PID=%d]", self.lock_file, os.getpid())
            return True

        except BlockingIOError:
            # Le verrou est déjà pris par un autre processus
            if self._lock_fd:
                self._lock_fd.close()
                self._lock_fd = None
            logging.warning(
                "Fichier de verrou déjà acquis: %s. Une opération est déjà en cours.",
                self.lock_file
            )
            return False

        except (IOError, OSError) as e:
            if self._lock_fd:
                self._lock_fd.close()
                self._lock_fd = None
            logging.error("Erreur lors de l'acquisition du verrou (fcntl): %s", e)
            return False

    def _acquire_fallback(self) -> bool:
        """
        Fallback pour Windows (race condition possible).

        Cette méthode n'est PAS atomique et peut souffrir de race conditions,
        mais elle est suffisante pour les tests locaux sur Windows.

        Returns:
            True si le verrou a été acquis, False sinon
        """
        if os.path.isfile(self.lock_file):
            logging.warning(
                "Fichier de verrou trouvé: %s. Une opération est déjà en cours.",
                self.lock_file
            )
            return False

        try:
            # Créer le répertoire parent si nécessaire
            os.makedirs(os.path.dirname(self.lock_file) or '.', exist_ok=True)

            with open(self.lock_file, 'w', encoding='utf-8') as f:
                f.write(f"{os.getpid()}\n")
            self.is_locked = True
            logging.debug("Verrou acquis (fallback): %s [PID=%d]", self.lock_file, os.getpid())
            return True
        except (IOError, OSError) as e:
            logging.error("Erreur lors de l'acquisition du verrou (fallback): %s", e)
            return False

    def release(self) -> bool:
        """
        Libère le verrou.

        Returns:
            True si succès, False en cas d'erreur
        """
        if not self.is_locked:
            return True  # Déjà libéré

        if HAS_FCNTL and self._lock_fd:
            # Linux: Libérer le verrou fcntl et fermer le file descriptor
            try:
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)  # type: ignore
                self._lock_fd.close()
                self._lock_fd = None
                logging.debug("Verrou libéré (fcntl): %s", self.lock_file)
            except (IOError, OSError) as e:
                logging.error("Erreur lors de la libération du verrou (fcntl): %s", e)
                return False

        # Supprimer le fichier de verrou
        if os.path.isfile(self.lock_file):
            try:
                os.remove(self.lock_file)
                self.is_locked = False
                logging.debug("Fichier de verrou supprimé: %s", self.lock_file)
                return True
            except (IOError, OSError) as e:
                logging.error("Erreur lors de la suppression du verrou: %s", e)
                return False

        self.is_locked = False
        return True

    def __enter__(self):
        """Support du context manager (with statement)."""
        if not self.acquire():
            raise RuntimeError(f"Impossible d'acquérir le verrou dans {self.directory}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        """Libère le verrou automatiquement à la sortie du context."""
        self.release()
        return False
