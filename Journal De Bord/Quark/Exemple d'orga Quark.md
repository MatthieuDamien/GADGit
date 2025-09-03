On reprend [[Cahier des charges Quark]]
## Cas d'Usage
**Lancement** : Initialiser Quark, vérifier les connexions (SLURM, LabKey).
**Surveillance** : Récupérer l'état du cluster et planifier les tâches en fonction des ressources disponibles.
**Exécution** : Soumettre les tâches, relancer automatiquement en cas d'échec, et analyser les logs.
**Reporting** : Générer des rapports synthétiques pour le suivi des pipelines (ex : qualité des données `/QC`).


## Questions à résoudre 
Qui stocke ?
Qui envoie ?
Comment ?
Quels sont les informations à afficher ?
	Mémoire / GPU libres ?
	Logs process ?
Quels paramètres pour lancer un processus ?
Plusieurs serveurs / clusters à interroger ?

Savoir les infos dans la file d'attente + les données à collecter avant, pendant, après un process (ex : logs)

Est-ce que vous avez des documentations sur vos outils ?

 Comment définir et ajuster dynamiquement les priorités entre les tâches  ?
	Listes de priorité ? `Liste_Prio_Urgent = []; Liste_Prio_Normale = []`

---
## Test
1. Run, Quark ouvre les yeux 
2. Quark se ping lui-même (vérification réseau)
	Si ça marche, étape 3
	Si ça marche pas, erreur réseau "Hors Connexion", boucler
3. Quark tente de se connecter au cluster via SLURM avec sa clé SSH
	Si ça marche, étape 4.
	Si ça marche pas, erreur de connexion "Cluster inaccessible", étape 4? boucler?
4. Quark demande le login / mdp LabKey de l'utilisateur ? (a-t-il son accès autonome ? -> pb de sécurité mais plus facile à mettre en place)
	Si ça marche, créer un thread ? -> pas un OS donc non
5. Création d'un Hook SLURM + Webhook (à déterminer) sur le cluster pour avoir l'update qu'il y a un changement dans l'allocation de la mémoire / GPU du cluster (voir [[Exemple d'orga Quark#Hook]])
	s


## Hook
### Cluster -> SLURM
Un hook est un script déclenché par un événement. Ici nous voulons créer un hook SLURM qui  fera en sorte que SLURM enverra une notification à Quark lorsqu'un événement spécifique se produit (ici : un changement d'allocation de ressource, début / fin d'un job)
Configuration à faire dans `slurm.conf.`
### SLURM -> QUARK
Ensuite on pourrait utiliser un hook SSH pour notifier la machine où tourne Quark qu'il a reçu une notification c'est simple et direct mais c'est un peu plus complexe qu'un Webhook qui lui est bien plus flexible et moderne car Quark peut s'exposer à une API HTTP, et donc Quark peut recevoir des requetes HTTP.
Il existe aussi des solutions bien plus robustes et scalable, les message broker (ex : RabbitMQ, Reddis) qui fait donc une file. Mais c'est aussi plus complexe à mettre en oeuvre et trop haut niveau, il faudrait un expert pour installer ça.