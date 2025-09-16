import paramiko
ssh = paramiko.SSHClient()

def get_sacct():
    list_jobs_sacct = []
    stdin, stdout, stderr = ssh.exec_command("sacct -a --format JobID,JobName%50,Partition,AllocCPUS,State,ExitCode,Elapsed,NNodes,NTasks,NodeList")
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    try:
        for line in output.splitlines()[1:]:                         # Ignorer l'en-tête
            JOBID, JOBNAME, PARTITION, ALLOCCPUS, STATE, EXITCODE, ELAPSED, NNODES, NTASKS, NODELIST = line.split()
            list_jobs_sacct.append({
                "JOBID": JOBID,
                "JOBNAME": JOBNAME,
                "PARTITION": PARTITION,
                "ALLOCCPUS": ALLOCCPUS,
                "STATE": STATE,
                "EXITCODE": EXITCODE,
                "ELAPSED": ELAPSED,
                "NNODES": NNODES,
                "NTASKS": NTASKS,
                "NODELIST": NODELIST
            })
        return list_jobs_sacct
    except Exception as e:
        print(f"Erreur lors de l'analyse de la sortie : {e}")