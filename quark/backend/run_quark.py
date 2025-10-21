#!/usr/bin/env python3
"""
Script de lancement de Quark en mode ponctuel (sans daemon)
À appeler via cron ou manuellement
"""

import sys
import logging
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
    # Configuration
    scheduler = QuarkScheduler(
        host='login-1.mesobfc.fr',
        username='umw040ir',
        password='PaeDaegh5uiX'
    )
    # Lancer un cycle
    try:
        scheduler.run_cycle()
        return 0
    except Exception as e:
        logging.error("Erreur critique: %s", e)
        return 1

if __name__ == '__main__':
    sys.exit(main())
