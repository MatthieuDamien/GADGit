# Guide de migration - Ancien vers nouveau code

## Comparaison de la structure

### Ancien code (monolithique)

```
auto_launcher_novaseqx.py    # 800+ lignes, tout dans un fichier
├── Variables globales
├── Fonctions utilitaires
├── Classe events_register
├── Étape concat   (inline)
├── Étape organize (inline)
├── Étape infofile (inline)
├── Étape analysis (inline)
└── Étape check    (inline)
```

### Nouveau code (se veut modulaire)

```
autolauncher/
├── config.py             # Configuration (50 lignes)
├── events.py             # Gestion événements (180 lignes)
├── mail.py               # Notifications (70 lignes)
├── lock.py               # Verrous (60 lignes)
├── utils.py              # Utilitaires (150 lignes)
├── subprocess_runner.py  # Subprocess (250 lignes)
├── main.py               # Orchestration (180 lignes)
└── steps/                # Étapes séparées (150-300 lignes chacune)
```

## Correspondances du code

### Configuration

**Ancien (lignes 23-33)** :

```python
configfile = "/work/work/shared/s-neomics/pipeline/..."
mail_bioinfo = "gad-astreinte-bioinfo@u-bourgogne.fr"
labkey_adress = "translad.chu-dijon.fr"
with open(file=configfile, mode="r") as f:
    for line in f:
        if line.startswith("pipelinebase\t"):
            pipelinebase=line.strip().split("\t")[1]
```

**Nouveau (config.py)** :

```python
class Config:
    def __init__(self, config_file: str = None):
        self.config_file = config_file or "/work/..."
        self.mail_bioinfo = "gad-astreinte-bioinfo@..."
        self._load_config()
```

### Gestion des événements

**Ancien (lignes 100-200)** :

```python
class events_register:
    def __init__(self, event_file):
        self.location_list = []
        self.sample_list = []
        # ...
    
    def add(self, event):
        event_split = event.split("\t")
        self.location_list.append(event_split[0])
        # ...
```

**Nouveau (events.py)** :

```python
class EventsRegister:
    EVENT_TYPES = [...]  # Types validés
    
    def add(self, location: str, sample: str, event_type: str):
        """Ajoute avec validation du type"""
        if event_type not in self.EVENT_TYPES:
            logging.error(f"Type inconnu: {event_type}")
```

### Notifications mail

**Ancien (lignes 85-95)** :

```python
def send_mail(target, launcherflag, comment, keyword="OK", error=False):
    if error == True:
        with open(mailFile, "a") as f:
            f.write(f"echo -e \"Error...\" | mail ...")
```

**Nouveau (mail.py)** :

```python
class MailManager:
    def send_notification(self, target, step, comment, 
                         keyword="OK", is_error=False):
        """Méthode unifiée avec paramètres clairs"""
    
    def send_error(self, target, step, comment):
        """Raccourci pour erreurs"""
```

### Étape de concaténation

**Ancien (lignes 250-350)** :

```python
if args.concat is not None:
    logging.info(f"--concat option specified...")
if args.concat is not None and unlocked_to_locked(in_dir):
    concat_file = os.path.join(in_dir, "concat.list")
    if not file_exist(concat_file):
        logging.error(...)
    flowcells = [folder for folder in glob.glob(in_dir + "/2*") ...]
    for flowcell_path in flowcells:
        # 100 lignes de logique...
```

**Nouveau (steps/concat.py)** :

```python
class ConcatStep(BaseStep):
    def execute(self, input_dir: str) -> bool:
        self.log_start(input_dir)
        if not self._check_concat_file(...):
            return False
        flowcells = self._get_flowcells(input_dir)
        for flowcell in flowcells:
            self._process_flowcell(...)
        self.log_end(True)
```

**Avantages** :

- Logique découpée en méthodes privées claires
- Gestion d'erreur centralisée
- Plus facile à tester et débugger

### Étape d'organisation avec LabKey

**Ancien (lignes 400-600)** :

```python
if args.organize is not None:
    # 200 lignes avec:
    # - Validation des FASTQ
    # - Requête LabKey inline
    # - Vérification famille
    # - Lancement subprocess
    # Tout mélangé, difficile à suivre
```

**Nouveau (steps/organize.py)** :

```python
class OrganizeStep(BaseStep):
    def execute(self, input_dir: str) -> bool:
        fastq_files = self._get_fastq_files(input_dir)
        valid, invalid = self._validate_fastq_files(...)
        ready, waiting = self._check_family_structure(...)
        return self._launch_organization(...)
    
    def _validate_fastq_files(self, fastq_files, input_dir):
        """Méthode dédiée à la validation"""
    
    def _check_family_structure(self, samples, input_dir):
        """Méthode dédiée à LabKey"""
```

**Avantages** :

- Chaque méthode fait une chose précise
- Logique métier séparée des détails techniques
- Facile d'ajouter des tests unitaires

**Désavantages** :

- Migration vers Labkey 4.0.1 donc il est possible que le code ne soit plus fonctionnel

### Exécution de subprocess

**Ancien (lignes 340-360)** :

```python
concat_script_path = os.path.join(pipelinebase, "common/fastq/...")
option_dict = {"INPUTDIR": ..., "OUTPUTDIR": ...}
basic_args = ["bash", concat_script_path]
sub = subprocess.run(basic_args, env={**option_dict, **os.environ}, ...)
if sub.returncode != 0:
    comment=f"concatenation step returned an error..."
    logging.error(comment)
    happened = event_count_then_add(subprocess_fail_event)
```

**Nouveau (subprocess_runner.py)** :

```python
class PipelineRunner:
    def run_concat_wrapper(self, input_dir, output_dir, log_file):
        """Méthode dédiée, réutilisable"""
        script_path = self.config.get_script_path("common/fastq/...")
        env_vars = {"INPUTDIR": input_dir, ...}
        return self.runner.run_bash_script(script_path, env_vars)
```

**Avantages** :

- Code réutilisable pour tous les subprocess
- Gestion d'erreur centralisée
- Timeout configurable (encore à revoir)
- Logging standardisé

## Tableau de correspondance des fonctions

| Ancien code | Nouveau code | Module |
|-------------|--------------|--------|
| `file_exist()` | `file_exists()` | utils.py |
| `check_output_dir()` | `ensure_directory()` | utils.py |
| `unlocked_to_locked()` | `LockManager.acquire()` | lock.py |
| `string_in_file()` | `string_in_file()` | utils.py |
| `arg_file_check()` | `get_or_create_file()` | utils.py |
| `send_mail()` | `MailManager.send_notification()` | mail.py |
| `format_event()` | `EventsRegister._format_event()` | events.py |
| `event_count_then_add()` | `EventsRegister.add_and_count()` | events.py |
| `event_number_control()` | `CheckStep._check_event_counts()` | steps/check.py |

## Migration étape par étape

### 1. Préparation

```bash
# Sauvegarder l'ancien code
cp auto_launcher_novaseqx.py auto_launcher_novaseqx.py.backup

# Créer la nouvelle structure
mkdir -p autolauncher/steps
cd autolauncher
```

### 2. Copier les nouveaux fichiers

```bash
# Copier tous les fichiers .py créés
# Vérifier les imports
python3 -m py_compile *.py steps/*.py
```

### 3. Tester en parallèle

```bash
# Ancien code (continuer à utiliser)
python3 auto_launcher_novaseqx.py -d /seq1/ --concat

# Nouveau code (tester en parallèle)
cd autolauncher
python3 main.py -d /seq1/ --concat

# Comparer les logs et résultats
diff ../autolauncher.log autolauncher.log
```

### 4. Adapter la configuration

Si votre fichier de config a un format différent, adapter `config.py` :

```python
# Dans config.py, méthode _load_config()
def _load_config(self):
    # Adapter le parsing selon votre format
    with open(self.config_file, 'r') as f:
        # Votre logique de parsing
```

### 5. Migration progressive

**Semaine 1** : Tester concat et organize
```bash
# Utiliser nouveau code pour ces étapes
crontab -e
# Modifier : python3 autolauncher/main.py -d /seq1/ --concat
```

**Semaine 2** : Ajouter infofile et analysis
**Semaine 3** : Basculer check
**Semaine 4** : Désactiver ancien code

## Vérification post-migration

### Checklist

- [ ] Les FASTQ sont concaténés correctement
- [ ] Les dossiers d'échantillons sont créés
- [ ] LabKey est interrogé avec succès
- [ ] Les analyses se lancent
- [ ] Les emails sont envoyés
- [ ] Le registre d'événements fonctionne
- [ ] Pas de fichiers de verrou bloqués

### Tests de régression

```bash
# Comparer les sorties
cd tests
bash test_concat.sh     # Compare ancien vs nouveau
bash test_organize.sh
bash test_analysis.sh

# Vérifier les événements
python3 compare_events.py ../old_events ../new_events
```

### Monitoring des performances

```bash
# Temps d'exécution
time python3 autolauncher/main.py -d /seq1/ --concat

# Utilisation mémoire
/usr/bin/time -v python3 autolauncher/main.py -d /seq1/ --concat
```

## Rollback en cas de problème

```bash
# Restaurer l'ancien code
cp auto_launcher_novaseqx.py.backup auto_launcher_novaseqx.py

# Restaurer les crontabs
crontab -e
# Remettre les anciennes lignes

# Vérifier que tout fonctionne
python3 auto_launcher_novaseqx.py -d /seq1/ --concat
```

## Points d'attention

### Chemins des fichiers

L'ancien code utilisait parfois des chemins relatifs. Le nouveau code utilise `os.path.join()` systématiquement.

**Vérifier** : Les chemins de sortie correspondent bien aux attendus.

### Format des logs

Le format des logs a changé pour être plus structuré.

**Vérifier** : Les outils qui parsent les logs doivent être adaptés.

### Comportement des événements

La logique est identique, mais l'implémentation est plus robuste.

**Vérifier** : Le fichier `autolauncher.events` se comporte comme avant.

### Exécution des subprocess

Les arguments et variables d'environnement sont gérés différemment.

**Vérifier** : Les scripts appelés reçoivent bien tous les paramètres.

## Support

En cas de problème pendant la migration :

1. Consulter les logs des deux versions
2. Comparer les fichiers produits
3. Vérifier le registre d'événements
4. Tester avec un petit échantillon d'abord
5. Contacter l'équipe si blocage

## Bénéfices attendus

Après migration complète :

- **Maintenabilité** : code plus clair
- **Débogage** : modules isolés
- **Extensibilité** : ajout facile de features
- **Tests** : code testable
- **Documentation** : inline + README (non à jour)

## Prochaines étapes

Après migration réussie, envisager :

1. Ajout de tests unitaires (quelques-uns réalisés dans tests/)
2. Monitoring avec métriques (à implémenter dans quark)
3. Dashboard web pour visualiser l'état (à implémenter dans quark)
4. API REST pour contrôle à distance
5. Intégration avec Dashboard React (à implémenter dans quark)