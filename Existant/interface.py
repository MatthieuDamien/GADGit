#!/usr/bin/python
# -*- coding: utf-8 -*-

### LABKEY TOOLS ###
##
## Version : 0.1.0
## Description :
## Usage :
## Output : None
## Requirements : python 2.7+


import os
import sys
import getopt
import logging
import glob
import re
import json
import time
from collections import defaultdict
import subprocess


# manage options
inputDirectory = ""
outputFile = ""
envFile = ""
workflowFile = ""
global wf
global directories
directories = []
global analysisTree
global data
data = {}


# global variables
directories = []
sampleList = []
env = {}




#opts, args = getopt.getopt(sys.argv[1:], 'd:o:h:w:u:')
opts, args = getopt.getopt(sys.argv[1:], 'd:')
for opt, arg in opts:
	if opt in ("-d", "--directory"):
		inputDirectory = arg
		inputDirectory = inputDirectory.strip()
	#elif opt in ("-h" , "--html" ):
		#htmlFile = arg
	#elif opt in ("-o" , "--output" ):
		#outputFile = arg
	#elif opt in ("-w", "--workflow"):
		#workflowFile = arg
	#elif opt in ("-u", "--user"):
		#user = arg


###################################################################################################################

htmlFile = inputDirectory + "/" + inputDirectory.split("/")[-1] + ".html"
outputFile = inputDirectory  + "/rerun.sh"
analysistype, user = None, None
f = inputDirectory + "/batch.info"
if os.path.isfile(f):
	fStream = open( f , 'r' )
	for line in fStream:
		line = line.strip()
		if re.search('Analysis type', line):
			analysistype = line.split("\t")[1]
		if re.search('Operator', line):
			user = line.split("\t")[1]				
	fStream.close()
else:
	sys.stderr.write('batch.info file not found\n')
	sys.exit(1)
if analysistype == "wes":
	workflowFile = "/work/gad/em0342ti/analyses/interface/full_wes.json"
elif analysistype == "wgs":
	workflowFile = "/work/gad/em0342ti/analyses/interface/full_wgs.json"
if analysistype == None or user == None:
	sys.stderr.write('analysis type or user missing\n')
	sys.exit(1)
###################################################################################################################


	



def parsejson(workflow_file):
	wf = json.load(open(workflow_file, "r"))
	dictjson = wf[0]["tree"]
	step = []
	global stepdict
	stepdict = defaultdict(dict)
	
	for elt in dictjson.keys():
		if dictjson[elt]["parent"][0] == "None":
			step.append(elt)
			stepdict[elt] = dictjson[elt]
			dictjson.pop(elt)
			break

	while len(dictjson.keys()) > 0:
		for elt in dictjson.keys():
			#print("%s" % (elt))
			# get the parent name of the step
			for p in dictjson[elt]["parent"]:
				#print("\t%s" % (p))
				parentFound = False
				parentIndex = None
				stepFound = False

				for i in range(0,len(step)):
					if step[i] == p:
						parentFound = True
						parentIndex = i
						#print("\t\ti:%s step:%s = p:%s" % (i,step[i],p))

					if step[i] == elt:
						stepFound = True

			if stepFound :
				continue

			if parentFound and not stepFound:
				step.append(elt)
				stepdict[elt] = dictjson[elt]
				dictjson.pop(elt)
				break
	return -1	
	
	
# get all samples from dir
def analyse_directory(incDir):
	global directories
	global trio
	global denovo
	#sys.stderr.write('Analyzing work directory ... ')

	files = glob.glob(incDir + "/*")
	#sys.stderr.write('Found %s files\n' % len(files) )

	for f in files :
		# ~ sys.stderr.write("\t%s\n" % f)
		# deal with directories
		if os.path.isdir(f):
			s = f.split ("/")[-1]
			if s == "logs":
				continue
			directories.append(s)

	if(len(directories) == 0) :
		logging.info("No directory detected : nothing to do : EXITING")
		sys.exit(0)

	logging.info('Work directory analyzed: found %s directories' % (len(directories)))
	
	denovo = {}
	trio = defaultdict(list)
	for elt in directories:
		f = incDir + "/"+elt+"/"+elt+".denovo"
		if os.path.isfile(f):
			denovo[elt] = []
			fStream = open( f , 'r' )
			for line in fStream:
				s = line.split()
				for d in s:
					denovo[elt].append(d)
					trio[d]=s
						
			fStream.close()
	
	
	
def analyze_log_for_exit_code(incLog):
	exit_code = None
	for line in open(incLog, "r"):
		line = line.strip()
		# search exit code
		if re.search('exit code', line):
			#sys.stderr.write("Found exit code line : %s\n" % line)
			str_ec = line.split(":")[1]
			str_ec.replace(" ", "")
			if len(str_ec) > 0:
				exit_code = int(str_ec)
			else:
				exit_code = None
	if exit_code is not None:
		return exit_code
	else:
		#sys.stderr.write("No exit code found, returning -1\n")
		return -1	


def check_job_statut(sgename):
    #result = subprocess.run(["/work/gad/shared/bin/gqstat | grep -E -w " +sgename+ " | sed \'s/  */\t/g\' | cut -f5"], shell=True, check=True, universal_newlines=True, stdout=subprocess.PIPE)
    result = subprocess.run(["/work/gad/shared/bin/uqstat "+user+" | grep -E -w " +sgename+ " | sed \'s/  */\t/g\' | cut -f5"], shell=True, check=True, universal_newlines=True, stdout=subprocess.PIPE)
    return result.stdout		




########################################  HTML  #####################################################################

def create_htmldict():

	htmldict = defaultdict(dict)
	for sample in directories:
		for elt in stepdict:
			
			# logfile
			lognamebase = stepdict[elt]["logname"]
			sge_name = stepdict[elt]["sge_name"]
			log_type = stepdict[elt]["log_type"]
			prefix = ""
			if log_type == "sample" or log_type == "trio" or log_type == "denovo" :
				prefix = sample + "/logs/"
			if log_type == "general":
				prefix = "logs/"
			if log_type == "analysisdir":
				prefix = ""
			if lognamebase.find("$(sample)"):
				lognamebase = lognamebase.replace("$(sample)" , sample)
			if lognamebase.find('$(date)'):
				lognamebase = lognamebase.replace('$(date)' , '*')	
			files = glob.glob(inputDirectory + "/" + prefix + lognamebase)
			if len(files) > 0:
				# parse the exit code for the last file
				files.sort(key=os.path.getmtime)
				logfile = files[-1]
				ec = analyze_log_for_exit_code(files[-1])
			else:
				logfile = "No_log_file"
				ec = -1
			
			# sgename
			if sge_name.find("$(sample)"):
				sge_name = sge_name.replace("$(sample)" , sample)
			if sge_name.find("$(directory)"):
				sge_name = sge_name.replace("$(directory)" , inputDirectory.split("/")[-1])
			statut = check_job_statut(sge_name)
			htmldict[elt][sample] = [sample,ec,statut]
			
	return htmldict


		

def html_beamer(htmldict, stepslist):
	global htmlStream
	htmlStream.write("<tr>\n")
	htmlStream.write("<th></th>\n")
	for sample in directories:
		htmlStream.write("<th>%s</th>\n" % (sample))
	htmlStream.write("</tr>\n")
	for step in htmldict:
		v = 0
		for sample in directories:
			if htmldict[step][sample][1] != 0 and htmldict[step][sample][1] != -1 or htmldict[step][sample][2] != "":
				v = 1
		if v == 0:
			htmlStream.write("<tr hide=yes>\n")
		else:
			htmlStream.write("<tr>\n")	
		htmlStream.write("<th>%s</th>\n" % (step))
		for sample in directories:
			if htmldict[step][sample][2] != "":
				#print("%s" % (htmldict[step][sample][2]))
				if htmldict[step][sample][2] == "r\n":
					color = "background-color: #FCE643;"
					code = htmldict[step][sample][2]
				else:
				    color = "background-color: #808080;"
				    code = htmldict[step][sample][2]
			elif htmldict[step][sample][1] == 0:
				color = "background-color: #008000;"
				code = htmldict[step][sample][1]
			elif htmldict[step][sample][1] == -1:
				color = ""
				code = ""
			else:
				color = "background-color: #8B0000;"
				code = htmldict[step][sample][1]

			if stepdict[step]["log_type"] == "sample" or stepdict[step]["log_type"] == "trio" or stepdict[step]["log_type"] == "denovo":
				name = step+"-"+sample
				if name in stepslist:
					htmlStream.write("<td style=\"%s\" align=\"center\" redo=\"yes\">%s</td>\n" % (color, str(code)))
				else:
					htmlStream.write("<td style=\"%s\" align=\"center\">%s</td>\n" % (color, str(code)))
		if stepdict[step]["log_type"] == "general" or stepdict[step]["log_type"] == "analysisdir":
			size = len(directories)
			if step in stepslist:
				htmlStream.write("<td colspan=\"%s\" style=\"%s\" align=\"center\" redo=\"yes\">%s</td>\n" % (size, color, str(code)))
			else:
				htmlStream.write("<td colspan=\"%s\" style=\"%s\" align=\"center\">%s</td>\n" % (size, color, str(code)))
		htmlStream.write("</tr>\n")
		
def html_footer_beamer():
	global htmlStream
	htmlStream.write("</table>\n</body>\n</html>")
	htmlStream.close()


def html_header_beamer():
	global htmlStream
	htmlStream = open(htmlFile, "w")
	# header
	htmlStream.write("<!DOCTYPE html>\n")
	htmlStream.write("<html lang=\"fr\">\n<head><meta charset=\"utf-8\">\n")
	htmlStream.write("<script>\nfunction toggle(thisname) {\n tr=document.getElementsByTagName(\'tr\')\n for (i=0;i<tr.length;i++){\n if (tr[i].getAttribute(thisname)){\nif ( tr[i].style.display==\'none\' ){\n tr[i].style.display = \'\';\n }\n else {\n tr[i].style.display = \'none\';\n }\n }\n }\n }\n\n")
	htmlStream.write("function rerun(thisname) {\ntd=document.getElementsByTagName(\'td\')\nfor (i=0;i<td.length;i++){\nif (td[i].getAttribute(thisname)){\nif (td[i].style.backgroundColor==\'red\'){\nif (td[i].innerHTML == \"0\"){\n td[i].style.backgroundColor = \'#008000\';\n }\n else if (td[i].innerHTML == \"\"){\n td[i].style.backgroundColor = \'\';\n }\n else if (td[i].innerHTML == \"r\\n\"){\n td[i].style.backgroundColor = \'#FCE643\';\n }\n else if (td[i].innerHTML == \"qw\\n\"  || td[i].innerHTML == \"hqw\\n\"  || td[i].innerHTML == \"Eqw\\n\" ){\n td[i].style.backgroundColor = \'#808080\';\n }\n else {\n td[i].style.backgroundColor = \'#8B0000\';\n }\n }\n else {\n td[i].style.backgroundColor = \'red\';\n}\n}\n}\n}\n</script>\n\n")
	htmlStream.write("<title>\"%s\"</title>\n</head>\n<body>\n" % inputDirectory)
	htmlStream.write("<button onClick=\"toggle(\'hide\');\">Show / Hide</button>\n")
	htmlStream.write("<button onClick=\"rerun(\'redo\');\">Rerun</button>\n")
	htmlStream.write("<table>\n<th></th>\n")
	
    
###################################################################################################################

def children():
	childrens = {}
	for elt in stepdict:
		childrens[elt] = []
	for elt in stepdict:	
		for p in stepdict[elt]["parent"]:
			if p != "None":
				childrens[p].append(elt)        
	return childrens
	
def redo(s):
	child = children()
	analysis = [s]
	c = child[s]
	for e in c:
		analysis.append(e)	    		
		c.extend(child[e])
	analysis = list(reversed((list(dict.fromkeys(reversed(analysis))))))
	return analysis


def redo_from_sample(st,sa):
	steps = redo(st)
	samples, temp = [sa], []
	stepslist = []
	for s in stepdict:
		if s in steps:
			if stepdict[s]["log_type"] == "general" or stepdict[s]["log_type"] == "analysisdir":
				#print("%s_DIR" % (s))
				stepslist.append(s)
				samples = directories
			elif stepdict[s]["log_type"] == "trio" and sa in trio and samples != directories :
				samples = trio[sa]
				for a in samples:
					#print("%s_%s" % (s,a))
					stepslist.append(s+"-"+a)
			elif stepdict[s]["log_type"] == "denovo" :
				temp = []
				for a in samples:
					if a in trio and a != trio[a][0] and trio[a][0] not in temp:
						temp.append(trio[a][0])
						stepslist.append(s+"-"+trio[a][0])
				#samples = temp
			else:
				for t in temp:
					if t not in samples:
						samples.append(t)				
				for a in samples:
					stepslist.append(s+"-"+a)
	return stepslist	
	
def extract_commands(sgename):    
	files = glob.glob( inputDirectory + "/full_w*s*.*.log" )
	files.sort(key=os.path.getmtime)
	f = files[-1]
	fStream = open(f,'r',encoding="latin-1")
	for line in fStream:
		if not line.startswith( "Command" ):
			continue
		if line.find( sgename ) == -1 :
			continue
		else:
			line = line.replace( "Command : " , "" )
			line = line.replace( ":" , "" )
			return line
			break
	fStream.close()


def redo_from_list(sl):
	stepslist = []
	for s in sl:
		if len(s) == 1:
    			steps = redo_from_sample(s[0],"")
		else:
    		    	steps = redo_from_sample(s[0],s[1])
		stepslist.extend(steps)
	stepslist = list(reversed((list(dict.fromkeys(reversed(stepslist))))))
	return stepslist
				

def print_commands_from_list(stepslist):
	commands = []
	for st in stepslist:
		s = st.split("-")[0]
		sgename = "-N " + stepdict[s]["sge_name"]
		if stepdict[s]["log_type"] == "general" or stepdict[s]["log_type"] == "analysisdir":	
			if sgename.find("$(directory)"):
				sgename = sgename.replace("$(directory)" , inputDirectory.split("/")[-1])
			sg = sgename.replace("-N " , "")
			commands.append("qdel "+sg)
			commands.append(extract_commands(sgename))
		else: 
			if sgename.find("$(sample)"):
				sgename = sgename.replace("$(sample)" , st.split("-")[1])
			sg = sgename.replace("-N " , "")
			commands.append("qdel "+sg)
			commands.append(extract_commands(sgename))
	outStream = open( outputFile , "w" )
	outStream.write( "#!/bin/bash\n\n" )
	for c in commands:
		outStream.write( "%s\n" % c )
	outStream.close()

def steps_to_redo(htmldict):
	toredolist = []
	for step in htmldict:
		for sample in directories:
			if htmldict[step][sample][2] == "" and htmldict[step][sample][1] != 0 and htmldict[step][sample][1] != -1:
				if stepdict[step]["log_type"] == "general" or stepdict[step]["log_type"] == "analysisdir":
					toredolist.append([step,""])
					break
				else:
					toredolist.append([step,sample])            
	return toredolist
			
###################################################################################################################    
# main
def main( ):

	parsejson(workflowFile)
	analyse_directory(inputDirectory)
	
	htmldict = create_htmldict()
	toredolist = steps_to_redo(htmldict)
	stepslist = redo_from_list(toredolist)
	html_header_beamer()
	html_beamer(htmldict,stepslist)
	html_footer_beamer()
	
	print_commands_from_list(stepslist)
	

	
	
if __name__ == "__main__":
	main()
