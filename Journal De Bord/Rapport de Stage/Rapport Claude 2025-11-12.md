## ARCHITECTURE RÉELLE DE DÉPLOIEMENT

Donc voici ce que je comprends maintenant :

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLUSTER SLURM                             │
│  ┌────────────────────────────────────────┐                     │
│  │  Autolauncher (Singularity)            │                     │
│  │  - Déclenché par cron/événements       │                     │
│  │  - Prépare les données (concat/organize)│                    │
│  │  - Écrit dans MongoDB (via réseau)     │────┐               │
│  └────────────────────────────────────────┘    │               │
│                                                  │               │
│  ┌────────────────────────────────────────┐    │               │
│  │  Jobs SLURM (pipelines)                │    │               │
│  │  - Lancés par sbatch                   │    │               │
│  │  - Génèrent .infos (logs)              │    │               │
│  │  - Peuvent pusher vers MongoDB         │────┤               │
│  └────────────────────────────────────────┘    │               │
└─────────────────────────────────────────────────┼───────────────┘
                                                  │
                    ┌─────────────────────────────▼─────────┐
                    │      MongoDB (Serveur équipe)         │
                    │   - Accessible par tous                │
                    │   - job_queue, pipeline_steps, etc.    │
                    └─────────────────────┬─────────────────┘
                                          │
        ┌─────────────────────────────────┼──────────────────────────┐
        │                                 │                          │
┌───────▼────────┐              ┌─────────▼─────────┐    ┌──────────▼────────┐
│  Backend       │              │  Server Node.js   │    │  Frontend React   │
│  (Python)      │              │  (WebSocket)      │    │  (sur labkey-     │
│  - Machine     │──SSH─────────│  - Machine équipe │    │   translad)       │
│    équipe      │  vers cluster│  - Port 5000      │    │  - Auth LabKey    │
│  - Fetch SLURM │              │  - Change Streams │◄───│  - Port 3000      │
│  - Soumet jobs │              └───────────────────┘    └───────────────────┘
│  - Pas daemon  │
└────────────────┘
```

**Contraintes validées :**

- ✅ Pas de daemon sur le cluster
- ✅ SSH depuis machine équipe vers cluster (polling autorisé)
- ✅ Autolauncher peut écrire dans MongoDB distant
- ✅ Jobs SLURM peuvent pusher vers MongoDB (via wrapper)

C'est une architecture **beaucoup plus sensée** maintenant.

---

## CLARIFICATION : QUESTION 4 (OPTIONS A/B/C)

Voici les 3 options pour **détecter et soumettre** de nouvelles analyses :

### **Option A : Autolauncher écrit directement dans job_queue**

```python
# Dans l'autolauncher (sur cluster) - steps/analysis.py
def _launch_analyses(self, correspondance_file, samples, input_dir):
    """Au lieu de lancer dispatch_sample, créer des jobs dans MongoDB"""
    from pymongo import MongoClient
    
    client = MongoClient(os.getenv('MONGO_URI'))  # MongoDB distant
    db = client['quark_db']
    
    for sample in samples:
        db.job_queue.insert_one({
            'sample_id': sample,
            'flowcell_dir': input_dir,
            'priority': self._calculate_priority(sample),
            'status': 'queued',
            'created_at': datetime.utcnow()
        })
    
    logging.info(f"{len(samples)} jobs ajoutés à job_queue")
```

**Avantage :** Push immédiat, pas de latence  
**Inconvénient :** Autolauncher doit gérer la connexion MongoDB

---

### **Option B : Backend scanne les flowcells**

```python
# Dans le backend (machine équipe) - job_detector.py
def scan_flowcell_directories(self, base_path: str):
    """Via SSH, scanner les flowcells sur le cluster"""
    ssh = connect_ssh(host, user, password)
    stdin, stdout, stderr = ssh.exec_command(
        f"find {base_path} -name 'sample_correspondance.info' -type f"
    )
    
    for info_file in stdout.readlines():
        # Vérifier si déjà traité
        # Lire le fichier via SSH (cat)
        # Créer jobs dans job_queue
```

**Avantage :** Autolauncher reste simple, backend contrôle tout  
**Inconvénient :** Polling nécessaire (toutes les 1-5 min)

---

### **Option C : Hybride (RECOMMANDÉE pour vous)**

```python
# 1. Autolauncher crée un flag file
def _launch_analyses(self, correspondance_file, samples, input_dir):
    flag_file = os.path.join(input_dir, ".quark_ready")
    with open(flag_file, 'w') as f:
        f.write(f"{datetime.utcnow().isoformat()}\n")
        f.write(",".join(samples))
    
    logging.info(f"Flag créé : {flag_file}")

# 2. Backend détecte les flags via SSH
def scan_ready_flags(self):
    ssh = connect_ssh(host, user, password)
    cmd = f"find {base_path} -name '.quark_ready' -type f"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    for flag_path in stdout.readlines():
        flowcell_dir = os.path.dirname(flag_path.strip())
        # Lire le contenu du flag
        # Créer jobs dans job_queue
        # Supprimer le flag (ou renommer en .quark_processing)
```

**Avantage :** Séparation des responsabilités, robuste, pas de dépendance MongoDB dans autolauncher  
**Inconvénient :** Légère latence (cycle du backend)

---

**Ma recommandation pour vous : Option C**, car :

1. Autolauncher reste simple (pas de dépendance MongoDB)
2. Backend garde le contrôle de la soumission
3. Facile à débugger (flag files visibles)
4. Robuste aux redémarrages

**Mais si vous voulez du vrai push (0 latence), prenez Option A**.

---

## SYSTÈME DE PUSH DEPUIS LE PIPELINE

Vous avez raison : le polling c'est lourd. Voici comment implémenter un **wrapper de push** dans vos scripts de pipeline.

### **Wrapper Python : update_job_status.py**

Créez ce script dans votre repo `gadpipeline` :

```python
#!/usr/bin/env python3
"""
Wrapper pour pusher les updates de jobs vers MongoDB depuis le cluster.
Usage: update_job_status.py <job_id> <status> [--metrics <json>]
"""

import sys
import os
import argparse
from datetime import datetime
from pymongo import MongoClient

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://serveur-equipe:27017/?replicaSet=rs0')

def update_job_status(job_id, status, metrics=None):
    """Push job status update to MongoDB"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client['quark_db']
        
        update_doc = {
            'status': status,
            'last_update': datetime.utcnow()
        }
        
        if metrics:
            update_doc['metrics'] = metrics
        
        if status == 'completed':
            update_doc['completed_at'] = datetime.utcnow()
        
        result = db.pipeline_steps.update_one(
            {'job_id': int(job_id)},
            {'$set': update_doc}
        )
        
        if result.matched_count > 0:
            print(f"✓ Job {job_id} updated to {status}")
            return 0
        else:
            print(f"✗ Job {job_id} not found in pipeline_steps", file=sys.stderr)
            return 1
            
    except Exception as e:
        print(f"✗ Error updating MongoDB: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('job_id', type=str)
    parser.add_argument('status', choices=['running', 'completed', 'failed'])
    parser.add_argument('--metrics', type=str, help='JSON string with metrics')
    
    args = parser.parse_args()
    
    metrics = None
    if args.metrics:
        import json
        metrics = json.loads(args.metrics)
    
    sys.exit(update_job_status(args.job_id, args.status, metrics))
```

### **Intégration dans vos scripts sbatch**

Modifiez vos scripts de pipeline existants :

```bash
#!/bin/bash
#SBATCH --job-name=alignment
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1

# Récupérer le JOBID SLURM
SLURM_JOB_ID=${SLURM_JOB_ID}

# Notifier le début
python3 /path/to/update_job_status.py $SLURM_JOB_ID running

# === VOTRE PIPELINE ICI ===
START_TIME=$(date +%s)

bwa mem -t 16 reference.fa sample_R1.fq sample_R2.fq > aligned.sam
EXIT_CODE=$?

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# === FIN PIPELINE ===

# Notifier la fin avec métriques
if [ $EXIT_CODE -eq 0 ]; then
    METRICS="{\"elapsed_seconds\": $ELAPSED, \"exit_code\": $EXIT_CODE}"
    python3 /path/to/update_job_status.py $SLURM_JOB_ID completed --metrics "$METRICS"
else
    python3 /path/to/update_job_status.py $SLURM_JOB_ID failed
fi

exit $EXIT_CODE
```

**Avantage :** Updates temps réel, pas besoin d'attendre le cycle de polling du backend.

---

## RÉCUPÉRATION DES .INFOS (LOGS SLURM)

Pour afficher les logs dans votre frontend, vous avez 2 options :

### **Option 1 : Stocker dans MongoDB**

Après chaque job, pusher le contenu du fichier .info :

```python
#!/usr/bin/env python3
"""push_job_logs.py"""
import sys
from pymongo import MongoClient

def push_logs(job_id, log_file_path):
    client = MongoClient(MONGO_URI)
    db = client['quark_db']
    
    with open(log_file_path, 'r') as f:
        log_content = f.read()
    
    db.pipeline_steps.update_one(
        {'job_id': int(job_id)},
        {'$set': {'slurm_log': log_content}}
    )

if __name__ == '__main__':
    push_logs(sys.argv[1], sys.argv[2])
```

Dans votre sbatch :

```bash
#SBATCH --output=/path/to/logs/%j.out
#SBATCH --error=/path/to/logs/%j.err

# À la fin du script
python3 push_job_logs.py $SLURM_JOB_ID /path/to/logs/${SLURM_JOB_ID}.out
```

### **Option 2 : API pour fetch à la demande**

Créer une route backend qui lit les logs via SSH :

```python
# Dans backend/scripts/api/routes.py
@app.route('/api/job/<job_id>/logs', methods=['GET'])
def get_job_logs(job_id):
    """Fetch SLURM logs via SSH"""
    ssh = connect_ssh(host, user, password)
    
    # Chercher le fichier de log
    cmd = f"find /path/to/logs -name '{job_id}.out' -o -name '{job_id}.err'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    log_file = stdout.read().decode().strip()
    
    if not log_file:
        return {'error': 'Log file not found'}, 404
    
    # Lire le contenu
    stdin, stdout, stderr = ssh.exec_command(f"cat {log_file}")
    log_content = stdout.read().decode()
    
    return {'job_id': job_id, 'log': log_content}
```

**Frontend :**

```jsx
// Dans AnalysisPage.jsx
const [jobLogs, setJobLogs] = useState(null);

const fetchJobLogs = async (jobId) => {
  const response = await axios.get(`http://localhost:5000/api/job/${jobId}/logs`);
  setJobLogs(response.data.log);
};

// Bouton dans le JobCard
<Button onClick={() => fetchJobLogs(job.JOBID)}>Voir logs</Button>
```

**Recommandation : Option 2** (fetch à la demande), car :

- Pas de surcharge MongoDB avec des gros fichiers texte
- Logs toujours à jour
- Fetch seulement quand l'utilisateur clique

---

## COLLECTION POUR LES ANALYSES COMPLÉTÉES

Pour répondre au besoin de votre maître de stage (temps d'exécution) :

### **Nouvelle collection : completed_analyses**

```python
# Structure du document
{
    'analysis_id': 'dijex_12345',
    'sample_id': 'dijex_12345',
    'status': 'completed',
    'started_at': datetime(2025, 11, 17, 10, 0, 0),
    'completed_at': datetime(2025, 11, 17, 22, 30, 0),
    'total_duration_seconds': 45000,  # 12.5 heures
    'steps': [
        {
            'step_name': 'alignment',
            'job_id': 61524,
            'duration_seconds': 28800,  # 8h
            'resources_used': {
                'cpus': 16,
                'gpus': 1,
                'memory_gb': 64,
                'node': 'cn0-18'
            },
            'exit_code': 0
        },
        {
            'step_name': 'variant_calling',
            'job_id': 61525,
            'duration_seconds': 14400,  # 4h
            'resources_used': {...},
            'exit_code': 0
        },
        # ...
    ],
    'total_resources': {
        'cpu_hours': 160,  # 16 CPUs × 10h
        'gpu_hours': 8,    # 1 GPU × 8h
        'node_hours': 12.5
    },
    'flowcell_dir': '/data/flowcells/20251115_novaseqx',
    'metadata': {
        'genome_build': 'hg38',
        'pipeline_version': '2.1.0'
    }
}
```

### **Logique d'insertion**

Dans votre backend, quand une analyse est complétée :

```python
# backend/scripts/slurm/job_separator.py
def _check_analysis_completion(self, analysis):
    """Vérifier si toutes les étapes sont complétées"""
    all_completed = all(
        job['STATE'] in ['COMPLETED', 'FINISHED'] 
        for job in analysis['jobs']
    )
    
    if all_completed:
        self._archive_completed_analysis(analysis)

def _archive_completed_analysis(self, analysis):
    """Archiver l'analyse complétée avec ses métriques"""
    # Calculer métriques totales
    total_duration = 0
    total_cpu_hours = 0
    total_gpu_hours = 0
    
    steps_data = []
    for job in analysis['jobs']:
        duration = self._calculate_duration(job['START_TIME'], job['END_TIME'])
        total_duration += duration
        
        # Calculer resource-hours
        cpus = int(job.get('NCPUS', 1))
        total_cpu_hours += (cpus * duration) / 3600
        
        # Si GPU utilisé
        if 'gpu' in job.get('PARTITION', ''):
            gpus = self._parse_gpu_count(job)
            total_gpu_hours += (gpus * duration) / 3600
        
        steps_data.append({
            'step_name': self._extract_step_name(job['NAME']),
            'job_id': job['JOBID'],
            'duration_seconds': duration,
            'resources_used': {
                'cpus': cpus,
                'gpus': gpus if 'gpu' in job.get('PARTITION', '') else 0,
                'memory_gb': self._parse_memory(job.get('ReqMem', '0')),
                'node': job.get('NODELIST', 'unknown')
            },
            'exit_code': int(job.get('EXIT_CODE', '0:0').split(':')[0])
        })
    
    # Insérer dans completed_analyses
    self.db.completed_analyses.insert_one({
        'analysis_id': analysis['analysis_id'],
        'status': 'completed',
        'started_at': min(job['START_TIME'] for job in analysis['jobs']),
        'completed_at': max(job['END_TIME'] for job in analysis['jobs']),
        'total_duration_seconds': total_duration,
        'steps': steps_data,
        'total_resources': {
            'cpu_hours': total_cpu_hours,
            'gpu_hours': total_gpu_hours,
            'node_hours': total_duration / 3600
        },
        'archived_at': datetime.utcnow()
    })
    
    logging.info(f"Analysis {analysis['analysis_id']} archived. "
                 f"Duration: {total_duration/3600:.2f}h, "
                 f"CPU-hours: {total_cpu_hours:.2f}")
```

### **Index MongoDB pour requêtes de performance**

```python
# Dans mongodb_client.py
self.completed_analyses.create_index([('analysis_id', 1)], unique=True)
self.completed_analyses.create_index([('total_duration_seconds', 1)])  # Pour tri rapide
self.completed_analyses.create_index([('completed_at', -1)])
self.completed_analyses.create_index([('total_resources.cpu_hours', 1)])
```

### **Requête pour trouver les analyses les plus rapides**

```python
# Backend API endpoint
@app.route('/api/completed_analyses/fastest', methods=['GET'])
def get_fastest_analyses():
    """Top 10 des analyses les plus rapides"""
    fastest = list(
        db.completed_analyses.find().sort('total_duration_seconds', 1).limit(10)
    )
    return jsonify(fastest)
```

---

## TODO LIST ACTUALISÉE (6 SEMAINES)

### 🔴 Semaine 47 (17-21 nov) : Corrections critiques

```markdown
**Jour 1 : Setup et corrections (Lundi 17)**
- [ ] Générer backend/requirements.txt (pip freeze > requirements.txt)
- [ ] Créer backend/.env avec MONGO_URI, SLURM_HOST, SLURM_USER, SLURM_PASSWORD
- [ ] Corriger race condition lock.py (os.O_EXCL) - CODE FOURNI CI-DESSUS
- [ ] Corriger ordre événements analysis.py (move events inside try)
- [ ] Vérifier config GPU optimizer.py (clarifier commentaires)

**Jour 2-3 : Tests existant (Mardi-Mercredi)**
- [ ] Tester autolauncher end-to-end avec vraies données
- [ ] Vérifier MongoDB Change Streams
- [ ] Valider interface web complète
- [ ] Tester connexion SSH depuis machine équipe vers cluster

**Jour 4-5 : Décision architecture (Jeudi-Vendredi)**
- [ ] Choisir Option A, B ou C pour détection jobs (voir ci-dessus)
- [ ] Implémenter la détection choisie
- [ ] Tester création de jobs dans job_queue
```

### 🟠 Semaine 48 (24-28 nov) : Pipeline Builder & Soumission

```markdown
**Jour 6-7 : PipelineBuilder**
- [ ] Créer backend/scripts/pipeline_builder.py
- [ ] Définir PIPELINE_STEPS pour workflow GAD
- [ ] Implémenter create_pipeline_for_job()
- [ ] Tester création pipeline_steps dans MongoDB

**Jour 8-9 : Soumission sbatch**
- [ ] Créer backend/config.yaml (chemins scripts, paramètres ressources)
- [ ] Corriger _build_sbatch_command() avec vrais chemins
- [ ] Tester génération commande sbatch (dry-run)
- [ ] Soumettre 1 job test sur cluster

**Jour 10 : Intégration détection → soumission**
- [ ] Connecter JobDetector → PipelineBuilder → Scheduler
- [ ] Tester cycle complet
- [ ] Valider que JOBID retourné est stocké dans pipeline_steps
```

### 🟡 Semaine 49 (1-5 déc) : Push system & Logs

```markdown
**Jour 11-12 : Wrapper de push**
- [ ] Créer update_job_status.py (CODE FOURNI CI-DESSUS)
- [ ] Intégrer dans vos scripts sbatch existants
- [ ] Tester push temps réel vers MongoDB
- [ ] Valider que frontend reçoit updates via WebSocket

**Jour 13-14 : Système de logs**
- [ ] Créer API endpoint /api/job/<job_id>/logs (fetch via SSH)
- [ ] Ajouter bouton "Voir logs" dans frontend (JobCard)
- [ ] Tester affichage logs dans interface
- [ ] Gérer cas où log file n'existe pas encore

**Jour 15 : Collection completed_analyses**
- [ ] Créer logique d'archivage dans job_separator.py
- [ ] Implémenter calcul métriques (duration, cpu_hours, gpu_hours)
- [ ] Tester archivage d'une analyse complétée
- [ ] Créer index MongoDB pour requêtes de performance
```

### 🟢 Semaine 50 (8-12 déc) : Optimisation & Monitoring

```markdown
**Amélioration optimizer**
- [ ] Implémenter algorithme de sélection plus intelligent (priorité, ressources, dépendances)
- [ ] Ajouter logique de retry pour jobs échoués
- [ ] Tester avec 10+ analyses simultanées

**Dashboard métriques**
- [ ] Créer page frontend "Statistiques"
- [ ] Afficher top 10 analyses les plus rapides
- [ ] Graphiques : CPU-hours par jour, GPU utilization
- [ ] Afficher nombre d'analyses en queue
```

### 🟢 Semaine 51 (15-19 déc) : Production readiness

```markdown
**Stabilisation**
- [ ] Tests de charge (50+ jobs)
- [ ] Gestion d'erreurs robuste (retry, timeouts)
- [ ] Logging amélioré (structured logging)
- [ ] Monitoring : alertes si queue > 20 jobs

**Déploiement**
- [ ] Script de déploiement (systemd service pour backend)
- [ ] Configuration production (MongoDB URI, chemins cluster)
- [ ] Build frontend (npm build)
- [ ] Déployer sur labkey-translad
```

### 📚 Semaine 52 (22-26 déc) : Documentation & Rapport

```markdown
**Documentation**
- [ ] README.md complet (installation, architecture, usage)
- [ ] Diagramme d'architecture (draw.io)
- [ ] Guide utilisateur (captures d'écran)
- [ ] Documentation API (endpoints, payloads)

**Rapport de stage**
- [ ] Rédaction rapport (contexte, architecture, implémentation)
- [ ] Résultats (benchmarks, métriques)
- [ ] Perspectives d'évolution
- [ ] Préparation soutenance (slides)
```

---

## ÉLÉMENTS SUPPRIMÉS DE VOTRE TODO

❌ **Retirés (hors-scope ou redondants) :**

```markdown
❌ Créer un serveur WSGI Django (inutile, Flask suffit)
❌ Créer une app.py qui se transforme en .exe (Linux, pas Windows)
❌ Ajouter qui est d'astreinte via Google Calendar (nice-to-have, pas prioritaire)
```

---

## RÉPONSES À VOS QUESTIONS

**1. "Va chercher dans les .infos du cluster"**  
→ **Compris.** Voir section "Récupération des .infos" ci-dessus. Je recommande l'API endpoint qui fetch à la demande via SSH.

 

**2. "Wrapper vers SQL"**  
→ **Compris.** Voir section "Système de push" avec `update_job_status.py`. C'est une bonne idée.

 

**3. "5000 jobs en dur"**  
→ **OK.** Si vous êtes sûrs de ne jamais atteindre cette limite, gardez-la. Mais ajoutez au moins un tri par `last_seen` décroissant dans le frontend pour afficher les plus récents en premier.

 

**4. "Optimized tasks pour meilleur temps"**  
→ **Résolu.** Voir section "Collection completed_analyses" qui stocke toutes les métriques.

 

**5. "Option A/B/C"**  
→ **Clarifiée ci-dessus.** Je recommande **Option C** (flag files) ou **Option A** (push direct MongoDB) selon vos préférences.

---

## QUESTION FINALE POUR VOUS

**Pour finaliser le plan, choisissez :**

1. **Détection de jobs** : Option A (push MongoDB), B (scan SSH), ou C (flag files) ?
2. **Logs SLURM** : Stocker dans MongoDB ou fetch via API à la demande ?
3. **Priorité** : Préférez-vous commencer par le système de soumission (semaines 47-48) ou par le push system (wrapper) ?

Ma recommandation :

- **Option C** (flag files) : Simple, robuste, pas de dépendance MongoDB dans autolauncher
- **Logs via API** : Pas de surcharge MongoDB
- **Priorité soumission d'abord** : Sans ça, le reste ne sert à rien

Qu'en pensez-vous ?