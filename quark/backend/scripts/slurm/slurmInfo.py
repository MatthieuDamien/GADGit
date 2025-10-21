def get_sinfo(ssh):
    list_info = []
    
    # %G affiche les GRES sous forme "gpu:2" ou "(null)" si pas de GPU
    stdin, stdout, stderr = ssh.exec_command(
        "sinfo -a --format=\"%20P %10a %5D %15F %10T %6c %10m %20G %20f %15l %20b %N\""
    )
    output = stdout.read().decode()
    error = stderr.read().decode()

    if error:
        print(f"Erreur : {error}")
        return "Error"

    try:
        for line in output.splitlines()[1:]:
            parts = line.split(maxsplit=11)
            if len(parts) == 12:
                PARTITION, AVAIL, NODES, NODES_AIOT, STATE, CPUS, MEMORY, GRES, AVAIL_FEATURES, TIMELIMIT, ACTIVE_FEATURES, NODELIST = parts
                list_info.append({
                    "PARTITION":       PARTITION,
                    "AVAIL":           AVAIL,
                    "NODES":           NODES,
                    "NODES_AIOT":      NODES_AIOT,
                    "STATE":           STATE,
                    "CPUS":            CPUS,
                    "MEMORY":          MEMORY,
                    "GRES":            GRES,  # Contient les GPU
                    "AVAIL_FEATURES":  AVAIL_FEATURES,
                    "TIMELIMIT":       TIMELIMIT,
                    "ACTIVE_FEATURES": ACTIVE_FEATURES,
                    "NODELIST":        NODELIST
                })
        return list_info
    except Exception as e:
        print(f"Erreur lors de l'analyse de la sortie : {e}")
        return "Error"