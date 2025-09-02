## Contexte et Objectifs
L'orchestrateur **Quark** est conçu pour optimiser la gestion des tâches et des ressources sur un cluster informatique dans un environnement hospitalier. Il doit s'exécuter dans un conteneur **Singularity** et repose sur une architecture **back-end Python** et **front-end React**, tout en restant accessible en ligne de commande (bash).

L'objectif principal est de **surveiller, planifier et exécuter** des pipelines de traitement de données médicales (ex : dépistage néonatal, exome, génome) en tenant compte des contraintes techniques et des priorités cliniques.

---
## Fonctionnalités Clés

### Surveillance et Récupération des Données
Quark doit **interroger régulièrement l'état du cluster** (files d'attente, nœuds disponibles, ressources CPU/GPU/mémoire) via **SLURM**. La bibliothèque **PySlurmUtils** sera utilisée pour récupérer les informations des queues et des ressources. Si cette bibliothèque ne permet pas de récupérer certaines données (GPU/mémoire/CPU), un développement spécifique sera nécessaire pour interpréter les logs SLURM (fichiers `.oXXXXXXX`).

### Planification Intelligente des Tâches
Quark doit **planifier et soumettre des tâches** en fonction :
- Des **ressources disponibles** (ex : allouer plus de GPU/mémoire si une seule tâche est en cours).
- Des **contraintes des pipelines** (dépendances, priorités).
- Des **identifiants patients** (format `PEDXXXXX` pour une famille, `PEDXXXXX.1` pour un individu, ou `djnbsXXX` pour les patients désanonymisables via LabKey Translational).

### Gestion des Échecs et Logs
- **Relancer automatiquement** les tâches en échec (jusqu'à 3-4 tentatives).
- **Analyser les logs** pour identifier les causes d'échec (ex : code de sortie via `get_exit_code.py`).
- **Optimiser le stockage des logs** : Éviter la redondance et centraliser les informations pertinentes (ex : logs par échantillon, qualité des données `/QC`).

### Intégration avec LabKey Translational
Quark doit **se connecter à LabKey Translational** pour :
- Récupérer les données patients (ex : `djen` pour génome, `djex` pour exome, `djenbs` pour dépistage néonatal).
- Synchroniser les processus à appliquer en fonction des informations cliniques.

---
## Architecture Technique

### Back-end Python
- **Communication avec SLURM** : Soumission de requêtes et récupération des états du cluster.
- **Traitement des logs** : Analyse des fichiers `.oXXXXXXX` et extraction des codes de sortie.
- **Connexion à LabKey** : Récupération des données patients et des processus associés.

### Front-end React
- **Visualisation** : État du cluster, suivi des tâches, accès aux logs et rapports.
- **Interface utilisateur** : Permettre aux utilisateurs de configurer les priorités et de consulter les résultats.

### Conteneurisation
**Singularity** : Assurer la portabilité et l'isolation de l'environnement d'exécution.

---
## Cas d'Usage
1. **Lancement** : Initialiser Quark, vérifier les connexions (SLURM, LabKey).
2. **Surveillance** : Récupérer l'état du cluster et planifier les tâches en fonction des ressources disponibles.
3. **Exécution** : Soumettre les tâches, relancer automatiquement en cas d'échec, et analyser les logs.
4. **Reporting** : Générer des rapports synthétiques pour le suivi des pipelines (ex : qualité des données `/QC`).

---

 Comment définir et ajuster dynamiquement les priorités entre les tâches  ?
	Listes de priorité ? `Liste_Prio_Urgent = []; Liste_Prio_Normale = []`
