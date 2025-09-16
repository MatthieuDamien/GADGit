import paramiko
ssh = paramiko.SSHClient()

def get_sinfo():
    list_info = []
    stdin, stdout, stderr = ssh.exec_command("sinfo -a --format=\"%20P %10a %5D %15F %10T %6c %10m %20f %15l %20b %N\"")
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    try:
        for line in output.splitlines()[1:]:                         # Ignorer l'en-tête
            PARTITION, AVAIL, NODES, NODES_AIOT, STATE, CPUS, MEMORY, AVAIL_FEATURES, TIMELIMIT, ACTIVE_FEATURES, NODELIST = line.split()
            list_info.append({
                "PARTITION": PARTITION,
                "AVAIL": AVAIL,
                "NODES": NODES,
                "NODES_AIOT": NODES_AIOT,
                "STATE": STATE,
                "CPUS": CPUS,
                "MEMORY": MEMORY,
                "AVAIL_FEATURES": AVAIL_FEATURES,
                "TIMELIMIT": TIMELIMIT,
                "ACTIVE_FEATURES": ACTIVE_FEATURES,
                "NODELIST": NODELIST
            })
        return list_info
    except Exception as e:
        print(f"Erreur lors de l'analyse de la sortie : {e}")