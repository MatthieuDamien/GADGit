# Autolauncher - Orchestrateur de Pipeline Bioinformatique

## Vue d'ensemble

L'autolauncher est un orchestrateur Python qui automatise l'exécution des pipelines bioinformatiques sur le cluster de calcul. Il gère le lancement séquentiel de plusieurs étapes, depuis la concaténation des FASTQ jusqu'au suivi des analyses et de l'archivage.

## Architecture

La nouvelle structure modulaire facilite la maintenance, le débogage et l'évolution du code :

```
autolauncher/
├── config.py              # Configuration centralisée
├── events.py              # Gestion des événements et compteurs
├── mail.py                # Notifications par email
├── lock.py                # Système de verrous (évite exécutions simultanées)
├── utils.py               # Fonctions utilitaires génériques
├── subprocess_runner.py   # Exécution de sous-processus
├── main.py                # Point d'entrée principal
└── steps/                 # Étapes du pipeline
    ├── __init__.py
    ├── base.py           # Classe abstraite de base
    ├── concat.py         # Concaténation des FASTQ
    ├── organize.py       # Organisation en dossiers
    ├── infofile.py       # Création fichier d'info
    ├── analysis.py       # Lancement analyses
    └── check.py          # Vérification et suivi
```

## Flux des étapes

```
NovaSeqX → [1. concat] → incoming/
                 ↓
           [2. organize] → incoming/organize/
                 ↓
           [3. infofile] → sample_correspondance.info
                 ↓
           [4. analysis] → analyse/PED*/
                 ↓
           [5. check] → Surveillance continue
```

## Utilisation

### 1. Étape de concaténation

Concatène les fichiers FASTQ par lane pour chaque flowcell NovaSeq X :

```bash
python3 main.py -d /path/to/seq1/ --concat
```

**Prérequis** :

- Fichier `concat.list` dans le répertoire d'entrée
- Flowcells dans des dossiers nommés `2*`
- Fichier `CopyComplete.txt` dans chaque run

**Sorties** :

- FASTQ concaténés dans `/work/work/shared/s-neomics/data/incoming/`
- Logs dans `incoming/logs/concat/`

### 2. Étape d'organisation

Organise les FASTQ en dossiers d'échantillons après vérification de la structure familiale :

```bash
python3 main.py -d /path/to/incoming/ --organize
```

**Vérifications effectuées** :

- Paires R1/R2 complètes
- Taille minimale des fichiers (>10 Mo)
- Concaténation terminée (fichiers .end)
- Structure familiale complète via LabKey
- Statut des échantillons dans LabKey

**Sorties** :

- Dossiers organisés dans `incoming/organize/`
- Fichier `samples_to_organize.list`

### 3. Étape de création du fichier d'information

Génère le fichier de métadonnées nécessaire au dispatch :

```bash
python3 main.py -d /path/to/incoming/organize/ --infofile
```

**Sorties** :

- `sample_correspondance.info` avec les métadonnées

### 4. Étape de lancement des analyses

Dispatche les échantillons vers SLURM pour analyse :

```bash
python3 main.py -d /path/to/incoming/organize/ --analysis
```

**Sorties** :

- Analyses lancées dans `/work/work/shared/s-neomics/data/analyse/`
- Logs de dispatch dans `organize/logs/`

### 5. Étape de vérification et suivi

Vérifie l'état des analyses, détecte les erreurs et surveille l'archivage :

```bash
python3 main.py -d /path/to/analyse/ --check
```

**Vérifications** :

- Dispatch réussi
- État de l'analyse (status.tsv)
- Détection des échecs
- Progression de l'archivage
- Alertes si analyses bloquées

## Options communes

```bash
python3 main.py \
  -d /path/to/directory \        # Répertoire à traiter (OBLIGATOIRE)
  -l autolauncher.log \          # Fichier de log
  -e autolauncher.events \       # Registre d'événements
  -m autolauncher_mailing.sh \   # Script de notifications
  --[étape]                      # concat|organize|infofile|analysis|check
```

## Système d'événements

Le registre d'événements (`autolauncher.events`) compte le nombre de fois qu'un problème se produit pour éviter le spam de notifications :

- **Première occurrence** : email envoyé
- **Occurrences suivantes** : compteur incrémenté, pas d'email
- **Tous les 50 événements** : alerte de potentiel blocage
- **Tous les 500 événements** (analyses non terminées) : alerte critique

### Types d'événements

**Erreurs bloquantes** :

- `concat_file_missing` : Fichier concat.list manquant
- `paired_not_found` : Fichier R1 ou R2 manquant
- `fastq_too_small` : Fichier FASTQ < 10 Mo
- `no_ped_id` : PED ID introuvable dans LabKey
- `family_missing` : Membres de famille manquants

**Événements de suivi** :

- `analysis_launched` : Analyse démarrée
- `analysis_ended` : Analyse terminée
- `analysis_ok` : Analyse réussie
- `analysis_failed` : Analyse échouée
- `archive_success` : Archivage terminé

## Débogage

### Consulter les logs

```bash
# Log principal de l'autolauncher
tail -f autolauncher.log

# Logs spécifiques par étape
tail -f incoming/logs/concat/[flowcell].concat.[date].log
tail -f incoming/organize/logs/organize_data_folder.[date].log
tail -f analyse/PED*/status.tsv
```

### Vérifier le registre d'événements

```bash
# Voir tous les événements
cat autolauncher.events

# Compter les erreurs par type
awk '{print $3}' autolauncher.events | sort | uniq -c

# Trouver les événements fréquents (>10 occurrences)
awk '$4 > 10' autolauncher.events
```

### Déblocage manuel

Si l'autolauncher est bloqué par un verrou :

```bash
# Vérifier le verrou
ls -l /path/to/directory/autolaunch.lock

# Supprimer le verrou (ATTENTION: vérifier qu'aucun processus n'est actif)
rm /path/to/directory/autolaunch.lock
```

### Réinitialiser un événement

Si un événement empêche le traitement d'un échantillon :

```bash
# Éditer le registre
nano autolauncher.events

# Supprimer ou modifier la ligne correspondante
# Format: location<TAB>sample<TAB>event_type<TAB>count
```

## Améliorations par rapport à l'ancien code

### Structure et organisation

1. **Séparation des responsabilités** : Chaque composant a un rôle clair
2. **Réutilisabilité** : Code factorisé dans des modules génériques
3. **Extensibilité** : Ajout facile de nouvelles étapes
4. **Testabilité** : Composants isolés, plus faciles à tester

### Gestion des erreurs

1. **Gestion centralisée** : Classe `BaseStep` avec méthodes communes
2. **Récupération propre** : Handlers de signaux et cleanup automatique
3. **Logging structuré** : Niveaux appropriés (INFO, WARNING, ERROR)

### Maintenance

1. **Code lisible** : Noms explicites, documentation inline
2. **Configuration centralisée** : Un seul endroit pour les paramètres
3. **Modularité** : Modification d'une étape sans toucher les autres
4. **Débogage facilité** : Logs clairs avec contexte

## Configuration

Le fichier `analysis_config_mesobfc.tsv` doit contenir :

```
pipelinebase\t/path/to/pipeline
targetlist\t/path/to/targetlist
```

Ces valeurs sont chargées automatiquement au démarrage.

## Intégration CRON

Pour automatiser l'exécution cyclique :

```cron
# Concaténation toutes les 30 minutes
*/30 * * * * cd /path/to/autolauncher && python3 main.py -d /seq1/ --concat >> concat.log 2>&1

# Organisation toutes les heures
0 * * * * cd /path/to/autolauncher && python3 main.py -d /incoming/ --organize >> organize.log 2>&1

# Vérification toutes les 15 minutes
*/15 * * * * cd /path/to/autolauncher && python3 main.py -d /analyse/ --check >> check.log 2>&1

# Exécution du script mail après chaque cycle
@hourly bash /path/to/autolauncher_mailing.sh && > /path/to/autolauncher_mailing.sh
```

## Développement futur

### Ajout d'une nouvelle étape

1. Créer un fichier `steps/nouvelle_etape.py`
2. Hériter de `BaseStep`
3. Implémenter la méthode `execute()`
4. Ajouter dans `steps/__init__.py`
5. Ajouter l'option dans `main.py`

Exemple :

```python
from .base import BaseStep

class NouvelleEtapeStep(BaseStep):
    def execute(self, input_dir: str) -> bool:
        self.log_start(input_dir)
        
        # Votre logique ici
        
        self.log_end(True)
        return True
```

### Tests unitaires

Structure recommandée :

```
tests/
├── test_config.py
├── test_events.py
├── test_utils.py
└── steps/
    ├── test_concat.py
    ├── test_organize.py
    └── ...
```

## Support

Pour toute question ou problème :

- Consulter les logs : `autolauncher.log`
- Vérifier le registre : `autolauncher.events`
- Contacter : gad-astreinte-bioinfo@u-bourgogne.fr ou matthieu.damien@icloud.com

## Licence

Propriétaire - GAD (Génétique et Anomalies du Développement)

# Ressources
## Style Python

[PEP 8](https://pep8.org/) : Guide de style officiel
Pour le debuggage manuel : [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
Utilisation de [Claude](https://claude.ai) Sonnet 4.5