On reprend [[Cahier des charges Quark]]
## Cas d'Usage
**Lancement** : Initialiser Quark, vérifier les connexions (SLURM, LabKey).
**Surveillance** : Récupérer l'état du cluster et planifier les tâches en fonction des ressources disponibles.
**Exécution** : Soumettre les tâches, relancer automatiquement en cas d'échec, et analyser les logs.
**Reporting** : Générer des rapports synthétiques pour le suivi des pipelines (ex : qualité des données `/QC`).

---
## Test
1. Run, Quark ouvre les yeux 
2. Quark se ping lui-même (vérification réseau)
	Si ça marche, étape 3
	Si ça marche pas, erreur réseau "Hors Connexion", boucler
3. Quark tente de se connecter au cluster via SLURM (-> bizarre si ça arrive)
	Si ça marche, étape 4.
	Si ça marche pas, erreur de connexion "Cluster inaccessible", étape 4? boucler?
4. Quark demande le login / mdp LabKey de l'utilisateur ? (a-t-il son accès autonome ? -> pb de sécurité mais plus facile à mettre en place)
	Si ça marche, créer un thread ? -> pas un OS donc non
5. Création d'un Hook SLURM + Webhook (à déterminer) sur le cluster pour avoir l'update qu'il y a un changement dans l'allocation de la mémoire / GPU du cluster (voir [[Exemple d'orga Quark#Hook]]), nous n'avons aucun droit sur les API SLURM utilisées ([Voir Sarus](https://sarus.readthedocs.io/en/1.6.4/config/slurm-global-sync-hook.html)) donc pas de hook mais des demandes au cluster
	s


## Hook
### Cluster -> SLURM
Un hook est un script déclenché par un événement. Ici nous voulons créer un hook SLURM qui  fera en sorte que SLURM enverra une notification à Quark lorsqu'un événement spécifique se produit (ici : un changement d'allocation de ressource, début / fin d'un job)
Configuration à faire dans `slurm.conf.`

A faire dans un script :
```bash
#!/bin/bash
# Dans le script SLURM, ajouter à la fin :
JOB_ID=$SLURM_JOB_ID
JOB_STATUS=$?
WEBHOOK_URL="https://votre-application-web.com/webhook"

# Envoi de la notification
curl -X POST -H "Content-Type: application/json" -d "{\"job_id\": \"$JOB_ID\", \"status\": \"$JOB_STATUS\"}" $WEBHOOK_URL
```
### SLURM -> QUARK
Ensuite on pourrait utiliser un hook SSH pour notifier la machine où tourne Quark qu'il a reçu une notification c'est simple et direct mais c'est un peu plus complexe qu'un Webhook qui lui est bien plus flexible et moderne car Quark peut s'exposer à une API HTTP, et donc Quark peut recevoir des requetes HTTP.
Il existe aussi des solutions bien plus robustes et scalable, les message broker (ex : RabbitMQ, Reddis) qui fait donc une file. Mais c'est aussi plus complexe à mettre en oeuvre et trop haut niveau, il faudrait un expert pour installer ça.