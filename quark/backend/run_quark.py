#!/usr/bin/env python3
"""
Script de lancement de Quark en mode ponctuel (sans daemon)
À appeler via cron ou manuellement
"""

import sys
import logging
import os
from scripts.scheduler import QuarkScheduler

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quark.log'),
        logging.StreamHandler()
    ]
)

def main():
    '''
    Lanceur de Quark
    '''
    # Configuration via variables d'environnement avec des valeurs par défaut
    scheduler = QuarkScheduler(
        host=os.getenv('SLURM_HOST', 'login-1.mesobfc.fr'),
        username=os.getenv('SLURM_USER', 'umw040ir'),
        password=os.getenv('SLURM_PASSWORD', 'PaeDaegh5uiX')
    )
    
    logging.info("Lancement d'un cycle Quark pour l'hôte %s...", os.getenv('SLURM_HOST', 'login-1.mesobfc.fr'))
    # Lancer un cycle
    try:
        scheduler.run_cycle()
        return 0
    except Exception as e:
        logging.error("Erreur critique: %s", e)
        return 1

if __name__ == '__main__':
    sys.exit(main())
