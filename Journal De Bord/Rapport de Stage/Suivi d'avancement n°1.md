# Contexte
Ce paragraphe doit permettre de comprendre la thématique générale de votre stage et poser les éléments explicatifs permettant la compréhension des champs suivants : problématique spécifique, bits principaux.

-- 
L’objectif de ce stage est de développer un outil en Python capable d’orchestrer automatiquement le lancement de pipelines bioinformatiques (par exemple : alignement, appel de variants, annotation) en fonction des ressources disponibles sur un cluster de calcul (SLURM ou autre). L’orchestrateur devra :  
- Avoir une interface web
- Interroger régulièrement l’état du cluster (files d’attente, nœuds disponibles, mémoire/CPU/GPU)  
- Planifier et soumettre des tâches en tenant compte des contraintes de chaque pipeline (ressources, dépendances, priorité)  
- Suivre l’exécution des jobs et relancer si besoin en cas d’erreur  
- Générer des logs et un reporting synthétique

---
# Problématique spécifique
Ce paragraphe doit permettre de comprendre pourquoi le stage a été proposé. Il est important de bien expliquer (et si possible quantifier) quels couts/inconvénients/enjeux posent la problématique actuelle. Attention à bien vous positionner par rapport à la problématique que vous allez réellement traiter par votre travail personnel durant votre stage.

--
Actuellement, le centre de bioinformatique gère manuellement le lancement des analyses génomiques (génome, exome, dépistage néonatal) sur son cluster HPC. Cette gestion manuelle génère plusieurs problématiques critiques : sous-utilisation des ressources disponibles (GPU et CPU inactifs), temps d'attente imprévisibles pour les analyses urgentes, et absence de traçabilité détaillée des traitements. Dans un contexte hospitalier où les délais d'analyse impactent directement les décisions cliniques, l'optimisation automatique des ressources et la priorisation intelligente des tâches deviennent essentielles pour améliorer les performances du service de génétique médicale.

---
# Equipe du projet 
Présentez les personnes avec qui vous allez collaborer durant votre stage et/ou qui vont vous aider. En premier lieu, il y a, bien sûr, à minima votre tuteur de stage. Merci de préciser les rôles et compétences/expertises de chacune de ces personnes. Pour des raisons de confidentialité, il n'est pas nécessaire de décliner leur identité. Si vous collaborez avec d'autres stagiaires, merci d'indiquer leur niveau de formation et institution scolaire.

--
Yannis Duffourd - tuteur de stage et responsable de l'équipe
	Compétences : Web (Html, JS), Python, SLURM, bash, CUDA, biologie chromosomique 
Emilie - 
	Compétences : Python, SLURM, bash, biologie chromosomique 
Valentin - 
	Compétences : Python, SLURM, bash, biologie chromosomique 
Anthony - 
	Compétences : Python, SLURM, bash, biologie chromosomique 

---
# Buts principaux
Présentez les buts de votre mission principale (un but est un accomplissement global participant généralement à la résolution de la problématique spécifique). Un but est souvent associé à un ou plusieurs livrables. Ce but doit être quantifié par un ou plusieurs objectifs mesurables permettant de définir la réussite ou non de ce but. Un but peut être décomposé en sous-buts.

--
**But principal :** Développer l'orchestrateur Quark, un système d'orchestration intelligent pour automatiser la gestion des pipelines bioinformatiques sur cluster HPC.

**Sous-buts :**

1. **Automatisation complète** : Eliminer les interventions manuelles pour le lancement des analyses (objectif : 95% des tâches lancées automatiquement)
2. **Optimisation des ressources** : Maximiser l'utilisation du cluster en allouant dynamiquement CPU/GPU/mémoire (objectif : améliorer l'utilisation de 30%)
3. **Traçabilité exhaustive** : Assurer un logging complet de chaque étape pour chaque échantillon (objectif : 100% des actions tracées)
4. **Interface utilisateur** : Fournir un dashboard web temps réel pour le suivi des analyses (objectif : interface responsive et intuitive)

--- 
# Livrables attendus 
Listez ce que vous devrez produire et remettre a votre tuteur au cours de votre stage, cela peut être un ou des programmes informatiques, des jeux de test, des documentations (dossier de spécification, de conception, de test, de benchmark d'outils), une ou des cartes électroniques, un PCB…

--
- **Application Python Quark** : Orchestrateur complet avec modules d'intégration SLURM/LabKey, système de logging par échantillon, et algorithmes d'optimisation des ressources
- **Interface web React** : Dashboard de monitoring temps réel avec visualisation des pipelines, métriques de performance et système d'alertes
- **Documentation technique** : Architecture système, guide d'installation, manuel utilisateur et procédures d'exploitation
- **Tests et validation** : Suite de tests unitaires, tests d'intégration avec environnement HPC, et validation sur cas réels d'analyses génomiques
- **Configuration et déploiement** : Scripts d'installation, configurations SLURM, templates de workflows et procédures de mise en production