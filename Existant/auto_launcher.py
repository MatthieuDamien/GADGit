#!/usr/bin/env python
# -*- coding: utf-8 -*-



### GAD PIPELINE ###
## auto_launcher.py
## Description :
## Usage :
## Output :
## Requirements : md5sum,python2

## Author : yannis.duffourd@u-bourgogne.fr ; anthony.auclair@u-bourgogne.fr
## Creation Date : 20231107
## last revision date : 20250203
## Known bugs : None

#$ -q batch
#$ -V

import os
import sys
import getopt
import logging
import glob
import hashlib
import time
import re
import labkey
import json
import signal
from subprocess import Popen, PIPE
import subprocess



incDir = ""
outputFile = ""
logFile = ""

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:o:s:l:')
    for opt, arg in opts:
        if opt in ("-d", "--directory"):
            incDir = arg
        elif opt in ("-o" , "--output" ):
            outputFile = arg
        elif opt in ("-s" , "--server" ):
            labkeyserver = arg
        elif opt in ("-l" , "--log" ):
            logFile = arg

opts, args = getopt.getopt(sys.argv[1:], 'd:o:l:s:')
for opt, arg in opts:
    if opt in ("-d", "--directory"):
        incDir = arg
    elif opt in ("-o" , "--output" ):
        outputFile = arg
    elif opt in ("-s" , "--server" ):
        labkeyserver = arg
    elif opt in ("-l" , "--log" ):
        logFile = arg

except getopt.GetoptError:
    print("usage :")
    sys.exit(2)

# check
logging.basicConfig(filename =  '%s' % (logFile), filemode = 'a', level = logging.INFO, format = '%(asctime)s %(levelname)s - %(message)s')

date=time.strftime("%Y%m%d")
logging.info("start : %s" % date)

if incDir == "":
    logging.error("Input directory seems to be empty : stopping execution")
    os.remove(incDir +"/autolaunch.lock")
    sys.exit(1)

def md5_on_file(inc):
    md5_hash = ""
    with open(inc, 'rb') as file_obj:
        file_contents = file_obj.read()
        md5_hash = hashlib.md5(file_contents).hexdigest()
    return md5_hash


def display_sample( incElt ) :
    sys.stdout.write( "%s\n" % json.dumps(incElt, sort_keys=True, indent=4, separators=(',', ': ') , ensure_ascii=False   ) )


if os.path.isfile(incDir +"/autolaunch.lock"):
    logging.info("A lock file was found, previous operation still in progress : Stopping execution")
    logging.info("end : %s" % date)
    sys.exit(0)
else:
    lockStream = open(incDir +"/autolaunch.lock", "w")
    lockStream.write("1")
    lockStream.close()


# check if there is md5
files = glob.glob(incDir + "/*")
logging.info('Found %s files' % len(files) )

md5FileList = []
badBatch = []

for f in files:
    if f.endswith(".md5"):
        logging.info("Found a md5 file : %s" % f)
        md5FileList.append(f)

allSampleList = []
fileToMd5 = {}

# parse md5 file
for elt in md5FileList:
    sampleList = []
    hashTable = {}
    stream = open(elt, "r")
    for line in stream:
        line = line.strip()
        file = re.split('\s+', line)[1]
        md5 =re.split('\s+', line)[0]
        completePathOfFile = incDir + "/" + file
        completePathOfFile = completePathOfFile.replace("//", "/")
        hashTable[completePathOfFile] = md5
        logging.info("Adding file %s with hash %s from %s" % (completePathOfFile, md5, elt))
        sampleList.append(completePathOfFile)
        allSampleList.append(completePathOfFile)
        fileToMd5[completePathOfFile] = elt

    sampleList = sorted(list(set(sampleList)))
    logging.info("%s files added from md5 file %s" % (len(sampleList), elt))


    # check if we have proper pairs R1, R2 in md5
    goThrough = True
    logging.info("LOOKING FOR PAIRS IN MD5")
    for s in sampleList:
        if s.find("R1") != -1:
            s2 = s.replace("R1", "R2")
            if s2 not in sampleList:
                logging.error("File %s has a R1 in md5 file, but no R2. This md5 %s is not complete." % (s , elt))
                goThrough = False
            else:
                logging.info("File %s has a R1 in md5 file and a R2. This md5 %s is complete for this pair." % (s , elt))

        if s.find("R2") != -1:
            s2 = s.replace("R2", "R1")
            if s2 not in sampleList:
                logging.error("File %s has a R2 in md5 file, but no R1. This md5 %s is not complete." % (s , elt))
                goThrough = False
            else:
                logging.info("File %s has a R2 in md5 file and a R1. This md5 %s is complete for this pair." % (s , elt))
        if not goThrough:
            break

    if not goThrough :
        logging.error("Stopping the analysis for file %s : md5 file error." % elt)
        badBatch.append(elt)
        continue

    # check if we have the files on the disk
    logging.info("LOOKING FOR FILES ON DISK")
    for s in sampleList:
        logging.info("Looking for file %s" % s)
        if s.find("R1") != -1:
            s2 = s.replace("R1", "R2")
            if s2 not in files:
                logging.error("File %s is a R1 on disk, but no R2 %s was found." % (s, s2))
                goThrough = False
            else:
                logging.info("File %s is a R1 on disk, and a R2 %s was found." % (s, s2))

        if s.find("R2") != -1:
            s2 = s.replace("R2", "R1")
            if s2 not in files:
                logging.error("File %s is a R2 on disk, but no R1 %s was found." % (s, s2))
                goThrough = False
            else:
                logging.info("File %s is a R2 on disk, and a R1 %s was found." % (s, s2))
        if not goThrough:
            break

    if not goThrough :
        logging.error("Stopping the analysis for file %s : file not found error " % elt)
        badBatch.append(elt)
        continue

    # perform md5 sum on the whole list
    logging.info("PERFORMING MD5SUM CHECK")
    # write a sub md5 file for each file
    md5waiting = []
    for f in hashTable.keys():
        racine = "_".join(re.split('[_.]',f)[0:-2])
        mdStream = open(racine + ".check", "w")
        mdStream.write("%s %s\n" % (hashTable[f], f))
        mdStream.close()
        cmd = "qsub -v INPUTFILE=" + racine + ".check /user1/gad/ya0902du/bin/check_md5sum.sh"
        logging.info("Launching md5check : %s" % cmd)
        os.system(cmd)
        # qsub_md5  = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, text=True)
        # qsub_md5_stderr = qsub_md5.communicate()[1]
        # sys.stderr.write("%s\n" % qsub_md5_stderr )
        # if qsub_md5_stderr.strip() != "":
        #     logging.warning("MV - "+ qsub_md5_stderr.strip())
        #     logging.error("QSUB - qsub md5 subprocess failed for %s" % (racine + ".check"))
        #     logging.info("end : %s" % date)
        #     os.remove(incDir +"/autolaunch.lock")
        #     sys.exit(1)
        md5waiting.append(racine)

    # now perform an infinite loop waiting for the md5check results
    stop = False

    while not stop:
        tmpmd5waiting = []
        for f in md5waiting:
            if os.path.isfile("/work/gad/shared/public_shared/BIOMNIS2/inc/check_md5sum." + f .split("/")[-1] + ".OK"):
                logging.info("MD5 check is successfull for sample %s" % f)
                continue
            elif os.path.isfile("/work/gad/shared/public_shared/BIOMNIS2/inc/check_md5sum." + f .split("/")[-1] + ".failed"):
                logging.info("MD5 check is failed for sample %s" % f)
                goThrough = False
            else:
                logging.info("No results found for sample %s, waiting next turn" % f)
                tmpmd5waiting.append(f)
        md5waiting = []
        md5waiting = tmpmd5waiting
        logging.info("Waiting another 60 s for job completion")
        time.sleep(60)
        if len(md5waiting) == 0:
            stop = True
        else:
            logging.info("%s more files to wait" % len(md5waiting))

    if not goThrough :
        logging.error("Stopping the analysis for file %s : md5 check error" % elt)
        badBatch.append(elt)
        continue

# interrogate labkey to get information
data = {}

# stop if no sample to analyze
if len(allSampleList) == 0:
    logging.info("No sample found")
    logging.info("end : %s" % date)
    os.remove(incDir +"/autolaunch.lock")
    sys.exit(0)


# server_context = labkey.utils.create_server_context(domain="translad.chu-dijon.fr", container_path="home/GAD/Génétique moléculaire", context_path="labkey")
server_context = labkey.utils.create_server_context(domain=labkeyserver, container_path="home/GAD/Génétique moléculaire", context_path="labkey")

logging.info("Querying Suivi exomes dataset ... ")
allExome = labkey.query.select_rows(server_context, schema_name = "study", query_name = "Suivi exomes")
logging.info(" done \n")

# construct data
logging.info("CONSTRUCTING THE ANALYSIS")
for elt in allSampleList:
    logging.info("Testing file %s" % elt)
    # verify if this sample has to be treated by getting the md5 name
    if fileToMd5[elt] in badBatch:
        logging.info("Passing file %s, due to issue with the batch" % elt)
        continue

    # extract the gad number
    logging.info("trying to match sample in filename %s" % elt)
    alias = re.split('[_.]', elt.split("/")[-1])[1]
    logging.info("Found an alias in filename : %s" % alias)
    if alias not in data.keys():
        logging.info("Alias is new %s, creating it" % (alias))
        data[alias] = {}
        data[alias]["files"] = []
    logging.info("Adding file %s to alias %s" % (elt, alias))
    data[alias]["files"].append(elt)

# parse labkey
for elt in data.keys():
    found = False
    for line in allExome["rows"]:
        if str(line["aliasID"]) != elt:
            continue
        if str(line["statut"]) in ["Annulé", "Echec CQ"]:
            continue
        if line["dijexID"] == None or line["dijexID"] == "Non renseigné" or  line["dijexID"] == "None":
            continue

        data[elt]["alias"] = str(line["aliasID"])
        logging.info("alias is %s" % data[elt]["alias"])
        data[elt]["gad"] = str(line["SpecimenID"])
        logging.info("gad is %s" % data[elt]["gad"])
        data[elt]["dijexId"] = str(line["dijexID"])
        logging.info("dijexId is %s" % data[elt]["dijexId"])
        data[elt]["PJ"] = str(line["numero_envoi"])
        logging.info("PJ is %s" % data[elt]["PJ"])
        if data[elt]["PJ"] == "" or data[elt]["PJ"] == None or data[elt]["PJ"] == "Non renseigné":
            pj = sorted(data.keys())[0] + "_" + sorted(data.keys())[-1]
            data[elt]["PJ"] = pj
            logging.info("PJ modified into %s" % data[elt]["PJ"])

# mv data
pjname = 1
PJCreated = []
PJ = {}
# create the pj
for elt in data.keys():
    pathToCreate = "/work/gad/shared/analyse/" + data[elt]["PJ"] + "_" + str(pjname)
    if pathToCreate not in PJCreated:
        logging.info("PJ directory not already found in this session")
        while os.path.isdir(pathToCreate):
            logging.info("PJ directory %s already existing, computing new name" % pathToCreate)
            pjname += 1
            pathToCreate = "/work/gad/shared/analyse/" + data[elt]["PJ"] + "_" + str(pjname)
            logging.info("PJ directory new name : %s" % pathToCreate)
        os.mkdir(pathToCreate)
        PJCreated.append(pathToCreate)
        logging.info("PJ directory created %s" % (pathToCreate))
    if pathToCreate not in PJ.keys():
        PJ[pathToCreate] = []



    for f in data[elt]["files"]:
        # compute the new name of the file
        finalName = ""
        if f.find('R1') != -1:
            finalName = data[elt]["dijexId"] + ".R1.fastq.gz"
            PJ[pathToCreate].append(data[elt]["dijexId"])
        if f.find('R2') != -1:
            finalName = data[elt]["dijexId"] + ".R2.fastq.gz"
        logging.info("File will be rename from %s to %s" %(f, finalName))


        if not os.path.isfile(pathToCreate +"/" + finalName):
            mv = "mv " + f + " " + pathToCreate + "/" + finalName
            os.system(mv)
            # mv_stderr = mv.communicate()[1]
            # if mv_stderr.strip() != "":
            #     logging.warning("MV - "+ mv_stderr.strip())
            #     logging.error("MV - mv subprocess failed for %s to %s" % (f, finalName))
            #     logging.info("end : %s" % date)
            #     os.remove(incDir +"/autolaunch.lock")
            #     sys.exit(1)
        else:
            logging.warning("The file %s already exists in target directory %s" % (finalName, pathToCreate))

# construct the bash command to execute for analysis launch
for pj in PJ.keys():
    tech = ""
    for elt in PJ[pj]:
        if elt.startswith("dijex"):
            tempTech = "ES"
        if elt.startswith("dijen"):
            tempTech = "GS"
        if elt.startswith("dijarn"):
            tempTech = "RNA"

        if tech == "":
            tech = tempTech
        else:
            if tech != tempTech:
                logging.error("Different technologies in the same PJ %s: aborting" % pj)
                break
    cmd = ""
    if tech == "ES":
        cmd = "cd " + pj + " && qsub -q batch -v ANALYSISDIR="+ pj + "/,MODE='PROD',CONFIGFILE=/work/gad/shared/pipeline/2.10.1/common/analysis_config.tsv /work/gad/shared/pipeline/2.10.1/wes_pipeline/full_wes.sh"
    if tech == "GS":
        cmd = "cd " + pj + " && qsub -q batch -v ANALYSISDIR=" + pj + "/,MODE='PROD',CONFIGFILE=/work/gad/shared/pipeline/2.10.1/common/analysis_config.tsv /work/gad/shared/pipeline/2.10.1/wgs_pipeline/full_wgs_gpu.sh"
    if tech == "RNA":
        cmd = "cd " + pj + " && qsub -q batch -v ANALYSISDIR=" + pj + "/,MODE='PROD',CONFIGFILE=/work/gad/shared/pipeline/2.10.1/common/analysis_config.tsv /work/gad/shared/pipeline/2.10.1/rnaseq_pipeline/full_rnaseq.sh"

    logging.info("Launching analysis on dir %s with command : %s" % (pj,cmd))
    os.system(cmd)
    # qsub = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    # qsub_stderr = qsub.communicate()[1]
    # if qsub_stderr.strip() != "":
    #     logging.warning("QSUB - "+ qsub_stderr.strip())
    #     logging.error("QSUB - qsub subprocess failed for %s" % pj)

    # mail
    cmd = 'echo -e "Bonjour,\n\nDes donnees ULTRAPRENATOME ont ete recues et l analyse bioinformatique a ete automatiquement lancee dans' + pj + '\n\n\nBonne journee" | mail -s ' + pj + ' -c biologistesuf6254@u-bourgogne.fr gad-astreinte-bioinfo@u-bourgogne.fr'
    os.system(cmd)
    # mail = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    # mail_stderr = mail.communicate()[1]
    # if mail_stderr.strip() != "":
    #     logging.warning("MAIL - "+ mail_stderr.strip())
    #     logging.error("MAIL - mail subprocess failed for %s" % pj)


date=time.strftime("%Y%m%d")
logging.info("end : %s" % date)
os.remove(incDir +"/autolaunch.lock")








#
