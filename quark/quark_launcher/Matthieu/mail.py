#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
mail.py

Description:
Gestion des notifications email pour l'autolauncher.
Écrit les commandes mail dans un fichier shell qui sera exécuté MANUELLEMENT
ou via un wrapper externe (cron, script, etc.).

Approche inspirée de Valentin (auto_launcher_novaseqx.py):
Le script Python prépare uniquement le fichier .sh, sans l'exécuter.

Auteur: Matthieu Damien
Creation Date: 2025-10-07
Dernière modification: 2025-11-14
Commentaires:
"""

import os
import logging


class MailManager:
    """
    Gestionnaire de notifications par email.
    Écrit les commandes mail dans un script shell.

    Note: Ce gestionnaire prépare uniquement le fichier shell.
    L'exécution du script doit être faite manuellement ou via un wrapper externe.
    """

    def __init__(self, mail_file: str, recipient: str):
        """
        Initialise le gestionnaire de mails.

        Args:
            mail_file: Chemin vers le fichier script mail
            recipient: Adresse email destinataire par défaut
        """
        self.mail_file = mail_file
        self.recipient = recipient
        self.mail_bioinfo = recipient
        self._init_mail_file()

    def _init_mail_file(self) -> None:
        """Initialise le fichier de script mail."""
        # Créer le répertoire parent si nécessaire
        os.makedirs(os.path.dirname(self.mail_file) or '.', exist_ok=True)

        with open(self.mail_file, 'w', encoding='utf-8') as f:  # Ajout encoding
            f.write("#!/bin/bash\n\n")
        logging.debug("Fichier mail initialisé: %s", self.mail_file)

    def send_notification(
        self,
        target: str,
        step: str,
        comment: str,
        keyword: str = "OK",
        is_error: bool = False
    ) -> None:
        """
        Ajoute une notification au fichier mail.

        Args:
            target: Cible de la notification (sample, flowcell, etc.)
            step: Étape concernée (concat, organize, analysis, etc.)
            comment: Message détaillé
            keyword: Mot-clé pour le sujet (OK, FAIL, etc.)
            is_error: True si c'est une erreur
        """
        if is_error:
            subject = f"ERROR autolauncher: {step} step ({target})"
            body = f"Error in autolauncher for {target} - {step} process FAILED: {comment}"
        else:
            subject = f"autolauncher: {step} step {keyword} ({target})"
            body = f"Autolauncher for process: {step}, target = {target} - {comment}"

        # Écrit la commande mail dans le fichier
        with open(self.mail_file, 'a', encoding='utf-8') as f:
            f.write(f'echo -e "{body}" | mail -s "{subject}" {self.recipient}\n')

        log_level = logging.ERROR if is_error else logging.DEBUG
        logging.log(
            log_level,
            "Mail %s préparé pour %s/%s",
            "erreur" if is_error else "info",
            target,
            step
        )

    def send_error(self, target: str, step: str, comment: str) -> None:
        """
        Raccourci pour envoyer une notification d'erreur.

        Args:
            target: Cible de la notification
            step: Étape concernée
            comment: Message d'erreur
        """
        self.send_notification(target, step, comment, is_error=True)

    def send_success(self, target: str, step: str, comment: str) -> None:
        """
        Raccourci pour envoyer une notification de succès.

        Args:
            target: Cible de la notification
            step: Étape concernée
            comment: Message de succès
        """
        self.send_notification(target, step, comment, keyword="OK", is_error=False)
