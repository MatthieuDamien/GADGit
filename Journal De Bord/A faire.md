
http://gitlab.gad-bioinfo.org/gad/gadpipeline/-/blob/master/common/fastq/dispatch_sample_and_mv.py
& autres fichiers pythons

Library custom : 
Dispach sample
http://gitlab.gad-bioinfo.org/gad/gadpipeline/-/blob/master/common/HPCTools.py

oxford nanoport, séminaire d'ouverture : mardi 25 9h, jeudi 27 9h.

A ajouter :
- MongoDB
	- [x] Create a table to get sinfo, sacct, squeue - depreciated
	- [x] Update plutôt que de créer un nouveau pour raw_jobs, cluster_snapshots etc.
	- [ ] Create a collection for the optimised tasks (best nodes_hour or core_hour) & completed analysis
	- [x] Enregistrer le nom des jobs liés à une analyse (linked_jobs = List {61524, 61525, 61526,...})
- Frontend
	- [x] Migration vers les couleurs de RadixUI
	- [x] Regroup under the same analysis (dependant of the SQL)
	- [x] Hydratation
	- [x] Boutons clickables pour les infos supplémentaires 
	- [ ] va chercher dans les .infos du cluster.
	- [ ] Ajouter qui est d'astreinte en haut à droite dans le header en utilisant google Calendar.
- Backend
	- [ ] Créer une app.py qui se transforme en .exe pour le serveur WSGI ?
	- [x] Arrêter le refresh toute les 5s (dépendant du pipeline)
	- [ ] Faire un wrapper qui `POST` ses infos + Slurm au MongoDB.
- Server
	- [x] Ajouter raw_jobs dans le code pour activer l'autodelete ?
- Autolauncher
	- [x] Faire un dossier de test pour le `auto_launcher_novaseqx.py` 
	- [x] Respecter ce dossier de tests pour faire le mien
	- [x]  Ajouter sys.excepthook (main.py)
	- [x]  Ajouter vérification already_analyzed (organize.py)
	- [x]  Résoudre race condition lock avec fcntl
- Singularity
	- [ ] Ajouter les id de connexions au cluster lors du démarrage (pas utile dans le futur mais à court terme, pratique si pas de compte Labkey et en local)
	- [x] Faire une singu pour l'autolauncher (labkey est infonctionnel...)

Replica Set :
```bash
mongod --port 27017 --dbpath C:\Users\skycr\ProDisk\Stages\GAD\CloneGAD\gadpipeline\data\db\rs0 --replSet rs0
```

---
## SEMAINE 47 (17-21 novembre) : SPRINT TECHNIQUE #1

**Objectif : Système de base fonctionnel**

### Corrections critiques

- [x]  Générer backend/requirements.txt (pip freeze)
- [x]  Créer backend/.env avec MONGO_URI, SLURM_HOST, SLURM_USER, SLURM_PASSWORD
- [ ]  ~~Corriger race condition lock.py (utiliser os.O_EXCL pour fallback Windows)~~ -> non nécessaire car full Linux
- [x]  Corriger ordre événements analysis.py (move events inside try block)
- [x]  Vérifier configuration GPU dans optimizer.py (commentaires vs valeurs)

### Tests de l'existant

- [x]  Tester autolauncher end-to-end avec vraies données flowcell
- [ ]  Vérifier MongoDB Change Streams fonctionnent correctement
- [x]  Valider interface web complète (toutes les pages)
- [x]  Tester connexion SSH depuis machine équipe vers cluster

### Détection de jobs (Option C : flag files)

- [ ]  Implémenter système de flag files dans autolauncher
- [ ]  Créer backend/scripts/job_detector.py (scan flags via SSH)
- [ ]  Tester détection de nouveaux flowcells
- [ ]  Tester création de documents dans collection job_queue

### Rédaction (1 jour)

- [ ]  🖊️ Rédiger contexte entreprise GAD (2-3 pages)
- [ ]  🖊️ Rédiger problématique et enjeux (1-2 pages)

---

## SEMAINE 48 (24-28 novembre) : SPRINT TECHNIQUE #2

**Objectif : Soumission de jobs fonctionnelle**

### PipelineBuilder

- [ ]  Créer backend/scripts/pipeline_builder.py
- [ ]  Définir PIPELINE_STEPS pour workflow GAD (alignment, variant_calling, annotation...)
- [ ]  Implémenter create_pipeline_for_job()
- [ ]  Tester création de pipeline_steps dans MongoDB

### Soumission sbatch

- [ ]  Créer backend/config.yaml (chemins scripts, paramètres ressources)
- [ ]  Corriger _build_sbatch_command() avec vrais chemins de scripts
- [ ]  Tester génération de commande sbatch (dry-run)
- [ ]  Soumettre 1 job test réel sur le cluster
- [ ]  Valider que JOBID est récupéré et stocké dans pipeline_steps

### Wrapper de push

- [ ]  Créer update_job_status.py (wrapper push MongoDB)
- [ ]  Intégrer wrapper dans scripts sbatch existants
- [ ]  Tester push temps réel vers MongoDB
- [ ]  Valider que frontend reçoit updates via WebSocket

### Intégration complète

- [ ]  Connecter JobDetector → PipelineBuilder → Scheduler
- [ ]  Tester cycle complet : détection → queue → soumission → monitoring
- [ ]  Tests avec 3-5 jobs simultanés

### Rédaction (1 jour)

- [ ]  🖊️ Créer diagrammes d'architecture (draw.io ou mermaid)
- [ ]  🖊️ Rédiger architecture globale (4-5 pages)
- [ ]  🖊️ Justification des choix techniques (MongoDB, Node.js, React, Singularity)

---

## SEMAINE 49 (1-5 décembre) : FINITIONS TECHNIQUES + DÉBUT RÉDACTION

**Objectif : Système stable + 50% du rapport rédigé**

### Système de logs SLURM

- [ ]  Créer API endpoint /api/job/<job_id>/logs (fetch via SSH)
- [ ]  Ajouter bouton "Voir logs" dans frontend (JobCard component)
- [ ]  Tester affichage des logs dans l'interface
- [ ]  Gérer cas où log file n'existe pas encore

### Collection completed_analyses

- [ ]  Implémenter logique d'archivage dans job_separator.py
- [ ]  Calculer métriques (duration, cpu_hours, gpu_hours, node_hours)
- [ ]  Créer index MongoDB pour requêtes de performance
- [ ]  Tester archivage d'une analyse complétée
- [ ]  Créer page frontend "Statistiques" (top 10 analyses rapides)

### Tests et stabilisation

- [ ]  Tests de charge (10+ jobs simultanés)
- [ ]  Corrections des bugs trouvés
- [ ]  Gestion d'erreurs robuste (retry, timeouts)
- [ ]  Logging amélioré

### Rédaction (3 jours)

- [ ]  🖊️ Rédiger choix technologiques et comparaisons (3-4 pages)
- [ ]  🖊️ Rédiger implémentation Backend (5-6 pages avec extraits code)
- [ ]  🖊️ Rédiger implémentation Frontend (3-4 pages avec screenshots)
- [ ]  🖊️ Rédiger implémentation Autolauncher (4-5 pages)
- [ ]  🖊️ Prendre captures d'écran du système en action
- [ ]  🖊️ Préparer extraits de code commentés

---

## SEMAINE 50 (8-13 décembre) : RÉDACTION INTENSIVE

**Objectif : FINIR LE RAPPORT (deadline 14 déc 00h00)**

### Rédaction intensive (6 jours)

-  🖊️ Rédiger résultats et benchmarks (3-4 pages)
    
-  🖊️ Créer tableaux comparatifs (avant/après automatisation)
    
-  🖊️ Ajouter métriques de performance (temps queue, latence monitoring)
    
-  🖊️ Rédiger impacts écologiques (2 pages) - OBLIGATOIRE ESEO
    
    - [ ]  Consommation énergétique cluster
    - [ ]  Optimisation utilisation ressources
    - [ ]  Perspectives éco-conception
-  🖊️ Rédiger gestion de projet (3-4 pages)
    
    - [ ]  Méthodologie suivie
    - [ ]  Planning initial vs réel
    - [ ]  Difficultés rencontrées et solutions
-  🖊️ Rédiger Abstract (1 page) - STRUCTURE FIXE ESEO
    
    - [ ]  Starting point / Motivation
    - [ ]  Key question
    - [ ]  Research objectives
    - [ ]  Process / Approach
    - [ ]  Results / Outcomes
    - [ ]  Conclusions
-  🖊️ Rédiger Introduction (1 page)
    
-  🖊️ Rédiger Conclusion (2 pages)
    
-  🖊️ Rédiger Remerciements (1 page)
    

### Annexes

- [ ]  🖊️ ANNEXE A : CV avec projet professionnel
- [ ]  🖊️ ANNEXE B : Bibliographie (références MongoDB, SLURM, React, etc.)
- [ ]  🖊️ ANNEXE C : Glossaire (définitions techniques, acronymes)
- [ ]  🖊️ ANNEXE D : Table des figures et illustrations

### Finitions

- [ ]  🖊️ Générer sommaire automatique
- [ ]  🖊️ Compléter engagement non-plagiat + déclaration IA générative
- [ ]  🖊️ Vérifier numérotation des pages
- [ ]  🖊️ Vérifier mise en forme (marges, police, cohérence)

### Relecture

- [ ]  📖 Relecture complète (orthographe, syntaxe, grammaire)
- [ ]  📖 Vérifier cohérence globale du rapport
- [ ]  📖 Faire relire par tuteur de stage (RECOMMANDÉ ESEO)
- [ ]  📖 Vérifier toutes les références bibliographiques
- [ ]  ✅ Intégrer retours du tuteur
- [ ]  ✅ Dernières corrections

### Rendu (14 décembre avant minuit)

- [ ]  🚀 Export PDF final
- [ ]  🚀 Vérifier poids fichier (<20 MB)
- [ ]  🚀 Tester ouverture PDF sur autre ordinateur
- [ ]  🚀 Upload sur plateforme MYESEO
- [ ]  🚀 Vérifier confirmation de dépôt
- [ ]  🚀 Email confirmation à référent ESEO

---

## SEMAINE 51 (15-19 décembre) : POST-RAPPORT

**Objectif : Préparation soutenance + déploiement production**

### Préparation soutenance

- [ ]  Créer support PowerPoint/Keynote (15-20 slides)
- [ ]  Structurer présentation (10-15 min oral)
    - [ ]  Introduction et contexte
    - [ ]  Problématique et objectifs
    - [ ]  Architecture et choix techniques
    - [ ]  Démonstration système
    - [ ]  Résultats et perspectives
- [ ]  Préparer démonstration live (backup vidéo si problème réseau)
- [ ]  Répéter présentation (timing, fluidité)
- [ ]  Préparer réponses aux questions probables

### Déploiement production (si temps disponible)

- [ ]  Créer script de déploiement backend (systemd service)
- [ ]  Configuration production (MongoDB URI, chemins cluster)
- [ ]  Build frontend production (npm build)
- [ ]  Déployer frontend sur labkey-translad
- [ ]  Tests déploiement avec équipe GAD
- [ ]  Formation utilisateurs (collègues)

### Documentation finale

- [ ]  README.md complet (installation, usage)
- [ ]  Documentation API (endpoints, exemples requêtes)
- [ ]  Guide utilisateur avec captures d'écran
- [ ]  Guide administrateur (maintenance, troubleshooting)

---

## SEMAINE 52 (22-26 décembre) : CLÔTURE STAGE

**Objectif : Finalisation et passation**

### Passation

- [ ]  Session de formation équipe GAD (présentation outil)
- [ ]  Documenter procédures maintenance
- [ ]  Transférer accès (credentials, repos Git)
- [ ]  Lister améliorations futures recommandées

### Bilan stage

- [ ]  Remplir évaluation stage (formulaire ESEO)
- [ ]  Demander évaluation au tuteur de stage
- [ ]  Rétrospective personnelle (compétences acquises)

### Soutenance (date à confirmer)

- [ ]  Confirmer date/heure soutenance avec ESEO
- [ ]  Confirmer composition jury (président + co-jury)
- [ ]  Imprimer support présentation (backup papier)
- [ ]  Répétition finale

### Administratif

- [ ]  Signer attestation de stage
- [ ]  Récupérer documents RH
- [ ]  Remercier équipe GAD