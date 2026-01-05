"""
Module pour interroger la commande `sacct` de SLURM et parser sa sortie.

Ce module fournit des fonctions pour récupérer l'historique des jobs,
extraire des informations pertinentes comme le `sample_id` et le `step_name`
à partir des noms de jobs, et calculer des métriques comme les `node_hours`.
"""
import re
import traceback

def parse_elapsed(elapsed_str):
    """Parse le format de temps écoulé de SLURM (ex: "01:23:45" ou "1-05:23:45")."""
    match = re.match(r'(?:(\d+)-)?(\d+):(\d+):(\d+)', elapsed_str)
    if not match:
        return 0
    days, hours, minutes, seconds = match.groups()
    days = int(days) if days else 0
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    return days * 24 + hours + minutes / 60 + seconds / 3600

def is_valid_user_format(username: str) -> bool:
    """Vérifie si le nom d'utilisateur correspond au format 'llnnnnll'."""
    # CORRIGÉ: Accepte les noms d'utilisateur de 8 caractères.
    if not username or len(username) != 8:
        return False
    return bool(re.match(r'^[a-zA-Z]+\d+[a-zA-Z]+$', username))

def extract_sample_id(job_name):
    """
    Extrait le sample_id depuis le nom du job.
    Exemple: 'fq2vcf_djen21012' -> 'djen21012'
             'align_djex5432' -> 'djex5432'
             'variant_calling_djenbsXXXX_R1' -> 'djenbsXXXX'

    Patterns supportés:
    - dijenXXXX (1+ chiffres)
    - dijexXXXX (1+ chiffres)
    - dijenbsXXXX (1+ chiffres)
    - PEDXXXX (1+ chiffres)
    """
    if not job_name:
        return None

    # Pattern pour capturer djen/djex/djenbs suivis de chiffres
    patterns = [
        r'(dijen\d+)',      # dijenXXXX (corrected from djen)
        r'(dijnbs\d+)',     # dijnbsXXXX (corrected from djenbs)
        r'(djex\d+)',       # djexXXXX
        r'(PED\d+)',        # PEDXXXX
    ]

    for pattern in patterns:
        match = re.search(pattern, job_name, re.IGNORECASE)
        if match:
            return match.group(1).lower()

    # Si aucun pattern ne match, retourner None
    return None

def extract_step_name(job_name, sample_id):
    """
    Extrait le nom de l'étape du pipeline depuis le nom du job.
    Exemple: 'fq2vcf_djen21012' avec sample_id='djen21012' -> 'fq2vcf'
    """
    if not job_name or not sample_id:
        return job_name

    # Retirer le sample_id du job_name (insensible à la casse)
    step_name = re.sub(rf"_{sample_id}", "", job_name, flags=re.IGNORECASE)
    step_name = re.sub(rf"{sample_id}", "", step_name, flags=re.IGNORECASE)

    # Nettoyer les underscores multiples ou en début/fin
    step_name = re.sub(r'_+', '_', step_name).strip('_')

    return step_name if step_name else job_name

def get_nodes_hours(job_data):
    """
    Calcul des heures-nœuds (node_hours_used) :
    Ce champ représente le coût d'utilisation des ressources du cluster pour un job Slurm,
    exprimé en "heures-nœuds".
    - 1 heure-nœud = 1 nœud utilisé pendant 1 heure.
    - Exemple : Un job utilisant 4 nœuds pendant 2 heures consomme 8 heures-nœuds.
    Utilité :
    - Suivi précis de l'utilisation des ressources par job/analyse (Plus c'est bas, mieux c'est).
    - Répartition des coûts.
    - Optimisation des pipelines (identifier les jobs gourmands en ressources).
    """
    try:
        elapsed = job_data.get("ELAPSED", "0-00:00:00.000")
        nnodes = int(job_data.get("NNODES", 0))
        hours = parse_elapsed(elapsed)
        node_hours = nnodes * hours
        return f"{node_hours:.4f}"
    except (ValueError, TypeError) as e:
        print(f"Erreur lors de la récupération des nodes hours : {e}")
        return "Error"

def get_sacct(ssh):
    """
    Récupère et parse la sortie de la commande `sacct` via une connexion SSH.

    Utilise un format parsable avec un délimiteur '|' pour éviter les problèmes
    de parsing liés aux espaces dans certains champs (ex: 'None Assigned').

    Args:
        ssh: Un client SSH paramiko connecté.

    Returns:
        Une liste de dictionnaires représentant les jobs,
        ou "Error" en cas d'échec.
    """
    list_jobs_sacct = []

    # ✅ Utilisation d'un format parsable et d'un délimiteur explicite
    command = (
        "sacct -a -X --parsable2 --delimiter='|' "
        "--format=JobID,JobName%50,Partition,AllocCPUS,State,ExitCode,"
        "Elapsed,NNodes,NodeList,User,Start,End,Submit,Timelimit,WorkDir,ReqMem,MaxRSS"
    )

    _, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    error = stderr.read().decode()

    if error:
        print(f"Erreur lors de l'exécution de la commande : {error}")
        return "Error"

    try:
        lines = output.splitlines()
        nb_colonnes = 17  # Nombre de colonnes attendues
        IGNORER_ENTETE = True

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Ignorer les entêtes
            if IGNORER_ENTETE and (line.startswith("JobID") or line.startswith("---")):
                continue

            # ✅ Split fiable avec le séparateur '|'
            parts = line.split('|')
            if len(parts) < nb_colonnes:
                print(f"Ligne sacct ignorée (format inattendu, {len(parts)} colonnes): '{line}'")
                continue

            try:
                (job_id, job_name, partition, alloc_cpus, state, exit_code,
                 elapsed, nnodes, nodelist, user, start, end, submit,
                 timelimit, workdir, req_mem, max_rss) = parts[:nb_colonnes]

                # Vérification du format utilisateur
                if not is_valid_user_format(user.strip()):
                    print(f"Utilisateur au format inattendu : '{user}' (ligne ignorée)")
                    continue

                # Extraction des champs dérivés
                sample_id = extract_sample_id(job_name.strip())
                step_name = extract_step_name(job_name.strip(), sample_id) if sample_id else None

                # Construction du dictionnaire
                job_data = {
                    "JOBID":     job_id.strip(),
                    "JOBNAME":   job_name.strip(),
                    "PARTITION": partition.strip(),
                    "ALLOCCPUS": alloc_cpus.strip(),
                    "STATE":     state.strip(),
                    "EXITCODE":  exit_code.strip(),
                    "ELAPSED":   elapsed.strip(),
                    "NNODES":    nnodes.strip(),
                    "NODELIST":  nodelist.strip() if nodelist else None,
                    "USER":      user.strip(),
                    "START":     start.strip(),
                    "END":       end.strip(),
                    "SUBMIT":    submit.strip(),
                    "TIMELIMIT": timelimit.strip(),
                    "WORKDIR":   workdir.strip(),
                    "REQMEM":    req_mem.strip(),
                    "MAXRSS":    max_rss.strip(),
                    "SAMPLE_ID": sample_id,
                    "STEP_NAME": step_name,
                }

                # Calcul des node_hours
                job_data["NODE_HOURS"] = get_nodes_hours(job_data)

                list_jobs_sacct.append(job_data)

            except ValueError as ve:
                print(f"Erreur de parsing sur la ligne : '{line}'")
                print(f"Parties : {parts}")
                print(f"Erreur : {ve}")
                continue

        return list_jobs_sacct

    except Exception as e:
        print(f"Erreur lors de l'analyse de la sortie sacct : {e}")
        traceback.print_exc()
        return "Error"
