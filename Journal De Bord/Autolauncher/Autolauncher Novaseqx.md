## Structure principale

- Vue d'ensemble de l'architecture
- Les 5 modes d'exécution (`--concat`, `--organize`, `--infofile`, `--analysis`, `--check`)
- Le flux de données entre les différentes étapes

## Points clés couverts

- **Système de sécurité** : verrouillage, gestion d'erreurs, signaux
- **Gestion d'événements** : tracking des problèmes récurrents avec 29 types d'événements
- **Notifications automatiques** : système d'emails pour succès/échecs
- **Intégration LabKey** : interrogation de la base de données pour validation des échantillons

## Ordre d'exécution typique

1. **Concat** : Traite les flowcells brutes
2. **Organize** : Valide et organise les échantillons par famille
3. **Infofile** : Crée les fichiers de correspondance
4. **Analysis** : Lance les analyses
5. **Check** : Surveille l'état et l'archivage

---

# Documentation - Auto Launcher NovaSeq X

## Vue d'ensemble

Le script `auto_launcher_novaseqx.py` est un automate pour le pipeline GAD qui traite automatiquement les données de séquençage provenant du séquenceur NovaSeq X. Il exécute différentes étapes du pipeline de manière séquentielle selon les conditions requises.

## Architecture générale

### Composants principaux

- **Système de verrouillage** : Évite les exécutions multiples simultanées
- **Gestion d'événements** : Suivi et comptage des erreurs/événements
- **Système de notification** : Envoi d'emails automatiques
- **Interface LabKey** : Interrogation de la base de données des échantillons

### Fichiers de configuration

- `configfile` : Configuration principale du pipeline (`/work/work/shared/s-neomics/pipeline/2.11.0/common/analysis_config_mesobfc.tsv`)
- `autolauncher.log` : Journal des opérations
- `autolauncher.events` : Registre des événements
- `autolauncher_mailing.sh` : Script de commandes email

## Étapes du pipeline

Le script fonctionne selon 5 modes d'exécution mutuellement exclusifs :

### 1. Mode `--concat`

**Objectif** : Concaténation des fichiers FASTQ depuis les dossiers de flowcell

**Processus** :

1. Recherche des dossiers flowcell (commençant par "2")
2. Vérification du fichier `concat.list` pour éviter les doublons
3. Contrôle de la présence du fichier `CopyComplete.txt`
4. Lancement du script `wrapper_concat_fastq.sh`
5. Mise à jour de `concat.list`

**Répertoires** :

- **Entrée** : Dossiers flowcell dans `INPUT_DIRECTORY`
- **Sortie** : `/work/work/shared/s-neomics/data/incoming/`

### 2. Mode `--organize`

**Objectif** : Organisation des échantillons en structure familiale

**Processus** :
1. **Validation des fichiers FASTQ** :
    - Vérification des paires R1/R2
    - Contrôle de la taille (>10MB)
    - Vérification des fichiers `.end`
2. **Interrogation LabKey** :
    - Récupération des données "Suivi exomes"
    - Validation des IDs PED et dijexID
    - Contrôle des statuts d'échantillons
3. **Analyse familiale** :
    - Recherche des membres de famille manquants
    - Exclusion des échantillons avec mauvais statut
    - Attente des échantillons familiaux complets
4. **Exécution** :
    - Création de `samples_to_organize.list`
    - Lancement de `organize_data_folder.py`

**Répertoires** :

- **Entrée** : `/work/work/shared/s-neomics/data/incoming/`
- **Sortie** : `INPUT_DIRECTORY/organize/`

### 3. Mode `--infofile`

**Objectif** : Création/mise à jour du fichier de correspondance des échantillons

**Processus** :

1. Détection des répertoires d'échantillons
2. Génération de `samples_to_infofile.list`
3. Exécution de `wrapper_create_sample_information_file.sh`
4. Production de `sample_correspondance.info`

**Répertoires** :

- **Entrée/Sortie** : `INPUT_DIRECTORY`

### 4. Mode `--analysis`

**Objectif** : Lancement de l'analyse des échantillons prêts

**Processus** :

1. Lecture de `sample_correspondance.info`
2. Lancement de `dispatch_sample_and_mv.py`
3. Dispatch vers le répertoire d'analyse

**Répertoires** :

- **Entrée** : `INPUT_DIRECTORY`
- **Sortie** : `/work/work/shared/s-neomics/data/analyse/`

### 5. Mode `--check`

**Objectif** : Vérification de l'état des analyses et archivage

**Processus** :

1. **Contrôle du dispatch** :
    
    - Vérification de la présence des échantillons dans les dossiers d'analyse
2. **Contrôle de l'analyse** :
    
    - Parsing du fichier `status.tsv`
    - Détection des échecs/succès d'analyse
3. **Contrôle de l'archivage** :
    
    - Analyse du fichier `archive.log`
    - Suivi de l'état d'archivage
4. **Contrôle des événements** :
    
    - Surveillance du nombre d'événements anormaux
    - Envoi d'alertes si nécessaire

**Répertoires** :

- **Entrée** : `/work/work/shared/s-neomics/data/analyse/`

## Système de gestion d'événements

### Classe `events_register`

Gère le suivi et la persistance des événements du système.

**Types d'événements surveillés** :

- `lockfile_found` : Fichier de verrouillage détecté
- `concat_file_missing` : Fichier concat.list manquant
- `fastq_too_small` : Fichier FASTQ trop petit
- `family_missing` : Membres de famille manquants
- `analysis_launched` : Analyse lancée avec succès
- `archive_success` : Archivage réussi
- Et 23 autres types d'événements...

**Fonctionnalités** :

- Comptage automatique des occurrences
- Persistance dans fichier
- Système de sauvegarde avec fichiers `.bak`

## Système de notification

### Fonction `send_mail`

Génère des commandes email dans le script `autolauncher_mailing.sh`.

**Types de notifications** :

- **Succès** : Étapes terminées avec succès
- **Erreurs** : Échecs de processus
- **Alertes** : Événements anormaux répétés

**Destinataire** : `gad-astreinte-bioinfo@u-bourgogne.fr`

## Gestion des erreurs et sécurité

### Mécanismes de protection

1. **Verrouillage** : Fichier `autolaunch.lock` pour éviter les exécutions simultanées
2. **Gestion des signaux** : Capture SIGTERM pour nettoyage propre
3. **Gestionnaire d'exceptions** : Log automatique des erreurs non gérées
4. **Fonction de sortie** : Nettoyage automatique à la fin du programme

### Récupération d'erreurs

- Tentative de récupération avec fichiers de sauvegarde
- Système d'événements pour tracking des problèmes récurrents
- Notifications automatiques des administrateurs

## Utilisation

```bash
# Étape 1 : Concaténation
python3 auto_launcher_novaseqx.py -d /path/to/flowcells --concat

# Étape 2 : Organisation
python3 auto_launcher_novaseqx.py -d /work/work/shared/s-neomics/data/incoming --organize

# Étape 3 : Fichier d'information
python3 auto_launcher_novaseqx.py -d /work/work/shared/s-neomics/data/incoming/organize --infofile

# Étape 4 : Analyse
python3 auto_launcher_novaseqx.py -d /work/work/shared/s-neomics/data/incoming/organize --analysis

# Étape 5 : Vérification
python3 auto_launcher_novaseqx.py -d /work/work/shared/s-neomics/data/analyse --check
```

## Dépendances

- **Python 3.9+**
- **LabKey API v1.4.0+**
- **Client mail système**
- **Accès aux scripts du pipeline GAD**

## Monitoring et maintenance

### Fichiers de log à surveiller

- `autolauncher.log` : Log principal
- `autolauncher.events` : Registre des événements
- `autolauncher_mailing.sh` : Commandes email générées

### Indicateurs de dysfonctionnement

- Événements répétés (>50 occurrences)
- Fichiers de verrouillage persistants
- Échecs de connexion LabKey
- Analyses bloquées (`analysis_not_ended`)

Le système est conçu pour être robuste et auto-diagnostique, avec des mécanismes de récupération automatique et des notifications proactives des problèmes.