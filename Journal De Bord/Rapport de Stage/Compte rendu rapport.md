
### Développement (30-40 pages)

**1. Contexte et problématique (5-6 pages)**

```markdown
- [ ] Présentation du service GAD (génétique médicale)
- [ ] Contexte actuel : lancement manuel des pipelines
- [ ] Volumétrie : nombre d'analyses/mois, temps par analyse
- [ ] Problématiques identifiées (délais, erreurs humaines)
- [ ] Enjeux : diagnostic rapide, scalabilité
```

**2. Objectifs et cahier des charges (3-4 pages)**

```markdown
- [ ] Objectifs du stage (orchestration automatique)
- [ ] Fonctionnalités attendues (monitoring, soumission, logs)
- [ ] Contraintes techniques (pas de daemon sur cluster)
- [ ] Contraintes temporelles (6 mois)
```

**3. Architecture et choix techniques (8-10 pages)**

```markdown
- [ ] Diagramme d'architecture globale (microservices)
- [ ] Justification choix MongoDB (vs SQL)
- [ ] Justification Node.js + WebSocket (temps réel)
- [ ] Justification React (interface moderne)
- [ ] Justification Singularity (conteneurisation)
- [ ] Comparaison avec solutions existantes (Airflow, Nextflow)
```

**4. Implémentation (12-15 pages)**

```markdown
- [ ] Backend Python : monitoring SLURM
  - [ ] Connexion SSH, parsing sinfo/squeue/sacct
  - [ ] Collections MongoDB (schémas)
  - [ ] Extraits de code commentés
- [ ] Système de file d'attente (job_queue, pipeline_steps)
- [ ] Soumission optimisée (ressources, priorités)
- [ ] Push system (wrapper dans scripts sbatch)
- [ ] Frontend React
  - [ ] Captures d'écran dashboard
  - [ ] Architecture composants
- [ ] Autolauncher
  - [ ] Pipeline steps (concat, organize, analysis)
  - [ ] Intégration LabKey
```

**5. Résultats et validation (4-5 pages)**

```markdown
- [ ] Tests réalisés (unitaires, intégration, charge)
- [ ] Benchmarks : temps de réponse, latence monitoring
- [ ] Comparaison avant/après (temps gagné)
- [ ] Captures d'écran du système en production
- [ ] Limitations identifiées
```

**6. Impacts écologiques (1-2 pages) - OBLIGATOIRE**

```markdown
- [ ] Analyse cycle de vie (serveurs, cluster)
- [ ] Optimisation ressources (éviter jobs inutiles)
- [ ] Économie énergétique (meilleure utilisation GPUs)
- [ ] Perspectives éco-conception
```

**7. Gestion de projet (3-4 pages)**

```markdown
- [ ] Méthodologie (Agile/Scrum ? Sprints ?)
- [ ] Planning initial vs réel (diagramme Gantt)
- [ ] Difficultés rencontrées (MongoDB Change Streams, SSH...)
- [ ] Solutions apportées
- [ ] Compétences acquises
```

**8. Pérennisation et perspectives (2-3 pages)**

```markdown
- [ ] Documentation livrée (README, API docs)
- [ ] Formation de l'équipe
- [ ] Évolutions futures (authentification, alerting, multi-cluster)
- [ ] Maintenabilité du code
```

---

## ⚠️ POINTS CRITIQUES ESEO

### Abstract : STRUCTURE FIXE (ne pas improviser)

```markdown
1. Starting point : "Les pipelines bioinformatiques du GAD sont lancés manuellement..."
2. Key question : "Comment automatiser et optimiser l'orchestration..."
3. Objectives : "Développer un système capable de..."
4. Approach : "Architecture microservices avec Python/Node.js/React..."
5. Results : "Système opérationnel surveillant X jobs, réduisant le temps de Y%..."
6. Conclusions : "Déploiement en production prévu, perspectives multi-cluster..."
```

### Impacts écologiques : NE PAS OUBLIER

C'est **obligatoire** et souvent oublié par les étudiants. Préparez cette section dès maintenant :

- Consommation énergétique cluster (GPUs H100)
- Optimisation utilisation ressources (éviter idle)
- Comparaison avec solution manuelle
- Perspectives (monitoring conso, extinction nœuds inutilisés)

### Déclaration IA générative

Vous devez **explicitement déclarer** l'utilisation de Claude Code :

```
"Durant la rédaction de ce rapport, j'ai utilisé l'IA générative Claude Code 
(Anthropic) afin de m'assister dans l'analyse d'architecture, la génération 
d'exemples de code, et la relecture de certaines sections techniques. Après 
avoir utilisé cet outil, j'ai relu et édité le contenu produit et j'assume 
toute responsabilité quant au contenu livré."
```

