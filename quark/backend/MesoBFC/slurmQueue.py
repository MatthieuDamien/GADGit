def get_squeue(ssh):
    list_jobs_queue = []
    stdin, stdout, stderr = ssh.exec_command("squeue -a --format \"%.18i %.9P %.50j %.8u %.2t %.10M %.6D %R\"")
    output = stdout.read().decode()
    error = stderr.read().decode()

    if error:
        print(f"Erreur lors de l'exécution de la commande : {error}")
        return "Error"

    try:
        for line in output.splitlines()[1:]:  # Ignorer l'en-tête
            parts = line.split(maxsplit=7)  # Limiter le split à 7 parties
            if len(parts) == 8:
                JOBID, PARTITION, JOBNAME, USER, STATE, TIME, NODES, NODELIST = parts
                list_jobs_queue.append({
                    "JOBID":     JOBID,
                    "PARTITION": PARTITION,
                    "JOBNAME":   JOBNAME,
                    "USER":      USER,
                    "STATE":     STATE,
                    "TIME":      TIME,
                    "NODES":     NODES,
                    "NODELIST":  NODELIST
                })
            else:
                print(f"Ligne mal formatée (squeue) : {line}")
        return list_jobs_queue
    except Exception as e:
        print(f"Erreur lors de l'analyse de la sortie (squeue) : {e}")
        return "Error"
