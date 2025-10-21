
http://gitlab.gad-bioinfo.org/gad/gadpipeline/-/blob/master/common/fastq/dispatch_sample_and_mv.py
& autres fichiers pythons

Library custom : 
Dispach sample
http://gitlab.gad-bioinfo.org/gad/gadpipeline/-/blob/master/common/HPCTools.py


A ajouter :
- SQL
	- [x] Create a table to get sinfo, sacct, squeue
	- [ ] Update plutot que de créer un nouveau
	- Create a table for the optimised tasks (best nodes_hour or core_hour)
- Frontend
	- [x] Migration vers les couleurs de RadixUI
	- [x] Regroup under the same analysis (dependant of the SQL)
- Backend
	- Créer un serveur WSGI Django
	- Créer une app.py qui se transforme en .exe pour le serveur WSGI.
	- Arrêter le refresh toute les 5s (dépendant du pipeline)
	- Faire un wrapper qui `POST` ses infos + Slurm au SQL.
- Autolauncher
	- [x] Faire un dossier de test pour le `auto_launcher_novaseqx.py` 
	- Respecter ce dossier de tests pour faire le mien
- Singularity
	- Ajouter les id de connexions au cluster lors du démarrage (pas utile dans le futur mais à court terme, pratique si pas de compte Labkey et en local)