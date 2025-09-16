import paramiko
ssh = paramiko.SSHClient()

def get_squeue():
    list_jobs_queue = []
    stdin, stdout, stderr = ssh.exec_command("squeue -a --format \"%.18i %.9P %.50j %.8u %.2t %.10M %.6D %R\"")
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    try:
        for line in output.splitlines()[1:]:                         # Ignorer l'en-tête
            JOBID, PARTITION, JOBNAME, USER, STATE, TIME, NODES, NODELIST = line.split()
            list_jobs_queue.append({
                "JOBID": JOBID,
                "PARTITION": PARTITION,
                "JOBNAME": JOBNAME,
                "USER": USER,
                "STATE": STATE,
                "TIME": TIME,
                "NODES": NODES,
                "NODELIST": NODELIST
            })
        return list_jobs_queue
    except Exception as e:
        print(f"Erreur lors de l'analyse de la sortie : {e}")