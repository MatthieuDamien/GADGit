#!/usr/bin/env python3

### GAD PIPELINE ###
## HPCTools.py
## Version : 
## Description : Module with functions to retrieve resource informations from clusters in sge or slurm.
## Usage : <command>
## Output : <description of output>
## Requirements : Python 2.7+

## Author : anthony.auclair@u-bourgogne.fr
## Creation Date : 20250327
## Last revision date : 20250522
## Known bugs : None




import logging
from subprocess import Popen, PIPE
import subprocess
import sys

# Logging
#check if logger already exists
logger = logging.getLogger(__name__)

def get_total_resource_slurm(partition,resource):
    logger.info("Command : scontrol show partition "+partition+" | grep 'TRES' | awk -F "+resource+" '{print $2}' | awk -F ',' '{print $1}' | awk -F '=' '{print $2}'")
    total_popen = subprocess.Popen("scontrol show partition "+partition+" | grep 'TRES' | awk -F "+resource+" '{print $2}' | awk -F ',' '{print $1}' | awk -F '=' '{print $2}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    total_stderr = total_popen.communicate()[1]
    total_stdout = total_popen.communicate()[0]
    total = total_stdout.strip()
    logger.info("TOTAL - "+total)
    if total_stderr.strip() != "":
        logger.warning("TOTAL - "+total_stderr.strip())
        logger.warning("TOTAL - getting total resource failed for partition "+partition+" and resource "+resource+".")
    else:
        logger.info("TOTAL - Total for partition "+partition+" and resource "+resource+" is "+total+".")
        return total

def get_resource_quota_slurm(qos,partition,resource):
    logger.info("Command : sacctmgr list qos format=Name%20,Priority,MaxTRESPU%20 | grep "+qos+" | awk '{print $3}' | awk -F "+resource+" '{print $2}' | awk -F '=' '{print $2}'")
    quota = subprocess.Popen("sacctmgr list qos format=Name%20,Priority,MaxTRESPU%20 | grep "+qos+" | awk '{print $3}' | awk -F "+resource+" '{print $2}' | awk -F '=' '{print $2}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    quota_stderr = quota.communicate()[1]
    quota_stdout = quota.communicate()[0]
    quota = quota_stdout.strip()
    total_resource = get_total_resource_slurm(partition,resource)
    if quota == '':
        quota = total_resource
    logger.info("QUOTA - "+quota)
    if quota_stderr.strip() != "":
        logger.warning("QUOTA - "+quota_stderr.strip())
        logger.warning("QUOTA - getting resource quota failed for qos "+qos+" and resource "+resource+".")
    else:
        logger.info("QUOTA - Quota for qos "+qos+" and resource "+resource+" is "+quota+".")
        return quota

def get_nodes_per_partition_slurm(partition,resource):
    logger.info("Command : scontrol show partition "+partition+" | grep '   Nodes' | awk -F '=' '{print $2}'")
    nodes = subprocess.Popen("scontrol show partition "+partition+" | grep '   Nodes' | awk -F '=' '{print $2}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    nodes_stderr = nodes.communicate()[1]
    nodes_stdout = nodes.communicate()[0]
    nodes = nodes_stdout.strip()
    logger.info("NODES - "+nodes)
    if nodes_stderr.strip() != "":
        logger.warning("NODES - "+nodes_stderr.strip())
        logger.warning("NODES - getting nodes resource failed for partition "+partition+" and resource "+resource+".")
    else:
        logger.info("NODES - Nodes for partition "+partition+" and resource "+resource+" are "+nodes+".")
        return nodes

def get_allocated_resources_slurm(partition,resource):
    nodes = get_nodes_per_partition_slurm(partition,resource)
    logger.info("Command : scontrol show node "+nodes+" | grep '   AllocTRES' | awk -F "+resource+" '{print $2}' | awk -F '=' '{print $2}' | grep -E '[0-9]' | paste -sd+ | bc")
    allocated = subprocess.Popen("scontrol show node "+nodes+" | grep '   AllocTRES' | awk -F "+resource+" '{print $2}' | awk -F '=' '{print $2}' | grep -E '[0-9]' | paste -sd+ | bc", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    allocated_stderr = allocated.communicate()[1]
    allocated_stdout = allocated.communicate()[0]
    allocated = allocated_stdout.strip()
    if allocated == "":
        allocated = "0"
    logger.info("ALLOCATED - "+allocated)
    if allocated_stderr.strip() != "":
        logger.warning("ALLOCATED - "+allocated_stderr.strip())
        logger.warning("ALLOCATED - getting allocated resource failed for partition "+partition+".")
    else:
        logger.info("ALLOCATED - Allocated resource for partition "+partition+" and resource "+resource+" is "+allocated+".")
        return allocated

#def get_allocated_nodes_slurm(partition,resource):
#    nodes = get_nodes_per_partition_slurm(partition,resource)
#    logging.info("Command : scontrol show node "+nodes+" | grep '   AllocTRES' | awk -F '=' '{print $2}'")
#    allocated_nodes = subprocess.Popen("scontrol show node "+nodes+" | grep '   AllocTRES' | awk -F '=' '{print $2}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#    allocated_nodes_stderr = allocated_nodes.communicate()[1]
#    allocated_nodes_stdout = allocated_nodes.communicate()[0]
#    allocated_nodes = allocated_nodes_stdout.strip()
#    logging.info("ALLOCATED - "+allocated_nodes)
#    if allocated_nodes_stderr.strip() != "":
#        logging.warning("ALLOCATED - "+allocated_nodes_stderr.strip())
#        logging.warning("ALLOCATED - getting allocated nodes failed for partition "+partition+".")
#    else:
#        logging.info("ALLOCATED - Allocated nodes for partition "+partition+" and resource "+resource+" are "+allocated_nodes+".")
#        return allocated_nodes

def get_number_of_resource_available_slurm(partition,qos,resource):
    allocated_nodes = get_allocated_resources_slurm(partition,resource)
    quota = get_resource_quota_slurm(qos,partition,resource)
    if int(allocated_nodes) == 0:
        logger.info("No node is allocated.")
        total_resource = get_total_resource_slurm(partition,resource)
        if quota == "":
            quota = total_resource
        logger.info("Quota is "+quota+".")
        if int(total_resource) >= int(quota):
            available_resource = int(quota)
            logger.info("Since no node is allocated, "+str(total_resource)+" "+resource+" are available. Furthermore, your quota is "+str(quota)+" "+resource+". So, "+str(available_resource)+" "+resource+" are truly available.")
            #return available_resource
        elif int(total_resource) < int(quota):
            available_resource = int(total_resource)
            logger.info("Since no node is allocated, "+str(total_resource)+" "+resource+" are available. However, your quota is "+str(quota)+" "+resource+". So, "+str(available_resource)+" "+resource+" are truly available.")
            #return available_resource
    else:
        total_resource = get_total_resource_slurm(partition,resource)
        if quota == "":
            quota = total_resource
        allocated = get_allocated_resources_slurm(partition,resource)
        logger.info(str(allocated)+" nodes are allocated.")
        total_bis = int(total_resource) - int(allocated)
        if int(total_bis) >= int(quota):
            available_resource = int(quota)
            logger.info("Since "+str(allocated)+" node(s) is(are) allocated, "+str(total_bis)+" "+resource+" are available. However, your quota is "+str(quota)+" "+resource+". So, "+str(available_resource)+" "+resource+" are truly available.")
            #return available_resource
        elif int(total_bis) < int(quota):
            available_resource = int(total_bis)
            logger.info("Since "+str(allocated)+" node(s) is(are) allocated, "+str(total_bis)+" "+resource+" are available. However, your quota is "+str(quota)+"  "+resource+". So, "+str(available_resource)+" "+resource+" are truly available.")
    return available_resource
    
def get_total_resource_sge(partition,resource):
    total = subprocess.Popen(f"qstat -g c | grep {partition} | awk -F ' ' '{{print $5}}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logger.info(f"COMMAND - qstat -g c | grep {partition} | awk -F ' ' '{{print $5}}'\n")
    logger.info(f"Total resource is : {total}.\n")
    total_stderr = total.communicate()[1]
    if total_stderr.strip() != "":
        logger.warning(total_stderr.strip())
        logger.warning(f"TOTAL - getting total resource failed for queue {partition}.\n")
    else:
        logger.info(f"TOTAL - Total available for queue {partition} and resource {resource} is {total}.\n")
        return total

def get_resource_quota_sge(partition,resource):
    quota = subprocess.Popen(f"qquota -u $LOGNAME | grep {partition} | awk -F 'slots' '{{print $2}}' | awk -F ' users' '{{print $1}}' | awk -F '/' '{{print $2}}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    quota_stderr = quota.communicate()[1]
    if quota_stderr.strip() != "":
        logger.warning(f"QUOTA - getting resource quota failed for queue {partition}.\n")
    else:
        logger.info(f"QUOTA - Quota for queue {partition} and resource {resource} is {quota}.\n")
        return quota
        
def get_number_of_resource_available_sge(partition,resource):
    total = get_total_resource_sge(partition,resource)
    quota = get_resource_quota_sge(partition,resource)
    sys.stdout.write(str(total)+str("\n"))
    sys.stdout.write(str(quota)+str("\n"))

    if int(total) >= int(quota):
        available_resources = int(quota)
        logger.info(f"Since no node is allocated, {total} {resource} are available. Furthermore, your quota is {quota} {resource}. So, {available_resources} {resource} are truly available.\n")
    elif int(total) < int(quota):
        available_resources = int(total)
        logger.info(f"Since no node is allocated, {total} {resource} are available. However, your quota is {quota} {resource}. So, {available_resources} {resource} are truly available.\n")
    return available_resources

def get_number_of_resource_available(partition,resource,qos,cluster):
    if cluster == "sge":
        logger.info(f"inside get_number_of_resource_available : partition = {partition}, resource = {resource}\n")
        available_resources = get_number_of_resource_available_sge(partition,resource)
        return available_resources
    elif cluster == "slurm":
        available_resources = get_number_of_resource_available_slurm(partition,qos,resource)
        return available_resources
