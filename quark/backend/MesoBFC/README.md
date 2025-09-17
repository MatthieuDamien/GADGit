Dépendances utilisées :
- paramiko (Connexion Windows)
- pexpect (Connexion Linux)
- re (splitter dans slurmSacct.py)
- flask (API Python->React)
- flask-cors (API React->Python)

Scripts :
- APIReact.py
    Fait le lien entre le port de l'app web (:3000) et le port Python (:5000) via méthodes HTML pour envoyer les données en format json
- slurmAccess.py
    Permet de se connecter au cluster MesoBFC
- slurmInfo.py
    Execute la commande Slurm ``sinfo``
    Renvoie la liste des ressources utilisées actuellement (nompi, mpi1, mpi2, GPU)
- slurmQueue.py
    Execute la commande Slurm ``squeue``
    Renvoi les listes des jobs :
    - Dépendants (``Dependency``)
    - en Attente (``Waiting``, ``LimitCPUperAccount``, ``cn2-X (ou cn2-[X-Y])``)
- slurmSacct.py
    Execute la commande Slurm ``sacctq``
    Renvoi les listes des jobs :
    - En cours (``Running``)
    - Terminées (``Completed``)
    - Echouées (``Failed``)