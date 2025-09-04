#!/usr/bin/env python3
# -*- coding: utf-8 -*-

### GAD PIPELINE ###
## upload_labkey.py
## Description : upload metrics and push it into labkey server
## Usage : python upload_labkey.py
## Output : None
## Requirements : python 3

## Author : Emilie.Tisserant@u-bourgogne.fr,yannis.duffourd@u-bourgogne.fr,anne-sophie.briffaut@u-bourgogne.fr, valentin.vautrot@u-bourgogne.fr
## Creation Date : 20230420
## last revision date : 20250704
## Known bugs : None


import os
import sys
import getopt
import labkey
import json
from datetime import date, datetime, timedelta
import ssl
import time
import glob
import pandas as pd

inDir = ""
logFile = ""
infoFile = ""
today = date.today()
verboseOnly = False
isBionano = False
nbs = False

# manage options
try:
	opts, args = getopt.getopt(sys.argv[1:], "vhl:i:n:x:", [ "verbose", "help" , "log" , "inputDir", "nbs" ] )
except getopt.GetoptError as err:
	# print help information and exit:
	print(err) # will print something like "option -a not recognized"
	sys.exit(2)

for o, a in opts:
	if o in ( "-h", "--help" ):
		sys.exit()
	elif o in ( "-l", "--log" ):
		logFile = a
		sys.stderr = open( logFile , 'a' )
	elif o in ( "-i" , "--inputDir" ):
		inDir = a
	elif o in ( "-v" , "--verbose" ):
		verboseOnly = True
	elif o in ( "-n", "--nbs" ):
		nbs = True
	else:
		assert False, "unhandled option"


# detect if is bionano : in this case, only one sample
lastDir = inDir.split("/")[-1]
lastDir = lastDir.replace("/", "")
if lastDir.startswith("dijoca"):
	isBionano = True

# fastq directory
fastqdir = "/archive/gad/shared/fastq/"



# Test if fastq files exist in archive
if not isBionano:
	sample_dir = sorted([d for d in os.listdir(inDir) if os.path.isdir(inDir+"/"+d) and not d.startswith("logs")])
	sample_to_upload = []
	for sample in sample_dir:
		# Test if fastq files exists
		if os.path.isfile(fastqdir+"/"+sample+".R1.fastq.gz") or os.path.isfile(fastqdir+"/"+sample+".R2.fastq.gz"):
			sys.stderr.write("%s fastq files already exist\n" %(sample))
		else:
			sample_to_upload.append(sample)

	for sample in sample_to_upload:
		sys.stderr.write("sample to upload : %s\n" %(sample))
else:
	sample_to_upload.append(lastdir)

# Variables to insert
statut = "Analysé"
bioinfo = os.popen('grep LKUSERNAME /users/$USER/.bashrc | cut -d "=" -f 2').read()
if bioinfo == "":
	bioinfo = os.popen('grep $USER /etc/passwd | cut -d ":" -f 5').read()
bioinfo = (bioinfo).strip()
files = list(glob.glob(inDir+"/*"))
files.sort(key=os.path.getctime)
date_re = time.strftime("%Y-%m-%d", time.gmtime(os.path.getctime(files[0])))
date_an = time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(files[-1])))

# Labkey Query
server_context = labkey.utils.create_server_context(domain="translad.chu-dijon.fr", container_path="home/GAD/Génétique moléculaire", context_path="labkey")
sys.stderr.write("Querying Suivi exomes dataset ... ")
try :
	allExome = labkey.query.select_rows(server_context, schema_name="assay.General.Suivi exomes", query_name="Data", timeout=120)
except labkey.exceptions.ServerContextError as error_text:
	comment = f"labkey server interrogation failed."
	sys.stderr.write(f"{comment} ({error_text})")
if nbs:
	try:
		astreinte = labkey.query.select_rows(server_context, schema_name="assay.General.Lists", query_name="Astreinte_Perigenomed", timeout=120)
	except labkey.exceptions.ServerContextError as error_text:
		comment = f"labkey server interrogation failed."
		sys.stderr.write(f"{comment} ({error_text})")
sys.stderr.write(" done \n")

if nbs:
	# check if sample meets min coverage requirements
	bad_samples = [ ]
	lines_to_upload = { } 

	for sample in sample_to_upload:
		qc_file = os.path.join(inDir, "QC.summary.tsv")
		qc_file = pd.read_csv(qc_file, sep="\t")
		idx = [idx for idx in qc_file.index if (qc_file.loc[idx, "SAMPLE"] == sample)]
		idx = idx[0]
		if qc_file.loc[idx, "COVERAGE_MEAN_REFSEQ"] < 25:	
			bad_samples.append(sample)
			sys.stdout.write(f"WARNING : {sample} has mean coverage < 25x. Its status in labkey will be registered as \"Echec séquençage\" and no reader will be assigned.\n")
			lines_to_upload[sample] = ["Echec séquençage : couverture moyenne < 25x"]
		else:
			report = os.path.join(inDir, sample, f"{sample}.pgc1.interpretation_check.tsv" )
			if not os.path.isfile(report):
				sys.stdout.write(f"WARNING : the file {report} was not found !\n")
			else:
				with open(report, "r") as f:
					lines = [line.strip() for line in f]
					lines_to_upload[sample] = [line for line in lines if line.split("\t")[1] == "Interpretation_needed"]

	# NBS : get readers
	dt = datetime.strptime(date_an, '%Y-%m-%d')
	as_starts = [datetime.strptime(dict["start"], "%Y-%m-%d %H:%M:%S.%f") for dict in astreinte["rows"]]
	as_ends = [datetime.strptime(dict["end"], "%Y-%m-%d %H:%M:%S.%f") for dict in astreinte["rows"]]
	current_start = [datetime.strftime(start, "%Y-%m-%d 00:00:00.000") for start, end in zip(as_starts, as_ends) if start <= dt <= end]
	if (len(current_start) == 0) or (len(current_start) > 1):
		sys.stdout.write("WARNING : No starting date or several dates for duty found in Astreinte_Perigenomed timetable. No readers attributed.\n")
		first_reader=""
		second_reader=""
	else:
		current_start = "".join(current_start)
		first_reader = (dict["lecteur1"] for dict in astreinte["rows"] if current_start == dict["start"])
		first_reader = " ".join(first_reader)
		second_reader = (dict["lecteur2"] for dict in astreinte["rows"] if current_start == dict["start"])
		second_reader = " ".join(second_reader)


for line in allExome["rows"]:
	
	if (line["dijexID"] in sample_to_upload):
		
		update = {"RowId": line["RowId"], "statut": statut, "bioinfo": bioinfo, "date_reception": date_re, "date_analyse": date_an}
		sample = line["dijexID"]

		if line['date_analyse'] != None:
			sys.stderr.write("Analysis date exists for %s\n" % (line["dijexID"]))
			continue

		elif nbs:
			if sample not in bad_samples:
				if len(lines_to_upload[sample]) > 0:
					update_nbs = {"RowId": line["RowId"], "commentaires" : "\n".join(lines_to_upload[sample]), "lecture1": first_reader, "lecture2": second_reader, "statut": "Analysé" }
				else:
					update_nbs = {"RowId": line["RowId"], "lecture1": "Interprétation Automatique", "lecture2": "Interprétation Automatique", "resultat": "Négatif", "statut": "Interprété"}
			else:
				update_nbs = {"RowId": line["RowId"], "statut": "Echec séquençage", "commentaires": "\n".join(lines_to_upload[sample])}
			update = {**update, **update_nbs}
		
		labkey.query.update_rows(server_context, schema_name="assay.General.Suivi exomes", query_name="Data",rows=[update])
		sys.stderr.write(f"{sample} - updated labkey with: {update}\n")
