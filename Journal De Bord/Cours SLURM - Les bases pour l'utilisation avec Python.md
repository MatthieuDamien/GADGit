## Introduction à SLURM

SLURM (**S**imple **L**inux **U**tility for **R**esource **M**anagement) est un gestionnaire de tâches et ordonnanceur de ressources open-source largement utilisé dans les clusters de calcul haute performance (HPC). Il permet de gérer l'allocation des ressources, la planification des tâches et le monitoring des jobs sur un cluster.

## Architecture de SLURM

SLURM fonctionne selon une architecture maître-esclave :

- **slurmctld** : Le démon contrôleur central qui gère l'état du cluster
- **slurmd** : Le démon qui s'exécute sur chaque nœud de calcul
- **slurmdbd** : La base de données pour la comptabilité (optionnel)

## Concepts fondamentaux

### Nœuds (Nodes)

Les machines physiques du cluster. Chaque nœud a des caractéristiques :

- Nombre de CPUs
- Quantité de mémoire
- État (idle, allocated, down, etc.)
intéressant qu'on sache l'état, moi ce que je dois faire c'est regarder si un etat est idle / allocated / down, la somme de tous pour savoir combien est au total, les idles pour lancer les jobs sur les noeuds
### Partitions

Groupes logiques de nœuds avec des politiques communes :

- Limites de temps d'exécution
- Priorités différentes
- Restrictions d'accès

### Jobs

Demandes d'allocation de ressources pour exécuter des tâches. Un job peut contenir :

- Une ou plusieurs tâches
- Des spécifications de ressources
- Des scripts à exécuter

## Commandes SLURM essentielles

### Soumission de jobs

**`sbatch`** : Soumet un script batch
Je pense que nous ce qui est souvent utilisé c'est `gs_solo_nbs.sh`

```bash
sbatch mon_script.sh
```

**`srun`** : Lance une commande directement

```bash
srun -n 4 python mon_programme.py
```

**`salloc`** : Alloue des ressources de manière interactive

```bash
salloc -n 4 -t 1:00:00
```

### Gestion et monitoring

**`squeue`** : Affiche l'état des jobs

```bash
squeue -u username  # Vos jobs
squeue -p partition_name  # Jobs d'une partition
```

**`scancel`** : Annule un job

```bash
scancel job_id
scancel -u username  # Tous vos jobs
```

**`sinfo`** : Informations sur les nœuds et partitions

```bash
sinfo  # Vue générale
sinfo -N  # Par nœud
```

**`sacct`** : Historique des jobs

```bash
sacct -j job_id
sacct -u username --starttime=2024-01-01
```

## Scripts SLURM

Un script SLURM typique commence par des directives `#SBATCH` :

```bash
#!/bin/bash
#SBATCH --job-name=mon_job
#SBATCH --output=output_%j.txt
#SBATCH --error=error_%j.txt
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=4
#SBATCH --mem=8GB
#SBATCH --partition=compute

# Chargement des modules nécessaires
module load python/3.9

# Activation de l'environnement virtuel
source /path/to/venv/bin/activate

# Exécution du programme
python mon_programme.py
```

### Principales options SBATCH

- `--job-name` : Nom du job
- `--time` : Temps maximum d'exécution (format HH:MM:SS)
- `--nodes` : Nombre de nœuds
- `--ntasks` : Nombre total de tâches
- `--ntasks-per-node` : Tâches par nœud
- `--cpus-per-task` : CPUs par tâche
- `--mem` : Mémoire par nœud
- `--mem-per-cpu` : Mémoire par CPU
- `--partition` : Partition à utiliser
- `--output` : Fichier de sortie standard
- `--error` : Fichier d'erreur

## Variables d'environnement SLURM

SLURM définit automatiquement des variables utiles :

- `$SLURM_JOB_ID` : ID du job
- `$SLURM_JOB_NAME` : Nom du job
- `$SLURM_NTASKS` : Nombre de tâches
- `$SLURM_CPUS_PER_TASK` : CPUs par tâche
- `$SLURM_JOB_NODELIST` : Liste des nœuds alloués

## Arrays de jobs

Pour lancer de nombreux jobs similaires :

```bash
#SBATCH --array=1-100
#SBATCH --array=1-100:2  # Pas de 2
#SBATCH --array=1,3,5,7  # Valeurs spécifiques

python analyse.py $SLURM_ARRAY_TASK_ID
```

## Utilisation avec Python et pyslurmutils

`pyslurmutils` permet d'interagir avec SLURM depuis Python. Voici les concepts importants :

### Installation

```bash
pip install pyslurmutils
```

### Exemples d'utilisation

**Soumettre un job depuis Python :**

```python
from pyslurmutils import submit_job

job_script = """#!/bin/bash
#SBATCH --job-name=python_job
#SBATCH --time=01:00:00
#SBATCH --ntasks=1

python mon_script.py
"""

job_id = submit_job(job_script)
print(f"Job soumis avec l'ID : {job_id}")
```

**Monitoring des jobs :**

```python
from pyslurmutils import get_job_status, wait_for_job

status = get_job_status(job_id)
print(f"Statut du job : {status}")

# Attendre la fin du job
wait_for_job(job_id)
```

## Bonnes pratiques

### Estimation des ressources

- Commencez par des tests sur de petits échantillons
- Utilisez `seff job_id` pour analyser l'efficacité des ressources
- Ajustez progressivement vos demandes

### Gestion des fichiers

- Utilisez des chemins absolus dans vos scripts
- Organisez vos données d'entrée et de sortie
- Attention aux quotas de stockage

### Optimisation

- Parallélisez vos codes quand c'est possible
- Utilisez les arrays pour les tâches répétitives
- Profitez des nœuds avec GPU si disponibles

### Debugging

- Vérifiez toujours les fichiers de sortie et d'erreur
- Testez vos scripts localement avant soumission
- Utilisez `srun` pour des tests interactifs

## Workflow typique avec Python

```python
import os
from pyslurmutils import submit_job, wait_for_job

# 1. Préparation des données
def prepare_data():
    # Votre code de préparation
    pass

# 2. Génération du script SLURM
def create_slurm_script(input_file, output_file):
    script = f"""#!/bin/bash
#SBATCH --job-name=analyse_{input_file}
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --mem=4GB

module load python/3.9
source /path/to/venv/bin/activate

python analyse.py {input_file} {output_file}
"""
    return script

# 3. Soumission et monitoring
def run_analysis(input_files):
    job_ids = []
    
    for input_file in input_files:
        output_file = f"result_{input_file}"
        script = create_slurm_script(input_file, output_file)
        job_id = submit_job(script)
        job_ids.append(job_id)
    
    # Attendre tous les jobs
    for job_id in job_ids:
        wait_for_job(job_id)
        print(f"Job {job_id} terminé")

# 4. Post-traitement
def collect_results():
    # Collecter et analyser les résultats
    pass
```

## Dépannage courant

**Job en attente (PENDING) :**

- Vérifiez la disponibilité des ressources avec `sinfo`
- Réduisez vos demandes de ressources
- Vérifiez les limites de votre partition

**Job échoué (FAILED) :**

- Consultez les fichiers d'erreur
- Vérifiez les chemins et permissions
- Testez avec `srun` en mode interactif

**Performance médiocre :**

- Analysez avec `seff job_id`
- Vérifiez l'utilisation CPU et mémoire
- Optimisez votre parallélisation

Ce cours vous donne les bases nécessaires pour utiliser SLURM efficacement avec Python. La maîtrise vient avec la pratique, alors n'hésitez pas à expérimenter avec des petits jobs au début !