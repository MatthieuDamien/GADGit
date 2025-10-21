# Guide Configuration GPU - Quark

## Situation actuelle de ton cluster

### Configuration détectée
- **Format GRES** : `gpu:h100:2` ✓
- **GPU par nœud** : 2 GPU H100
- **Nœuds GPU** : 3 (cn0-18, cn0-19, cn0-20)
- **Total GPU** : 6 GPU H100

---

## Solution : Configuration corrigée

### Dans `collector_corrected.py` et `optimizer_corrected.py`

```python
GPU_CONFIG = {
    'partitions': {
        'gpu': 2,      # 2 GPU H100 par nœud 
        'nompi': 0,
        'mpi1': 0,
        'mpi2': 0,
        'transfer': 0,
    },
    'node_patterns': {
        r'cn0-1[8-9]': 2,   # cn0-18, cn0-19 
        r'cn0-20': 2,       # cn0-20 
    },
    'features': {
        'gpu': 2,
    }
}
```

### Amélioration du parsing GRES

Le regex a été amélioré pour gérer le format `gpu:h100:2` :

```python
# Avant (ne fonctionnait pas avec gpu:h100:2)
match = re.search(r'gpu[^:]*:(\d+)', gres)

# Après (fonctionne avec tous les formats)
match = re.search(r'gpu:[\w]*:?(\d+)', gres)
```

**Formats supportés :**
- `gpu:h100:2` → 2 GPU ✓
- `gpu:2` → 2 GPU ✓
- `gpu:tesla:4` → 4 GPU ✓
- `gpu:a100:8` → 8 GPU ✓

---

## Vérification

### 1. Vérifier le nombre réel de GPU par nœud

Lance sur le cluster :

```bash
# Méthode 1 : scontrol
scontrol show node cn0-18 | grep Gres

# Méthode 2 : nvidia-smi (si accessible)
ssh cn0-18 nvidia-smi -L

# Méthode 3 : slurm.conf
grep "NodeName=cn0-18" /etc/slurm/slurm.conf
```

**Résultat attendu :** 2 GPU H100

### 2. Après déploiement, vérifier les métriques

```python
from database.mongodb_client import MongoDBClient

db = MongoDBClient()
snapshot = db.cluster_snapshots.find_one(sort=[('timestamp', -1)])
metrics = snapshot['metrics']

print(f"Total GPUs: {metrics['total_gpus']}")       # Attendu: 6 (3 nœuds × 2 GPU)
print(f"GPUs idle: {metrics['gpus_idle']}")         # Attendu: 6 (si tous idle)
print(f"GPUs allocated: {metrics['gpus_allocated']}")  # Attendu: 0 (si rien ne tourne)
```

**Résultat attendu :**
```
Total GPUs: 6
GPUs idle: 6
GPUs allocated: 0
```

---

## Exemples d'utilisation

### Job nécessitant 1 GPU H100

```python
from database.models import create_pipeline_step_document

step = create_pipeline_step_document(
    analysis_id="analysis_123",
    step_name="variant_calling",
    step_category="gpu_intensive"
)

step['resources'] = {
    'partition': 'gpu',
    'nodes': 1,
    'cpus': 16,
    'gpus': 1,  # Demander 1 GPU H100
    'memory_gb': 64,
    'time_limit_hours': 12
}

db.pipeline_steps.insert_one(step)
```

### Job nécessitant 2 GPU H100 (tout le nœud)

```python
step['resources']['gpus'] = 2  # Utiliser les 2 GPU d'un nœud
step['resources']['cpus'] = 48  # Utiliser tous les CPU du nœud
```

---

## Différences entre configurations

### Ancienne configuration (INCORRECTE)

```python
GPU_CONFIG = {
    'partitions': {'gpu': 4},  # ❌ Incorrect
}
```

**Résultat :**
- 3 nœuds × 4 GPU = **12 GPU détectés** (incorrect)
- Ou seulement **1 GPU détecté** si le parsing GRES échouait

### Nouvelle configuration (CORRECTE)

```python
GPU_CONFIG = {
    'partitions': {'gpu': 2},  # ✓ Correct
}
```

**Résultat :**
- 3 nœuds × 2 GPU = **6 GPU détectés** (correct)

---

## Ajouter de nouveaux nœuds GPU

### Exemple : Ajout de cn0-21 avec 4 GPU A100

```python
GPU_CONFIG = {
    'partitions': {
        'gpu': 2,  # Par défaut 2 GPU pour la partition gpu
    },
    'node_patterns': {
        r'cn0-1[8-9]': 2,  # cn0-18, cn0-19 : 2 GPU H100
        r'cn0-20': 2,       # cn0-20 : 2 GPU H100
        r'cn0-21': 4,       # cn0-21 : 4 GPU A100 (NOUVEAU)
    },
}
```

**Total GPU :** 3×2 + 1×4 = **10 GPU**

---

## Troubleshooting

### Problème : total_gpus = 0

**Cause :** GRES retourne `(null)` et la config n'est pas appliquée.

**Solution :**
1. Vérifie que `GPU_CONFIG` est bien défini dans `collector.py`
2. Active les logs debug :
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```
3. Regarde les logs : `"GPU trouvés via partition gpu pour cn0-18: 2"`

### Problème : total_gpus trop élevé

**Cause :** La configuration ne correspond pas au nombre réel de GPU.

**Solution :**
1. Vérifie le nombre réel de GPU : `ssh cn0-18 nvidia-smi -L | wc -l`
2. Ajuste `GPU_CONFIG['partitions']['gpu']` avec la bonne valeur

### Problème : total_gpus trop faible

**Cause :** Tous les nœuds ne sont pas comptés.

**Solution :**
1. Vérifie l'état des nœuds : `sinfo -p gpu`
2. Les nœuds `down` ou `drained` ne sont pas comptés dans `nodes_idle`
3. Vérifie que tous les nœuds GPU sont bien dans l'état `idle` ou `alloc`

---

## Tests automatisés

### Test 1 : Parsing GRES

```bash
python test_gres_parsing.py
```

**Attendu :** Tous les tests passent ✓

### Test 2 : Configuration GPU

```python
# Test rapide
node = {
    "PARTITION": "gpu",
    "NODELIST": "cn0-18",
    "STATE": "idle",
    "GRES": "gpu:h100:2"
}

from collector_corrected import SlurmCollector
collector = SlurmCollector("host", "user", "pass")
gpu_count = collector._parse_gpu_count(node)

assert gpu_count == 2, f"Attendu 2, obtenu {gpu_count}"
print("✓ Test parsing GPU réussi")
```

---

## Résumé

| Configuration | Avant | Après | Attendu |
|--------------|-------|-------|---------|
| GPU par nœud | 4     | 2     | 2 ✓     |
| Nœuds GPU    | 3     | 3     | 3 ✓     |
| **Total GPU**| 12 ou 1 | **6** | **6** ✓ |

**Action à faire :** Remplacer `collector.py` et `optimizer.py` par les versions corrigées (`collector_corrected.py` et `optimizer_corrected.py`).
