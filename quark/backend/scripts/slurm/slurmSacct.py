import re


def parse_elapsed(elapsed_str):
    # Parse Slurm Elapsed format (e.g., "01:23:45" or "1-05:23:45")
    match = re.match(r'(?:(\d+)-)?(\d+):(\d+):(\d+)', elapsed_str)
    if not match:
        return 0
    days, hours, minutes, seconds = match.groups()
    days = int(days) if days else 0
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    return days * 24 + hours + minutes / 60 + seconds / 3600


def extract_sample_id(job_name):
    """
    Extrait le sample_id depuis le nom du job.
    Exemple: 'fq2vcf_djen21012' -> 'djen21012'
             'align_djex5432' -> 'djex5432'
             'variant_calling_djenbsXXXX' -> 'djenbsXXXX'
    
    Patterns supportés:
    - djenXXXX (4+ chiffres)
    - djexXXXX (4+ chiffres)
    - djenbsXXXX (4+ chiffres)
    """
    if not job_name:
        return None
    
    # Pattern pour capturer djen/djex/djenbs suivis de chiffres
    patterns = [
        r'(djen\d{4,})',      # djenXXXX
        r'(djex\d{4,})',      # djexXXXX
        r'(djenbs\d{4,})',    # djenbsXXXX
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
    - Répartition des coûts entre projets/équipes.
    - Optimisation des pipelines (identifier les jobs gourmands en ressources).
    """
    try:
        elapsed = job_data.get("ELAPSED", "0-00:00:00.000")
        nnodes = int(job_data.get("NNODES", 0))
        hours = parse_elapsed(elapsed)
        node_hours = nnodes * hours
        return f"{node_hours:.4f}"
    except Exception as e:
        print(f"Erreur lors de la récupération des nodes hours : {e}")
        return "Error"


def get_sacct(ssh):
    list_jobs_sacct = []
    
    # Utiliser le format original sans délimiteur
    stdin, stdout, stderr = ssh.exec_command("sacct -a -X --format JobID,JobName%50,Partition,AllocCPUS,State,ExitCode,Elapsed,NNodes,NodeList")
    nb_colonnes = 9  # Nombre de colonnes attendues dans la sortie
    output = stdout.read().decode()
    error = stderr.read().decode()
 
    if error:
        print(f"Erreur lors de l'exécution de la commande : {error}")
        return "Error"

    try:
        lines = output.splitlines()
        
        # Ignorer les 2 premières lignes (header + séparateur)
        data_lines = lines[2:] if len(lines) > 2 else []
        
        for line in data_lines:
            line = line.strip()
            if not line:  # Ignorer les lignes vides
                continue
            
            # Utiliser regex pour split sur espaces multiples
            parts = re.split(r'\s+', line)
            
            # Si moins de nb_colonnes
            if len(parts) < nb_colonnes:
                # Compléter avec des valeurs vides
                parts.extend([''] * (nb_colonnes - len(parts)))
            elif len(parts) > nb_colonnes:
                # Si plus, prendre les premiers et joindre le reste pour NodeList
                nodelist_parts = parts[nb_colonnes-1:]  # Tout ce qui reste va dans NodeList
                parts = parts[:nb_colonnes-1] + [' '.join(nodelist_parts)]
            
            # S'assurer qu'on a nb_colonnes éléments
            parts = parts[:nb_colonnes]
            
            try:
                JOBID, JOBNAME, PARTITION, ALLOCCPUS, STATE, EXITCODE, ELAPSED, NNODES, NODELIST = parts
                
                # Extraire le sample_id et le step_name
                sample_id = extract_sample_id(JOBNAME.strip())
                step_name = extract_step_name(JOBNAME.strip(), sample_id) if sample_id else None
                
                # Nettoyer les valeurs (enlever les espaces)
                job_data = {
                    "JOBID":     JOBID.strip(),
                    "JOBNAME":   JOBNAME.strip(),
                    "PARTITION": PARTITION.strip(),
                    "ALLOCCPUS": ALLOCCPUS.strip(),
                    "STATE":     STATE.strip(),
                    "EXITCODE":  EXITCODE.strip(),
                    "ELAPSED":   ELAPSED.strip(),
                    "NNODES":    NNODES.strip(),
                    "NODELIST":  NODELIST.strip() if NODELIST and NODELIST.strip() else None,
                    
                    # Nouveaux champs
                    "SAMPLE_ID": sample_id,
                    "STEP_NAME": step_name
                }
                
                list_jobs_sacct.append(job_data)
                
            except ValueError as ve:
                print(f"Erreur de décomposition pour la ligne: '{line}'")
                print(f"Parties: {parts}")
                print(f"Erreur: {ve}")
                continue
            
            # Calcul des node_hours
            job_data["NODE_HOURS"] = get_nodes_hours(job_data)
            
        return list_jobs_sacct
        
    except Exception as e:
        print(f"Erreur lors de l'analyse de la sortie (sacct) : {e}")
        import traceback
        traceback.print_exc()
        return "Error"