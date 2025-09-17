import re

def get_sacct(ssh):
    list_jobs_sacct = []
    
    # Utiliser le format original sans délimiteur
    stdin, stdout, stderr = ssh.exec_command("sacct -a --format JobID,JobName%50,Partition,AllocCPUS,State,ExitCode,Elapsed,NNodes,NTasks,NodeList")
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
            
            # Si moins de 10 colonnes
            if len(parts) < 10:
                # Compléter avec des valeurs vides
                parts.extend([''] * (10 - len(parts)))
            elif len(parts) > 10:
                # Si plus de 10, prendre les 9 premiers et joindre le reste pour NodeList
                nodelist_parts = parts[9:]  # Tout ce qui reste va dans NodeList
                parts = parts[:9] + [' '.join(nodelist_parts)]
            
            # S'assurer qu'on a  10 éléments
            parts = parts[:10]
            
            try:
                JOBID, JOBNAME, PARTITION, ALLOCCPUS, STATE, EXITCODE, ELAPSED, NNODES, NTASKS, NODELIST = parts
                
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
                    "NTASKS":    NTASKS.strip() if NTASKS and NTASKS.strip() else None,
                    "NODELIST":  NODELIST.strip() if NODELIST and NODELIST.strip() else None
                }
                
                list_jobs_sacct.append(job_data)
                
            except ValueError as ve:
                print(f"Erreur de décomposition pour la ligne: '{line}'")
                print(f"Parties: {parts}")
                print(f"Erreur: {ve}")
                continue
            
        return list_jobs_sacct
        
    except Exception as e:
        print(f"Erreur lors de l'analyse de la sortie (sacct) : {e}")
        import traceback
        traceback.print_exc()
        return "Error"