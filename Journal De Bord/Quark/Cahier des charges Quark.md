## 1. Contexte et Objectifs

L'orchestrateur **Quark** est une solution d'orchestration avancée conçue pour optimiser la gestion dynamique de pipelines bioinformatiques sur un cluster HPC dans un environnement hospitalier. Il doit permettre le lancement, le suivi et l'optimisation automatique des analyses génomiques (génome, exome, dépistage néonatal) en tenant compte des ressources disponibles et des priorités cliniques.

### Objectifs principaux

- **Intégration système** : Communication native avec LabKey et SLURM
- **Orchestration dynamique** : Gestion intelligente des ressources et des priorités
- **Traçabilité complète** : Logging détaillé de chaque action sur chaque échantillon
- **Interface utilisateur** : Dashboard web (React) pour le suivi temps réel
- **Optimisation automatique** : Allocation intelligente des ressources selon la disponibilité

## 2. Architecture Technique

### 2.1 Infrastructure

- **Environnement d'exécution** : Conteneur Singularity
- **Backend** : Python (architecture modulaire)
- **Frontend** : Interface React
- **Base de données** : Système de logs JSON + fichiers de suivi par échantillon
- **Communication** : API REST pour intégrations externes

### 2.2 Composants principaux

- **Core Engine** : Moteur d'orchestration principal
- **Resource Manager** : Gestionnaire de ressources HPC
- **Workflow Parser** : Analyseur de configurations JSON
- **Logger System** : Système de traçabilité
- **Web Interface** : Interface de monitoring
- **Integration Layer** : Couche d'intégration (LabKey, SLURM)

## 3. Spécifications Fonctionnelles

### 3.1 Système de Logging par Échantillon

#### 3.1.1 Structure des logs

Pour chaque échantillon, création d'un fichier de log dédié contenant :

- **Date début** : Timestamp de début d'exécution de l'étape
- **Date fin** : Timestamp de fin d'exécution
- **Étape** : Identification de l'étape du pipeline
- **Code sortie** : Code de retour de l'exécution
- **Log correspondant** : Chemin vers les logs détaillés
- **Machine d'exécution** : Identification du nœud HPC utilisé

#### 3.1.2 Format de log

```json
{
  "sample_id": "PEDXXXXX.1",
  "workflow": "genome_analysis",
  "steps": [
    {
      "step_name": "alignment",
      "start_time": "2025-09-04T08:30:00Z",
      "end_time": "2025-09-04T12:45:00Z",
      "exit_code": 0,
      "log_path": "/path/to/alignment.log",
      "execution_node": "node-gpu-01",
      "resources_used": {
        "cpu_cores": 16,
        "memory_gb": 64,
        "gpu_count": 1
      }
    }
  ]
}
```

### 3.2 Communication avec LabKey

#### 3.2.1 Récupération des informations échantillons

- **Connexion sécurisée** à LabKey Translational
- **Récupération automatique** des métadonnées patients
- **Support des identifiants** : `PEDXXXXX`, `djnbsXXX`, `djen`, `djex`
- **Synchronisation** des statuts d'analyse

#### 3.2.2 Récupération des informations processus

- **Configuration des workflows** selon le type d'analyse
- **Paramètres spécifiques** par type d'échantillon
- **Priorités cliniques** et contraintes temporelles

### 3.3 Communication avec SLURM

#### 3.3.1 Gestion des quotas et ressources

- **Monitoring temps réel** des ressources disponibles
- **Récupération des informations** : CPU, mémoire, GPU, files d'attente
- **Utilisation de PySlurmUtils** avec extension pour données manquantes

#### 3.3.2 Gestion des jobs

- **Soumission automatique** des jobs avec paramètres optimisés
- **Monitoring continu** de l'état des jobs
- **Gestion des dépendances** entre étapes
- **Relance automatique** en cas d'échec (jusqu'à 3-4 tentatives)

### 3.4 Parser de Configuration JSON

#### 3.4.1 Analyse des workflows

- **Parsing des fichiers JSON** de configuration de pipeline
- **Validation** de la structure et des dépendances
- **Génération automatique** des paramètres de lancement

#### 3.4.2 Modification dynamique

- **Adaptation des paramètres** selon les ressources disponibles
- **Personnalisation** par type d'échantillon
- **Optimisation** des scripts de lancement

### 3.5 Interface HTML de Suivi

#### 3.5.1 Dashboard principal

- **Vue d'ensemble** de tous les pipelines en cours
- **Colorisation** par statut :
    - 🟢 Terminé avec succès
    - 🟡 En cours d'exécution
    - 🔴 Échec
    - ⚪ En attente
    - 🔵 En pause (à voir)

#### 3.5.2 Visualisation graphique

- **Graphe des pipelines** avec représentation des étapes
- (**Diagramme de Gantt** pour le suivi temporel)
- **Métriques de performance** par étape
- **Alertes stockées appart**

### 3.6 Optimisation des Ressources

#### 3.6.1 Allocation dynamique

- **Calcul automatique** du nombre de cœurs optimal
- **Gestion intelligente** des GPU
- **Parallélisation** selon le nombre d'échantillons
- **Équilibrage** de la charge sur le cluster

#### 3.6.2 Stratégies d'optimisation

- **Regroupement de jobs** : Consolidation des tâches similaires
- **Priorisation intelligente** selon les contraintes cliniques
- **Adaptation en temps réel** aux ressources disponibles

### 3.7 Système de Notification

#### 3.7.1 Événements de notification

- **Fin de run** : Notification de completion
- **Échec récurrent** : Alerte après plusieurs tentatives
- **Archivage** : Confirmation des opérations d'archivage
- **Lancement** : Confirmation de démarrage des analyses

#### 3.7.2 Canaux de communication

- **Email** avec templates personnalisables
- **Interface web** avec notifications push
- **Logs structurés** pour intégration avec systèmes externes

## 4. Spécifications Avancées

### 4.1 Système de Connexion Générique

#### 4.1.1 Multi-sessions

- **Support de multiples sessions** Quark simultanées
- **Isolation des environnements** par utilisateur/projet
- **Gestion des permissions** et des accès

#### 4.1.2 Traçabilité des utilisateurs

- **Logging des actions** par utilisateur
- **Gestion des changements d'astreinte**
- **Audit trail** complet des opérations

### 4.2 Lancement par Groupes

#### 4.2.1 Groupes temporels

- **Batching** par fenêtre de temps
- **Priorisation** selon l'urgence clinique
- **Optimisation** des ressources par groupe

#### 4.2.2 Groupes fonctionnels

- **Regroupement** par étape d'analyse
- **Parallélisation** des étapes compatibles
- **Synchronisation** des dépendances

### 4.3 Regroupement et Consolidation

#### 4.3.1 Optimisation des slots

- **Consolidation** : 48 cœurs non-MPI → 1 slot MPI 48 cœurs
- **Réduction** de l'encombrement des files d'attente
- **Amélioration** du throughput global

#### 4.3.2 Stratégies de regroupement

- **Analyse des patterns** d'utilisation
- **Regroupement intelligent** des tâches similaires
- **Optimisation** des temps d'attente

### 4.4 Intelligence Artificielle (Roadmap Future)

#### 4.4.1 Calcul des priorités

- **Entraînement** sur l'historique des analyses
- **Prédiction** des temps d'exécution
- **Optimisation** automatique des paramètres

#### 4.4.2 Apprentissage automatique

- **Analyse des patterns** de performance
- **Prédiction des échecs** potentiels
- **Optimisation continue** des stratégies

## 5. Architecture des Données

### 5.1 Structure des fichiers

```
/quark_data/
├── samples/
│   ├── PEDXXXXX.1/
│   │   ├── workflow.log
│   │   ├── steps/
│   │   └── outputs/
├── configs/
│   ├── workflows/
│   └── templates/
├── logs/
│   ├── system/
│   └── access/
└── reports/
    ├── daily/
    └── monthly/
```

### 5.2 Base de données

- **SQLite** pour les métadonnées
- **JSON** pour les configurations
- **Fichiers plats** pour les logs détaillés

## 6. Interfaces et API

### 6.1 Interface en ligne de commande

```bash
quark start                    # Démarrage du système
quark status                   # État général
quark submit <workflow> <sample> # Soumission manuelle
quark monitor <job_id>         # Monitoring spécifique
quark report <period>          # Génération de rapports
```

### 6.2 API REST

- **GET /api/status** : État du système
- **POST /api/submit** : Soumission de job
- **GET /api/jobs** : Liste des jobs
- **GET /api/samples/{id}** : Détails échantillon
- **POST /api/notifications** : Configuration des alertes

### 6.3 Interface Web

- **Dashboard** principal avec métriques temps réel
- **Pages détaillées** par échantillon
- **Configuration** des paramètres
- **Rapports** interactifs

## 7. Exigences Non Fonctionnelles

### 7.1 Performance

- **Scalabilité** : Support de centaines d'échantillons simultanés
- **Latence** : Temps de réponse < 5 secondes pour les opérations courantes
- **Disponibilité** : 99.5% de temps de fonctionnement

### 7.2 Sécurité

- **Authentification** robuste
- **Chiffrement** des communications
- **Audit trail** complet
- **Conformité** aux standards hospitaliers

### 7.3 Fiabilité

- **Tolérance aux pannes** avec recovery automatique
- **Backup** automatique des configurations et logs
- **Monitoring** proactif des composants critiques

## 8. Plan de Développement

### 8.1 Phase 1 - Core & Interface (3-4 mois)

- Moteur d'orchestration principal
- Intégration SLURM et LabKey
- Système de logging
- Dashboard web
- API REST
- Système de notifications

### 8.3 Phase 2 - Optimisation (2-3 mois)

- Algorithmes d'optimisation
- Regroupement intelligent
- Métriques avancées

### 8.4 Phase 4 - IA (6+ mois, futur)

- Module d'apprentissage automatique
- Prédiction des performances
- Optimisation prédictive

## 9. Tests et Validation

### 9.1 Tests unitaires

- Couverture > 90% du code
- Tests d'intégration avec SLURM/LabKey
- Tests de performance

### 9.2 Tests d'acceptation

- Validation avec cas réels
- Tests de montée en charge
- Validation des workflows cliniques

## 10. Maintenance et Support

### 10.1 Documentation

- Documentation technique complète
- Guides utilisateur
- Procédures d'exploitation

### 10.2 Support

- Monitoring proactif
- Procédures d'escalade
- Plan de maintenance préventive