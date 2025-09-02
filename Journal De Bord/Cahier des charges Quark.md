- Interroger régulièrement l’état du cluster (files d’attente, nœuds disponibles, mémoire/CPU/GPU)  
- Planifier et soumettre des tâches en tenant compte des contraintes de chaque pipeline (ressources, dépendances, priorité)  
- Suivre l’exécution des jobs et relancer si besoin en cas d’erreur
- Générer des logs et un reporting synthétique

L'orchestrateur Quark doit pourvoir tourner dans son conteneur [Singularity](https://docs.sylabs.io/guides/3.5/user-guide/index.html#). Quark a un back-end [Python](https://www.python.org/) et avec un interface en front-end [React](https://fr.react.dev/). Avec le back-end Python, Quark doit pouvoir envoyer des requêtes sur le cluster en utilisant [SLURM](https://www.schedmd.com/slurm/) . 
Quark doit pouvoir interroger régulièrement l’état du cluster (files d’attente, nœuds disponibles, mémoire/CPU/GPU), ce qui est la base de tout. En ayant ces information, l'orchestrateur doit pouvoir planifier des jobs de manière intelligente, c'est à dire tenir compte des contraintes de chaque pipeline, leur priorité, ou encore allouer des ressources de manière logique. Si qu'une seule tache est panifié, allouer plus de GPU / mémoire que normalement. Parfois des taches ne peuvent pas être accompli du à un bug d’architecture, il est généralement dans les habitudes de l'équipe de relancer ces tâches 3-4 fois , mais cela est fastidieux pour pas grand chose. Quark doit donc être capable de relancer automatiquement une tache 'Failed'. Si cette tache ne réussi pas plusieurs fois, c'est qu'il y a un vrai problème, dans ce cas là, afficher les logs pour debug. 



Code:
	- Lancer
	- Se connecter à LabKey Translad
		Server web applicatif, bdd des patients et toutes leurs informations, les processus à appliquer etc.
	- 