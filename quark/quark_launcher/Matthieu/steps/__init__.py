#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
steps/__init__.py

Description:
Module contenant les différentes étapes du pipeline autolauncher.
Chaque étape hérite de BaseStep et implémente sa logique spécifique.

Auteur: Matthieu Damien
Creation Date: 2025-10-07
Dernière modification: 2025-10-31
Commentaires:
- Ajouter de nouvelles étapes si nécessaire (Enovoi à MongoDB par exemple).
"""

# pylint: disable-next=E0401
from .base import BaseStep
from .concat import ConcatStep
from .organize import OrganizeStep
from .infofile import InfofileStep
from .analysis import AnalysisStep
from .check import CheckStep

__all__ = [
    'BaseStep',
    'ConcatStep',
    'OrganizeStep',
    'InfofileStep',
    'AnalysisStep',
    'CheckStep'
]