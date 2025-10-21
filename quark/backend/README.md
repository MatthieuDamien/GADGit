# **API Slurm - Documentation Technique**

## **1. Contexte**

Cette API permet de surveiller et gérer les jobs Slurm sur le cluster **MesoBFC** via une interface React. Elle utilise :

- **Flask** pour l’API REACT.
- **Paramiko** pour les connexions SSH sécurisées.
- **Slurm** (`sinfo`, `squeue`, `sacct`) pour récupérer les données.

---

## **2. Architecture**

React (port 3000) → API Flask (port 5000) → SSH (Paramiko) → Cluster Slurm

---

## **3. Dépendances**

| Dépendance  | Rôle                                  |
|-------------|---------------------------------------|
| paramiko    | Connexion SSH aux nœuds du cluster.   |
| flask       | Création de l’API REACT.              |
| flask-cors  | Autorise les requêtes depuis React.   |
| re          | Parsing des sorties Slurm.            |

---

## **4. Scripts**

### API

### Database

### Slurm

#### Tests initiaux

- ``APIReact.py``
    Fait le lien entre le port de l'app web (:3000) et le port Python (:5000) via méthodes HTML pour envoyer les données en format json
- ``slurmAccess.py``
    Permet de se connecter au cluster MesoBFC
- ``slurmInfo.py``
    Execute la commande Slurm ``sinfo``
    Renvoie la liste des ressources utilisées actuellement (nompi, mpi1, mpi2, GPU)
- ``slurmQueue.py``
    Execute la commande Slurm ``squeue``
    Renvoi les listes des jobs :
    - En cours (`Running`)
    - Dépendants (``Dependency``)
    - en Attente (``Waiting``, ``MaxCpuPerAccount``, ``cn2-X (ou cn2-[X-Y])``, ``Resources``)
    - Erreur (``DependencyNeverSatisfied``)
- ``slurmSacct.py``
    Execute la commande Slurm ``sacct``
    Renvoi les listes des jobs :
    - En cours (``Running``)
    - Terminées (``Completed``)
    - Echouées (``Failed``)

#### Avancé

- `collector.py`
- `optimizer.py`

---

## **4. Points à vérifier**

- **Sécurité** : Revoir le mot de passe SSH car il est en clair dans le code. Voir pour des variables d’environnement ou un fichier `.env`.
- **Gestion des erreurs** : Que faire si `ssh.connect()` échoue ? Ajouter -> mécanisme de reconnexion et pop-up d'alerte  en haut à droite dans React.
- **Performances** : Le cache est mis à jour toutes les 5 secondes. Est-ce nécessaire ? Peut-on utiliser un :followup, un webhook ou un événement Slurm

> [!question] Comment configurer un webhook ou un événement Slurm pour déclencher des mises à jour automatiques ?
