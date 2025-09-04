
- creation d'un fichier pour chaque sample qui log chaque action sur cet échantillon. 
		Pour chaque action : 
		- date début
		- date fin 
		- étape 
		- code sortie 
		- log correspondant 
		- machine execution 

 - Communication avec Labkey 
	 - recup info échantillon
	 - recup info process

- Communication avec Slurm 
	- récupérer les infos de quota
	- lancer des jobs
	- monitorer des jobs 

- Parser les jsons pour avoir les infos du workflow 
	- modifier json pour avoir la liste des paramètres du script à lancer. 

- Générer une interface html de suivi de l'analyse pour chaque étape 
	- avec colorisation des étapes terminées, en cours, echouées, etc
	- avec modelisation sous forme de graphe des pipelines


- Optimiser les paramètres de lancement d'un job selon dispo ressources 
	- nb coeurs
	- nb GPUs
	- nb sample à lancer, etc.

- Capacité de mailing
	- fin de run
	- echec redondant
	- archivage
	- lancement, etc. 

Ajouts :
- Réfléchir à un systeme de connexion générique, pas seulement le compte ya0902du 
	- plusieurs session de quark 
	- logguer qui lance les pipelines pour les changements d'astreinte; 
- Lancer par groupe des jobs : selon groupe de temps, ou selon partie de l'analyse. 
- Regrouper les jobs : ex 48 c nompi vers 1 slots mpi2 de 48c (moins encombré)
- Entrainement IA pour calcul des prio (futur)
- 
