# Développement d’un orchestrateur Python pour le lancement dynamique de pipelines bioinformatiques sur un cluster HPC

**Description :**  
L’objectif de ce stage est de développer un outil en Python capable d’orchestrer automatiquement le lancement de pipelines bioinformatiques (par exemple : alignement, appel de variants, annotation) en fonction des ressources disponibles sur un cluster de calcul (SLURM ou autre). L’orchestrateur devra :  
- Interroger régulièrement l’état du cluster (files d’attente, nœuds disponibles, mémoire/CPU/GPU)  
- Planifier et soumettre des tâches en tenant compte des contraintes de chaque pipeline (ressources, dépendances, priorité)  
- Suivre l’exécution des jobs et relancer si besoin en cas d’erreur  
- Générer des logs et un reporting synthétique

Ce projet vise à améliorer la robustesse et la réactivité des traitements bioinformatiques dans un contexte multi-projets.  

**Compétences clés :**
- Programmation Python (gestion de processus, interfaces système)  
- Connaissance d’un système de gestion de cluster (SLURM, PBS, etc.)  
- Bases en administration système Linux  
- Notions de pipelines bioinformatiques (Snakemake, Nextflow ou équivalent)  
- Bonnes pratiques de développement (logs, tests, documentation)