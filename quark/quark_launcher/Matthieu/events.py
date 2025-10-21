#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gestion des événements de l'autolauncher.
Permet de tracer et compter les événements (erreurs, succès, etc.)
"""

import logging
from typing import List, Tuple, Set
from pathlib import Path


class EventsRegister:
    """
    Registre des événements de l'autolauncher.
    Permet de compter le nombre de fois qu'un événement se produit
    pour éviter les spams de notifications.
    """
    
    # Types d'événements reconnus (catégorisés)
    EVENT_TYPES = {
        "erreurs_et_echecs": [
            "concat_file_missing", "concat_ambiguity", "concat_subprocess_fail",
            "paired_not_found", "fastq_too_small", "no_ped_id", "family_missing",
            "organize_subprocess_fail", "spl_corresp_file_missing",
            "infofile_subprocess_fail", "missing_dijex_id",
            "dismissed_family_members", "labkey_status_bad", "analysis_launch_fail",
            "archive_fail", "no_dispatch", "analysis_failed"
        ],
        "succes_et_validations": [
            "analysis_launched", "found_in_organize", "archive_success",
            "infofile_sucess", "dispatch_ok", "analysis_ok", "analysis_ended"
        ],
        "etats_intermediaires_ou_neutres": [
            "lockfile_found", "already_analyzed", "archive_in_progress",
            "no_archive_log", "analysis_not_ended"
        ]
    }
    
    def __init__(self, event_file: str):
        """
        Initialise le registre depuis un fichier.
        
        Args:
            event_file: Chemin vers le fichier d'événements
        """
        self.event_file = event_file
        self.loaded = False
        self.registration_fail = False
        
        # Aplatir le dictionnaire pour obtenir tous les types valides
        self._valid_event_types: Set[str] = set()
        for category_events in self.EVENT_TYPES.values():
            self._valid_event_types.update(category_events)
        
        # Listes parallèles pour stocker les événements
        self.location_list: List[str] = []
        self.sample_list: List[str] = []
        self.type_list: List[str] = []
        self.counter_list: List[int] = []
        self.event_list: List[str] = []
        
        self.load()
    
    def load(self) -> None:
        """Charge les événements depuis le fichier."""
        try:
            with open(self.event_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split("\t")
                    if len(parts) != 4:
                        continue
                    
                    location, sample, event_type, counter = parts
                    try:
                        counter_int = int(counter)
                    except ValueError:
                        logging.error(f"Compteur invalide pour événement: {line}")
                        continue
                        
                    self.location_list.append(location)
                    self.sample_list.append(sample)
                    self.type_list.append(event_type)
                    self.counter_list.append(counter_int)
                    self.event_list.append(self._format_event(location, sample, event_type))
            
            self.loaded = True
            self.registration_fail = "registration_fail" in self.location_list
            logging.info(f"Registre d'événements chargé: {len(self.event_list)} événements")
            
        except FileNotFoundError:
            # Fichier n'existe pas encore, on démarre avec un registre vide
            self.loaded = True
            logging.info("Nouveau registre d'événements créé")
        except Exception as e:
            logging.error(f"Erreur lors du chargement du registre: {e}")
            self.loaded = False
            self.registration_fail = True
    
    @staticmethod
    def _format_event(location: str, sample: str, event_type: str) -> str:
        """
        Formate un événement en string.
        
        Args:
            location: Localisation de l'événement
            sample: Échantillon concerné
            event_type: Type d'événement
        
        Returns:
            String formaté "location\tsample\tevent_type"
        """
        return f"{location}\t{sample}\t{event_type}"
    
    def add(self, location: str, sample: str, event_type: str) -> None:
        """
        Ajoute un événement ou incrémente son compteur.
        
        Args:
            location: Localisation de l'événement
            sample: Échantillon concerné
            event_type: Type d'événement
        """
        if event_type not in self._valid_event_types:
            logging.error(
                f"Type d'événement inconnu '{event_type}'. "
                f"Types valides: {', '.join(sorted(self._valid_event_types))}"
            )
            self.registration_fail = True
            return
        
        event = self._format_event(location, sample, event_type)
        
        if event in self.event_list:
            # Incrémente le compteur
            idx = self.event_list.index(event)
            self.counter_list[idx] += 1
        else:
            # Nouvel événement
            self.location_list.append(location)
            self.sample_list.append(sample)
            self.type_list.append(event_type)
            self.counter_list.append(1)
            self.event_list.append(event)
    
    def delete(self, location: str, sample: str, event_type: str) -> None:
        """
        Supprime un événement du registre.
        
        Args:
            location: Localisation de l'événement
            sample: Échantillon concerné
            event_type: Type d'événement
        """
        event = self._format_event(location, sample, event_type)
        
        if event in self.event_list:
            idx = self.event_list.index(event)
            self.location_list.pop(idx)
            self.sample_list.pop(idx)
            self.type_list.pop(idx)
            self.counter_list.pop(idx)
            self.event_list.pop(idx)
    
    def count(self, location: str, sample: str, event_type: str) -> int:
        """
        Compte le nombre de fois qu'un événement s'est produit.
        
        Args:
            location: Localisation de l'événement
            sample: Échantillon concerné
            event_type: Type d'événement
        
        Returns:
            Nombre d'occurrences
        """
        event = self._format_event(location, sample, event_type)
        if event in self.event_list:
            idx = self.event_list.index(event)
            return self.counter_list[idx]
        return 0
    
    def add_and_count(self, location: str, sample: str, event_type: str) -> int:
        """
        Ajoute un événement et retourne le nombre de fois qu'il s'est produit avant.
        Utile pour décider d'envoyer ou non un email.
        
        Args:
            location: Localisation de l'événement
            sample: Échantillon concerné
            event_type: Type d'événement
        
        Returns:
            Nombre d'occurrences avant ajout
        """
        count_before = self.count(location, sample, event_type)
        self.add(location, sample, event_type)
        return count_before
    
    def get_all_events(self) -> List[Tuple[str, int]]:
        """
        Retourne tous les événements avec leurs compteurs.
        
        Returns:
            Liste de tuples (event_string, count)
        """
        return list(zip(self.event_list, self.counter_list))
    
    def get_event_category(self, event_type: str) -> str:
        """
        Retourne la catégorie d'un événement.
        
        Args:
            event_type: Type d'événement
            
        Returns:
            Nom de la catégorie ou "unknown"
        """
        for category, events in self.EVENT_TYPES.items():
            if event_type in events:
                return category
        return "unknown"
    
    def get_events_by_category(self, category: str) -> List[Tuple[str, int]]:
        """
        Retourne tous les événements d'une catégorie donnée.
        
        Args:
            category: Nom de la catégorie
            
        Returns:
            Liste de tuples (event_string, count) pour cette catégorie
        """
        if category not in self.EVENT_TYPES:
            logging.warning(f"Catégorie inconnue: {category}")
            return []
        
        category_events = []
        for event, count in zip(self.event_list, self.counter_list):
            event_type = event.split("\t")[2]
            if event_type in self.EVENT_TYPES[category]:
                category_events.append((event, count))
        
        return category_events
    
    def get_statistics(self) -> dict:
        """
        Retourne des statistiques sur les événements par catégorie.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        stats = {
            "total_events": len(self.event_list),
            "categories": {}
        }
        
        for category in self.EVENT_TYPES.keys():
            category_events = self.get_events_by_category(category)
            stats["categories"][category] = {
                "count": len(category_events),
                "total_occurrences": sum(count for _, count in category_events)
            }
        
        return stats
    
    def test_integrity(self) -> bool:
        """
        Vérifie l'intégrité du registre.
        
        Returns:
            True si le registre est cohérent
        """
        lists_lengths = [
            len(self.location_list),
            len(self.sample_list),
            len(self.type_list),
            len(self.counter_list),
            len(self.event_list)
        ]
        
        if len(set(lists_lengths)) > 1:
            self.registration_fail = True
            logging.error("Incohérence détectée dans le registre d'événements")
            return False
        return True
    
    def save(self) -> None:
        """Sauvegarde le registre dans le fichier."""
        try:
            with open(self.event_file, 'w', encoding='utf-8') as f:
                for event, count in zip(self.event_list, self.counter_list):
                    f.write(f"{event}\t{count}\n")
            logging.debug(f"Registre sauvegardé: {self.event_file}")
        except Exception as e:
            logging.error("Erreur lors de la sauvegarde du registre: %s", e)


def create_events_register(event_file: str, backup_limit: int = 10) -> EventsRegister:
    """
    Crée un registre d'événements avec gestion des backups.
    
    Args:
        event_file: Chemin vers le fichier d'événements
        backup_limit: Nombre maximum de fichiers backup à essayer
    
    Returns:
        Instance de EventsRegister
    """
    events = EventsRegister(event_file)
    
    if events.loaded:
        logging.info("Registre d'événements chargé: %s", event_file)
        return events
    
    # Essayer les fichiers backup
    for i in range(1, backup_limit + 1):
        backup_file = f"{event_file}.{i}.bak"
        events = EventsRegister(backup_file)
        
        if events.loaded:
            logging.warning(
                "Registre principal corrompu, backup utilisé: %s", backup_file
            )
            return events
    
    # Échec total
    raise RuntimeError(
        f"Impossible de charger le registre d'événements après {backup_limit} tentatives"
    )