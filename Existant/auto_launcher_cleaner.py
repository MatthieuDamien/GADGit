#!/usr/bin/env python
# -*- coding: utf-8 -*-

### GAD PIPELINE ###
## auto_launcher_clean.py
## Description : Clean sample/flowcell lists and autolauncher event files for samples and flowcells already analysed. Archive autolauncher logfiles and event files, and remove old event files backups. Handle archived log compression and supress old log files from input directory with options.
## Usage : auto_launcher_clean.py [-h] -d INPUT_DIRECTORY [-l LOGFILE] [-e EVENT_FILE] [-s SEQUENCER] [-a ARCHIVE_FOLDER]
## Output : -
## Requirements : python3.9

## Author : valentin.vautrot@u-bourgogne.fr
## Creation Date : 20250428
## last revision date : 20250430
## Known bugs : None

import os
import sys
import argparse
import logging
import subprocess
import re
import glob
from datetime import datetime, isoformat
import subprocess
from subprocess import Popen, PIPE
from itertools import chain

# default option values
input_dir_default = "/work/work/shared/s-neomics/data/incoming/logs/"
logFile_default = "autolauncher_cleaner.log"
event_file_default = "/work/work/shared/s-neomics/data/incoming/logs/autolauncher/all.events.log"
sequencer_default = "/neomics/seq1/"
archive_default = "/archive/gad/shared/autolauncher/"
workdir_default = "/work/work/shared/s-neomics/data/analyse"
# options
parser = argparse.ArgumentParser(description="Clean logfiles, event files and sample/flowcell lists whose analysis has correctly been launched with novaseqx autolauncher", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# required
parser.add_argument("-d", "--directory", dest="in_dir", help="complete path of directory of logs to be examined by autolauncher cleaner (must contain autolauncher log folder and subprocesses log folders : autolauncher, concat, organize, info, analysis)", metavar="INPUT_DIRECTORY", required=True)
# with defaults 
parser.add_argument("-l", "--log", dest="logFile", help="path to autolauncher cleaner logfile", default=logFile_default)
parser.add_argument("-e", "--events", dest="event_file", help="file to register autolauncher events that already happened", default=event_file_default)
parser.add_argument("-s", "--sequencer", dest="sequencer", help="path to the sequencer data directory where raw data is received", default=sequencer_default)
parser.add_argument("-a", "--archive", dest="archive_folder", help="path to the archive destination for old autolauncher logs and event files (contains or will make autolauncher and subprocesses log folders)", default=archive_default)
parser.add_argument("-w", "--workingdir", dest="workdir", help="Analysis folder in which analysis directories are created to launch pipelines", default=workdir_default)
parser.add_argument("--remove", action="store_true", help="flag to remove old files from inputdir once copied + remove old events files backups", default=False)
parser.add_argument("--tarball", action="store_true", help="flag to compress by month old (= from at least the previous month) autolauncher logfiles present in archive directory", default=False)

args = parser.parse_args()
in_dir = args.in_dir
sequencer = args.sequencer
event_file = args.event_file
archive_folder = args.archive_folder
workdir = args.workdir

# logging setup
logging.basicConfig(filename =  '%s' % (args.logFile), filemode = 'a', level = logging.DEBUG, format = '%(asctime)s %(levelname)s - %(message)s')
logging.info("START cleaning")

# for time delta calculation in days
today = datetime.today()
# for backup files naming
current_date = datetime.today().strftime("%Y-%m-%d")

# fonctions
def check_output_dir(output_directory):
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory, mode=0o770, exist_ok = True)
        os.chmod(output_directory, mode=0o770)
        logging.info(f"creating output directory: {output_directory} as it does not exists yet.")

def backup(file, destination):
    archive_name = os.path.basename(file)
    archive_name = f"{destination}/{archive_name}_{current_date}.bak"
    logging.info(f"BACKUP - backing up {file} to {archive_name}")
    cmd = list("mv", file, archive_name)
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        sub = subprocess.run(cmd, capture_output=True, text=True, encoding="UTF-8")
        logging.error(f"BACKUP - back up failed for {file} - exit code {sub.returncode} (\"{sub.stderr} {sub.stdout}\")")
        sys.exit(1)
    else:
        logging.info(f"BACKUP - backup successful")

def get_log_date(logfile):
    """Return file creation date as a datetime object for a logfile, from the name if format 20XX-XX-XX is present, or from the file creation date (shell ctime) if not. The logfile argument must be a full path to the logfile.
    Args:
        logfile (str): full path to the logfile from which the creation date should be extracted.
    """    
    re_date = r".*(20\d{2}[\.-]\d{2}[\.-]\d{2}).*"
    if re.search(re_date, os.path.basename(logfile)):
        logdate = re.sub(r".*(20\d{2}[\.-]\d{2}[\.-]\d{2}).*", r"\1", logfile)
        logdate = datetime.fromisoformat(logdate)
    else:
        ctime = os.path.getctime(logfile)
        logdate = datetime.fromtimestamp(ctime)
    return(logdate)

def is_logdate_old(logfile, ndays):
    logdate = get_log_date(logfile=logfile)
    if (today - logdate).days >= ndays:
        return(True)
    else:
        return(False)

def logbackup(log_folder, archive_folder,log_regexp, ndays):
    log_regexp = re.compile(log_regexp)
    loglist = filter(log_regexp.search, os.listdir(log_folder))
    loglist = [ os.path.join(log_folder, log) for log in loglist ]
    # glob.glob(os.path.join(log_folder), globbing)
    log_copy = [ log for log in loglist if is_logdate_old(logfile=log, ndays = ndays) ]
    return_filelist = []
    if len(log_copy) > 0:
        for log in log_copy:
            log = os.path.basename(log)
            logging.info("COPY - Copying {} to {}".format(os.path.join(log_folder, log), os.path.join(archive_folder, log)))
            cmd = "cp {} {}".format(os.path.join(log_folder, log), os.path.join(archive_folder, log))
            logging.info(f"COPY - Command: {cmd}")
            try:
                subprocess.run(cmd.split(" "), check=True)
            except subprocess.CalledProcessError:
                sub = subprocess.run(cmd.split(" "), capture_output=True, text=True, encoding="UTF-8")
                logging.error(f"COPY - Copy of {log} file to {auto_archive} encountered an error with exit code : {sub.returncode} (\"{sub.stderr} {sub.stdout}\")")
                sys.exit(1)
            else:
                return_filelist.append(log)
    return(return_filelist)

def removal(fullname_list):
    if len(fullname_list) > 0:
        for full in fullname_list:
            logging.info(f"DELETE - deleting file: {full}")
            try:
                subprocess.run(["rm", full], check=True)
            except subprocess.CalledProcessError:
                sub = subprocess.run(["rm", full], capture_output=True, text=True, encoding="UTF-8")
                logging.error(f"DELETE - deletion of the file {full} encountered an error with exit code : {sub.returncode} (\"{sub.stderr} {sub.stdout}\")")
                sys.exit(1)
            else:
                continue

# check final destinations dirs
auto_dir = os.path.join(in_dir, "autolauncher")
concat_dir = os.path.join(in_dir, "concat")
orga_dir = os.path.join(in_dir, "organize")
infofile_dir = os.path.join(in_dir, "info")
analysis_dir = os.path.join(in_dir, "analysis")

auto_archive = os.path.join(archive_folder, "autolauncher")
concat_archive = os.path.join(archive_folder, "concat")
orga_archive = os.path.join(archive_folder, "organize")
infofile_archive = os.path.join(archive_folder, "info")
analysis_archive = os.path.join(archive_folder, "analysis")
all_archive_folders = [auto_archive, concat_archive, orga_archive, infofile_archive, analysis_archive]
for folder in [archive_folder] + all_archive_folders:
    check_output_dir(folder)

# backup and read events file
backup(file=event_file, destination=archive_folder)
with open(event_file, "r") as f:
    events = re.split("\n+", f.read())

# cleaning concatenation files
concat_file = f'{sequencer}/concat.list'
backup(file=concat_file, destination=archive_folder)
logging.info(f'removing all the flowcells no more present in the {sequencer} directory from {concat_file}')
flowcell_input = [dir for dir in os.listdir(sequencer) if os.path.isdir(dir) and dir.startswith("2") and not dir.endswith("logs")]
with open(concat_file, "r") as f:
    concat_list = re.split("\n+", f.read())
flowcell_removal = [flowcell for flowcell in concat_list if flowcell not in flowcell_input]
if len(flowcell_removal) != 0:
    flowcell_to_keep = [flowcell for flowcell in concat_list if flowcell in flowcell_input]
    with open(f'{sequencer}/concat.list', "w") as f:
        f.write("\n".join(flowcell_to_keep))
    logging.info("removed {} from {}".format(",".join(flowcell_removal), concat_file))
    # remove eliminated flowcells events from event_file
    final_events = [event for event in events if event.split("\t")[1] not in flowcell_removal]
    logging.info("registered for deletion {} flowcells related events from {}".format(",".join(flowcell_removal), event_file))
else:
    logging.info(f"no flowcell removed from {concat_file}. All the flowcells are still present in the {sequencer} directory.")

# cleaning event file for all samples aleardy analyzed and for family (= analysis folder) already archived
samples_removal = [event.split("\t")[1].split(",") for event in final_events if event.split("\t")[2] == "analysis_launched"]
samples_removal = list(set(chain.from_iterable(samples_removal)))
logging.info("Found {} samples with registered analysis launched events: {}".format(len(samples_removal), ",".join(samples_removal)) )
analysisdir_list = glob.glob(os.path.join(workdir, "PED*")) + glob.glob(os.path.join(in_dir, "dij*"))
analysisdir_list = [os.path.join(workdir, dir) for dir in analysisdir_list if os.path.isdir(os.path.join(workdir,dir))]
samples_analyzed = [ ]
for dir in analysisdir_list:
    samples_found = glob.glob(os.path.join(dir, "dij*"))
    samples_found = [sample for sample in samples_found if os.path.isdir(os.path.join(dir, sample))]
    samples_analyzed = samples_analyzed + samples_found
logging.info("Found samples successfully dispatched in {}: {}".format(workdir, ",".join(samples_analyzed)))
samples_removal = [sample for sample in samples_removal if sample in samples_analyzed]
logging.info("registered for deletion all events for samples whose analysis was successfully dispatched ({})".format(",".join(samples_removal)))
final_events = [event for event in final_events if event.split("\t")[1] not in samples_removal]

# events for samples registered as .R1 and .R1
final_events = [event for event in final_events if event.split("\t")[1].split(".")[0] not in samples_removal]

# events for samples registered as lists of samples (infofile_success, analysis_launched, dispatch_ok)
for event_type in ["infofile_success", "analysis_launched", "dispatch_ok"]:
    samples_list = [event.split("\t")[1] for event in final_events if event.split("\t")[2] == "infofile_success"]
    counter = 0
    for samples in samples_lists:
        current_set = set(samples.split(","))
        if current_set.issubset(set(samples_removal)):
            final_event = [event for event in final_events if event.split("\t")[1] != samples]
            counter += 1
    logging.info(f"registered for deletion all events for which the entire list of samples was processed ({counter} event(s))")

# analysis directories events
family_removal = [event.split("\t")[1] for event in final_events if event.split("\t")[2] == "archive_success"]
final_events = [event for event in final_events if event.split("\t")[1] not in family_removal]
final_events = [event for event in final_events if event.split("\t")[2] != "archive_sucess"]
logging.info("registered for deletion all events for which the analysis directory was sucessfully archived ({})".format(",".join(family_removal)))

# remove all analysis launched events
final_events = [event.split("\t")[1].split(",") for event in final_events if event.split("\t")[2] != "analysis_launched"]

# final event file rewrite
logging.info(f"Updating event file {event_file}")
with open(event_file, "w") as f:
    f.write("\n".join(final_events))
nb_events_removed = len(final_events) - len(events)
logging.info(f"Done.  In total, {nb_events_removed} were removed.")

# autolauncher logs backup (= archive autolauncher log files older than one day)
regexp_dict = { 
"autolauncher" : r"^auto_launcher\..*\.20.*\.log$",
"concat" : r"^(concat_fastq_dij|run_md5_fastq_dij).*(\.out|\.log)$|^20\d+.*\.concat\..*(\.log|\.out)$",
"organize" : r"^organize_data_folder.*(\.log|\.out)$",
"info" : r"^create_sample_information_file.*(\.log|\.out)$",
"analysis" : r"^dispatch_sample.*(\.log|\.out)$"
}
backed = [ ]
for stepname, lognames in regexp_dict.items():
    input_name = os.path.join(in_dir, stepname)
    archive_name = os.path.join(archive_folder, stepname)
    log_ok = logbackup(log_folder=input_name, archive_folder=archive_name, log_regexp=lognames, ndays=1)
    backed = backed + log_ok

# remove old files if --remove
if args.remove:
    # remove old logs from input dir once copied
    log_removal = [ log for log in backed if is_logdate_old(logfile=log, ndays = 7) ]
    removal(fullname_list=log_removal)    

    # remove event files backup from archive (keep only the 3 lasts)
    baklist = glob.glob(os.path.join(archive_folder, "all.events.log.*.bak"))
    baklist = sorted(baklist, key=lambda k: os.path.get_ctime(k))
    baklist_removal = baklist[:-3]
    removal(fullname_list=baklist_removal)

    # remove concat.list backups from archive (keep only the 3 lasts)
    concats = glob.glob(os.path.join(archive_folder, "concat.list_*.bak"))
    concats = sorted(concats, key=lambda k: os.path.get_ctime(k))
    concats_removal = concats[:-3]
    removal(fullname_list=concats_removal)

# tar and compress autolauncher logs by month if --compress
if args.taball:
    for folder in all_archive_folders:
        stepname = os.path.basename(folder)
        unarchived = re.compile(r".*(\.log|\.out)$")
        unarchived = filter(unarchived.search, os.listdir(folder))
        unarchived = [os.path.join(folder, file) for file in unarchived]
        unarchived_dates = (get_log_date(log) for log in unarchived)
        unarchived_dates = (logdate for logdate in unarchived_dates if (logdate.year < today.year or (logdate.year == today.year and logdate.month < today.month)))
        # unarchived_dates = set([datetime.strftime(logdate, "%Y-%m") for logdate in unarchived_dates])
        for logdate in unarchived_dates:
            str_logdate = datetime.strftime(logdate, "%Y-%m")
            logging.info("tarballing logfiles for {} step by month, for the date {}".format(stepname, str_logdate))
            tar_name = os.path.join(folder, f"{stepname}.{str_logdate}.tar")
            to_archive = [logfile for logfile in unarchived if (get_log_date(logfile).year == logdate.year and get_log_date(logfile).month == logdate.month)]
            logging.info("{} unarchived files found".format(len(to_archive)))
            if not os.path.isfile(tar_name) or not os.path.isfile(f"{tar_name}.gz"):
                logging.info(f"Archiving files to {tar_name}")
                cmd = "tar -vf {} {}".format(tar_name, " ".join(to_archive))
                logging.debug(f"Command: {cmd}")
                sub = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, text=True)
                sub_stderr = sub.communicate()[1].strip()
                if sub_stderr != "":
                    print(f"Compress in tarball failed for {stepname} step files at date {str_logdate}: {sub_stderr}")
                    archive_error = 1    
            elif not os.path.isfile(tar_name):
                logging.warning(f"{tar_name} file already exists. Appending unarchived files to the tarball")
                cmd = "tar -rvf {} {}".format(tar_name, " ".join(to_archive))
                logging.debug(f"Command: {cmd}")
                sub = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, text=True)
                sub_stderr = sub.communicate()[1].strip()
                if sub_stderr != "":
                    print(f"Compress in tarball failed for {stepname} step files at date {str_logdate}: {sub_stderr}")
                    archive_error = 1
            elif os.path.isfile(f"{tar_name}.gz"):
                logging.warning(f"it seems that a compressed tarball {tar_name}.gz already exists. Please review and proceed manually to avoid unwanted data loss.")

    if archive_error == 1:
        logging.error("Execution ended with errors. Please check log file in details.")

logging.info("END cleaning")