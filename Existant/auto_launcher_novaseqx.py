#!/usr/bin/env python
# -*- coding: utf-8 -*-

### GAD PIPELINE ###
## auto_launcher_novaseqx.py
## Description : Automatically launches different processes of the gadpipeline (for incoming data from the novaseq x sequencer), given that the right conditions are met.
## Usage : auto_launcher_novaseqx.py [-h] -d INPUT_DIRECTORY [-s [LABKEYSERVER]] [-l LOGFILE] [-e EVENTFILE] [-m MAILFILE] (--concat | --organize | --infofile | --analysis)
## Output : -
## Requirements : python3.9 with labkey API v1.4.0+, mail client

## Author : valentin.vautrot@u-bourgogne.fr
## Creation Date : 20250221
## last revision date : 20250704
## Known bugs : None

import os
import sys
from datetime import datetime
import argparse
import logging
from pathlib import Path
import glob
import re
import labkey
import itertools
import subprocess
import signal
import atexit
import traceback

# default option values
logFile_default = "autolauncher.log"
eventFile_default = "autolauncher.events"
mailFile_default = "autolauncher_mailing.sh"

# "fixed" values
# TODO parse config file in wrapper and create specific options for important external parameters rather than doing this ? (in particular configfile)
configfile = "/work/work/shared/s-neomics/pipeline/2.11.0/common/analysis_config_mesobfc.tsv"
mail_bioinfo = "gad-astreinte-bioinfo@u-bourgogne.fr"
labkey_adress = "translad.chu-dijon.fr"
with open(file=configfile, mode="r") as f:
    for line in f:
        if line.startswith("pipelinebase\t"):
            pipelinebase=line.strip()
            pipelinebase=pipelinebase.split("\t")[1]
        if line.startswith("targetlist\t"):
            targetlist=line.strip()
            targetlist=targetlist.split("\t")[1]
concat_out_dir = "/work/work/shared/s-neomics/data/incoming/"
#organize output_dir = in_dir/organize (see organize step)
analysis_out_dir = "/work/work/shared/s-neomics/data/analyse/"

# options
parser = argparse.ArgumentParser(description="Automatically launches different processes of the gadpipeline (for incoming data from the novaseq x sequencer), given that the right conditions are met.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# required
parser.add_argument("-d", "--directory", dest="in_dir", help="complete path of directory to be examined by autolauncher on the cluster", metavar="INPUT_DIRECTORY", required=True)
# with defaults 
parser.add_argument("-s", "--server", dest="labkeyserver", nargs='?', default=labkey_adress, help="server adress for labkey queries")
parser.add_argument("-l", "--log", dest="logFile", help="autolauncher logfile", default=logFile_default)
parser.add_argument("-e", "--events", dest="eventFile", help="file to register autolauncher events that already happened", default=eventFile_default)
parser.add_argument("-m", "--mail", dest="mailFile", help="path to shell script file to store mailing commands to be executed after the autolauncher cycle", default=mailFile_default)
# flags (required but mutually exclusive)
flags_group = parser.add_mutually_exclusive_group(required = True)
flags_group.add_argument("--concat", action="store_const", const=1, help="flag to attempt the fastq concatenation step")
flags_group.add_argument("--organize", action="store_const", const=1, help="flag to attempt the sample data folders creation")
flags_group.add_argument("--infofile", action="store_const", const=1, help="flag to attempt the creation or update of sample information files")
flags_group.add_argument("--analysis", action="store_const", const=1, help="flag to launch the pipeline analysis for readied data")
flags_group.add_argument("--check", action="store_const", const=1, help="flag to check samples, analysis state and archiving any analysis folder, and send alert mails if needed")

args = parser.parse_args()
in_dir = args.in_dir
unlock_needed = True
step_registered = "autolauncher_setup"

# logging setup
logging.basicConfig(filename =  '%s' % (args.logFile), filemode = 'a', level = logging.DEBUG, format = '%(asctime)s %(levelname)s - %(message)s')
logging.info("AUTORUN CYCLE START")

current_date = datetime.today().strftime("%Y-%m-%d")
current_time = datetime.today().strftime("%Y-%m-%d_%H-%M-%S")


# handling program ending with or without exceptions
@atexit.register
def end_program(folder=in_dir):
    # event revision and writing
    logging.debug("entering program exit procedure...")
    if "events" in globals():
        events.test()
        if events.registration_fail:
            comment = "There is something wrong with autolauncher events registration. Previous or future errors may not be accounted for. (Please also verify event registration file)." 
            logging.error(comment)
            happened = event_count_then_add(format_event(location = "registration_fail", sample="-", event_type="-"))
            if happened == 0:
                send_mail("autolauncher_events_registration_file", "events_registration", comment=comment, error=True)
        events.write_event_file(eventFile)
    # ending
    autolock_file = os.path.join(folder, "autolaunch.lock") 
    if unlock_needed == True and os.path.isfile(autolock_file):
        os.remove(autolock_file)
        logging.debug(f"lock file: {autolock_file} removed.")
    # check events
    logging.info("AUTORUN CYCLE END")

def signal_handler(sig, frame):                       
    sigcomment = f"Signal interruption SIGTERM ({sig}) received during {step_registered} step, which exited prematurely."
    logging.error(sigcomment)
    send_mail(target="signal_interruption", launcherflag=step_registered, comment=sigcomment,error=True)
    sys.exit(1)

signal.signal(signal.SIGTERM, signal_handler)

def error_handler(error_type, value, tb):
    tb =  traceback.extract_tb(tb)
    tb = "".join(traceback.format_list(tb))
    logging.error(f"an unexpected exception of class \"{error_type.__name__}\" occured. Traceback:\n{tb}{value}")

sys.excepthook = error_handler

# functions definitions
def file_exist(file, comment="", log=True):
    if os.path.isfile(file):
        if log:
            logging.info(f"the file: {file} was found. {comment}")
        return True
    else:
        logging.warning(f"the file: {file} was not found.")
        return False

def check_output_dir(output_directory):
    if not os.path.isdir(output_directory):
        os.mkdir(output_directory, mode=0o770)
        logging.info(f"creating output directory: {output_directory} as it does not exists yet.")

def unlocked_to_locked(folder):
    autolock_file = os.path.join(folder, "autolaunch.lock")
    lock_event = format_event(location=folder, sample="autolaunch.lock", event_type="lockfile_found" )
    if os.path.isfile(autolock_file):
        logging.warning(f"A lock file: {autolock_file} was found, previous operation still in progress : Stopping execution.")
        events.add(lock_event)
        global unlock_needed
        unlock_needed = False
        sys.exit(0)
    else:
        events.delete(lock_event)
        lockStream = open(autolock_file, "w")
        lockStream.write("1")
        lockStream.close()
        logging.debug(f"lock file autolaunch.lock created in {folder}")
        return True

def string_in_file(string, file_name, log=True):
    with open(file=file_name, mode="r") as f:
        matches = [ ] 
        for line in f:
            matches += re.findall("^" + string + "$", line)
        if len(matches) == 1:
            if log:
                logging.debug(f"{string} was found in the file {file_name}")
            return True
        elif len(matches) > 1:
            if log:
                logging.error(f"{string} was found several times in the file {file_name}. Something may be wrong.")
            return True
        else:
            if log:
                logging.debug(f"{string} was not found in the file {file_name}")
            return False

def arg_file_check(arg, file_category, default_value):
    if arg == default_value:
        file_path = os.path.join(in_dir, default_value)
    else:
        file_path = arg
    logging.debug(f"Autolauncher {file_category} will be written in the file: {file_path}")
    if not os.path.isfile(file_path):
        Path(file_path).touch(mode=0o770, exist_ok=False)
        os.chmod(file_path, mode=0o770)
        logging.debug(f"creating empty {file_category} file: {file_path} as it does not exists yet")
    return(file_path)

# mail handling setup
mailFile = arg_file_check(args.mailFile, "mail script", mailFile_default)
with open(mailFile, "w") as f:
    f.write("#/!bin/bash\n")

def send_mail(target, launcherflag, comment, keyword="OK", error=False, mail_file = mailFile, mail_bioinfo=mail_bioinfo):
    if error == True:
        with open(mailFile, "a") as f:
            f.write(f"echo -e \"Error in autolauncher for {target} - {launcherflag} process FAILED: {comment}\" | mail -s \"ERROR autolauncher: {launcherflag} step ({target})\" {mail_bioinfo}\n")
        logging.debug(f"Error mail command written for process: {launcherflag}, target = {target}. (comment: {comment})")
    else:
        with open(mailFile, "a") as f:
            f.write(f"echo -e \"Autolauncher for process: {launcherflag}, target = {target} - {comment}\" | mail -s \"autolauncher: {launcherflag} step {keyword} ({target})\" {mail_bioinfo}\n")
        logging.debug(f"Mail command written for {target} {launcherflag} process: {keyword} (comment: {comment})")

# error events handling setup
eventFile = arg_file_check(args.eventFile, file_category="event registration", default_value=eventFile_default)

def format_event(location, sample, event_type):
    """
        Format event to create or compare events for events_register instance. The end value is a string including tab-separated descriptors of the event (location, sample, type). The event "counter" value (number of times event happened) present in the register must not be included.
    Args:
        location (string): General location of the sample affected by the event (e.g. name of the current flowcell examined or name of the autolauncher step or input directory.)
        sample (string): name of the sample affected on the event. (Irrelevant in case of registering a global event).
        event_type (string): describes the type of event. Its value must belong to event_type_values global method of events_register class.
    """    
    event = "{}\t{}\t{}".format(location, sample, event_type)
    return(event)

def event_count_then_add(event):
    """Add an event formatted with format_event function to the global event register, and increment a counter in the register for the number of times it already happened.
    Args:
        event (string): tab separated string of (location, sample, event_type) for the event. (= Ouput of format_event function).
    """    
    times_happened = events.count_event(event)
    events.add(event)
    return(times_happened)

class events_register:

    event_type_values = ["lockfile_found", "concat_file_missing", "concat_ambiguity", "concat_subprocess_fail", "paired_not_found", "fastq_too_small", "no_ped_id", "family_missing", "organize_subprocess_fail", "spl_corresp_file_missing", "infofile_subprocess_fail", "missing_dijex_id", "dismissed_family_members", "labkey_status_bad", "already_analyzed", "analysis_launch_fail", "analysis_launched", "found_in_organize", "archive_fail", "archive_success", "archive_in_progress", "no_archive_log", "infofile_sucess", "dispatch_ok", "no_dispatch", "analysis_ended", "analysis_failed","analysis_ok", "analysis_not_ended"]
    
    def __init__(self, event_file):
        logging.debug(f"trying to create event register from {event_file}") 
        try:
            f = open(event_file, "r")
            f.close()
        except OSError:
            logging.exception(f"the event file {event_file} loading failed")
            self.loaded = False
        else:
            self.loaded = True
            self.location_list = [ ]
            self.sample_list = [ ]
            self.type_list = [ ]
            self.counter_list = [ ]
            with open(event_file, "r") as f:
                for line in f:
                    line = line.strip()
                    self.location_list.append(line.split("\t")[0])
                    self.sample_list.append(line.split("\t")[1])
                    self.type_list.append(line.split("\t")[2])
                    self.counter_list.append(int(line.split("\t")[3]))
            event_list = [format_event(location, sample, event_type) for location, sample, event_type in zip(self.location_list, self.sample_list, self.type_list)]
            self.event_list = event_list
            if "registration_fail" in self.location_list:
                self.registration_fail = True
            else:
                self.registration_fail = False
    
    def listing(self):
        return self.event_list
    
    def add(self, event):
        event_type = event.split("\t")[2]
        if event_type not in self.event_type_values:
            logging.error("CAUTION - Cannot add the event type [{}] to autolauncher event register. Please check that event type belongs to the following list: {}. Event registration as of now is no longer adequate.".format(event_type, ",".join(self.event_type_values)))
        if event in self.event_list:
            idx = self.event_list.index(event)
            self.counter_list[idx] += 1
        else:
            event_split = event.split("\t")
            self.location_list.append(event_split[0])
            self.sample_list.append(event_split[1])
            self.type_list.append(event_split[2])
            self.counter_list.append(1)
            self.event_list.append(event)

    def test(self):
        if len(self.location_list) != len(self.sample_list) or len(self.location_list) != len(self.type_list) or len(self.sample_list) != len(self.type_list) or len(self.event_list) != len(self.counter_list) and self.registration == False:
            self.registration_fail = True

    def count_event(self, event):
        if event in self.event_list:
            idx = self.event_list.index(event)
            count = self.counter_list[idx] 
            return(count)
        else:
            return(0)
    
    def delete(self, event):
        if event in self.event_list:
            idx = self.event_list.index(event)
            mock = [att_list.pop(idx) for att_list in [self.location_list, self.sample_list, self.type_list, self.counter_list, self.event_list]]

    def write_event_file(self, event_file):
        with open(event_file, "w") as f:
            str_counters = [str(count) for count in self.counter_list]
            full_events = ["\t".join(full) for full in zip(self.event_list, str_counters)]
            f.write("\n".join(full_events))

def event_number_control(limit):
    events_list = events.listing()
    events_counts = [events.count_event(e) for e in events_list]
    events_list = list(zip(events_list, events_counts))
    too_high = [ ]
    for event, count in events_list:
        location = event.split("\t")[0]
        sample = event.split("\t")[1]
        event_type = event.split("\t")[2]
        event_number_fail = format_event(location=location, sample=sample, event_type="high_event_number")
        if event_type == "analysis_not_ended" and (count % (limit*10) == 0):
            comment = f"WARNING: there was {count} registration for the 'analysis_not_ended' event for {sample} at location {location}, which may mean that the analysis is stuck."
            send_mail(target="event register", launcherflag="event number control", comment=comment, error=True)
            too_high.append(event)
            logging.debug(f"Articially adding 1 count for event: {event_type} for {sample} at location {location} to avoid mail spam if stuck at modulo {limit} counts.")
            events.add(event)
        if (count % limit == 0) and event_type not in ["archive_success", "analysis_launched", "infofile_success", "dispatch_ok", "analysis_ended", "analysis_ok", "analysis_not_ended"]:
            comment = f"WARNING : there was {count} registrations for the {event_type} event for {sample} at location {location}, which may mean that the autolauncher is stuck and unable to launch the corresponding sample analysis. Please check autolauncher logs."
            send_mail(target="event register control", launcherflag="event number control", comment=comment, error=True)    
            too_high.append(event)
            logging.debug(f"Articially adding 1 count for event: {event_type} for {sample} at location {location} to avoid mail spam if stuck at modulo {limit} counts.")
            events.add(event)
    return(too_high)

def event_creator(event_file, backup_limit = 10):
    counter = 1
    events = events_register(event_file)
    event_fail_file = os.path.join(os.path.dirname(event_file), "event_creator.failed")
    while events.loaded == False and (counter <= backup_limit):
        event_bak = f"{event_file}.{counter}.bak"
        counter += 1
        if not os.path.isfile(event_bak):
            open(event_bak, "w").close()
        events = events_register(event_bak)
    if events.loaded == True and counter == 1:
        logging.info(f"events registration successfully set up using {event_file}")
        if os.path.isfile(event_fail_file):
            os.remove(event_fail_file)
    elif events.loaded == True and counter != 1:
        comment = f"event registration successfully set up, but using backup event file {event_bak} instead of {event_file}. Please check to see what is wrong."
        logging.error(comment)
        send_mail(target="autolauncher", launcherflag="event_creator", comment=comment, error=True)
        if os.path.isfile(event_fail_file):
            os.remove(event_fail_file)
    else:
        comment = (f"events registration attempts using event file {event_file} failed ({backup_limit} backup alternatives used).")
        logging.error(comment)
        if not os.path.isfile(event_fail_file):
            open(event_fail_file, "w").close()
            send_mail(target="autolauncher", launcherflag="event_creator", comment=comment, error=True)
        logging.info("AUTOLAUNCHER CYCLE END")
        sys.exit(1)
    return(events)


events = event_creator(event_file=eventFile)



##### --concat (check neomics/seq1/)
if args.concat is not None:
    logging.info(f"--concat option specified, attempting concatenation process from flowcell folders in {in_dir} to {concat_out_dir}.")
    step_registered = "autolauncher_concat"
if args.concat is not None and unlocked_to_locked(in_dir):
    # check concat file
    concat_file = os.path.join(in_dir, "concat.list")
    no_concat_event = format_event(location=in_dir, sample=concat_file, event_type="concat_file_missing")
    if not file_exist(concat_file):
        logging.error(f"no {concat_file} found. This file is required. Exiting.")
        happened = event_count_then_add(no_concat_event)
        if happened == 0:
            send_mail("concat_file", "concatenation", comment="concatenation file not found.", error=True)
        sys.exit(1)
    else:
        events.delete(no_concat_event)
    # if folder begins by "2" it is likely to be a flowcell folder
    flowcells = [folder for folder in glob.glob(in_dir + "/2*") if os.path.isdir(folder) and not folder.endswith("logs")]
    for flowcell_path in flowcells:
        flowcell_name = os.path.basename(flowcell_path)
        logging.info(f"Flowcell {flowcell_name} found")
        if string_in_file(flowcell_name, concat_file):
            logging.info(f"Flowcell {flowcell_name} already in concatened files list : stopping concat process.")
        else:
            run_list_path = [folder for folder in glob.glob(flowcell_path + "/Analysis/*") if os.path.isdir(folder)]
            # check if several run folders in subfolder "Analysis"
            ambiguity_event = format_event(location=in_dir, sample=flowcell_name, event_type="concat_ambiguity")
            if len(run_list_path) > 1:
                happened = event_count_then_add(ambiguity_event)
                logging.error(f"Several run data was found in {flowcell_path}/Analysis")
                logging.error(f"Awaiting further desambiguation from user. Stopping concat process for {flowcell_name}")
                if happened == 0:
                    send_mail(flowcell_name, "concatenation", comment="Need for desambiguation - several runs present in Analysis folder.", error=True)
            # launch if ok
            elif len(run_list_path) == 1:
                events.delete(ambiguity_event)
                completion_file = os.path.join(run_list_path[0], "CopyComplete.txt")
                # TODO : factorize code for subprocess launch for each step...
                if file_exist(completion_file, comment= "Attempting to launch concatenation."):
                    current_run_path = os.path.join(run_list_path[0], "Data", "BCLConvert", "fastq")
                    check_output_dir(concat_out_dir)
                    check_output_dir(os.path.join(concat_out_dir, "logs"))
                    check_output_dir(os.path.join(concat_out_dir, "logs", "concat"))
                    concat_log_file = os.path.join(concat_out_dir, "logs" , "concat", f"{flowcell_name}.concat.{current_date}.log")
                    concat_script_path = os.path.join(pipelinebase, "common/fastq/wrapper_concat_fastq.sh")
                    option_dict = {"INPUTDIR" : current_run_path, "OUTPUTDIR" : concat_out_dir, "CLUSTER" : "slurm", "LOGFILE" : concat_log_file, "CONFIGFILE" : configfile}
                    basic_args = ["bash", concat_script_path]
                    subprocess_fail_event = format_event(location=in_dir, sample=flowcell_name, event_type="concat_subprocess_fail")
                    cmd_log = "\"{}\" with exported arguments: {}".format(" ".join(basic_args), ",".join([f"{k}={v}" for k, v in option_dict.items()]))
                    logging.info(f"Command: {cmd_log}")
                    sub = subprocess.run(basic_args, env={**option_dict, **os.environ}, capture_output=True, text=True, encoding="UTF-8")
                    if sub.returncode != 0:
                        comment=f"concatenation step returned an error with exit code : {sub.returncode}"
                        logging.error(comment)
                        if sub.stdout != '' or sub.stderr != '':
                            logging.error(f"error message:{sub.stdout} {sub.stderr}")
                        happened = event_count_then_add(subprocess_fail_event)
                        if happened == 0:
                            send_mail(target=flowcell_name, launcherflag="concat", comment=comment, error=True)
                        sys.exit(1)
                    else:
                        if sub.stdout != '':
                            logging.debug(f"cmd output: {sub.stdout}")
                        events.delete(subprocess_fail_event)
                        with open(concat_file, "a") as f:
                            f.write(flowcell_name + "\n")
                        logging.info(f"concatenation process successfully launched for {flowcell_name} and name added to concat.list")
                        send_mail(flowcell_name, "concatenation", comment="has been successfully launched.")
                else:
                    logging.warning(f"sequencing process not completed for {flowcell_name} (no CopyComplete.txt). Waiting for the next autolauncher round.")



##### --organize (check /work/work/shared/s-neomics/data/incoming)
if args.organize is not None:
    logging.info(f"--organize option specified, attempting organize sample folder process from {in_dir} files.")
    step_registered = "autolauncher_organize"
if args.organize is not None and unlocked_to_locked(in_dir):
    fastq_list = [ ] 
    files = os.listdir(in_dir)
    for f in files:
        if f.endswith(".fastq.gz"):
            fastq_list.append(f)
    if len(fastq_list) == 0:
        logging.info("No fastq file found.")
        sys.exit(0)
    logging.info(f"Found {len(fastq_list)} files in {in_dir}")
    fastq_list = sorted(list(set(fastq_list)))
    badBatch = [ ]
    # TODO : factorize (create class with search R1, R2, R1end, R2end and a validation methods instead) ?
    for s in fastq_list:
        goThrough = True
        if s in badBatch:
            continue
        sample_name = s.split(".")[0]
        if s.find("R1") != -1:
            s2 = s.replace("R1", "R2")
            if s2 not in files:
                logging.warning(f"File {s} is a R1 on disk, but no R2 {s2} was found.")
                goThrough = False
            else:
                logging.info(f"File {s} is a R1 on disk, and a R2 {s2} was found.")
                goThrough = True
        elif s.find("R2") != -1:
            s2 = s.replace("R2", "R1")
            if s2 not in files:
                logging.warning(f"File {s} is a R2 on disk, but no R1 {s2} was found.")
                goThrough = False
            else:
                logging.info(f"File {s} is a R2 on disk, and a R1 {s2} was found.")
                goThrough = True
        
        if not goThrough and s not in badBatch:
            happened = event_count_then_add(format_event(location=in_dir, sample=s, event_type="paired_not_found"))
            logging.warning(f"## paired file not found for {s}. Stopping further processing regarding sample {sample_name}.")
            mock = [badBatch.append(file) for file in [s, s2]]
            continue
        elif s not in badBatch:
            if not file_exist(in_dir + "/" + s + ".end", log=False):
                logging.warning(f"## concatenation not ended for at least one fastq file for sample {sample_name}. Stopping further processing for files {s} and {s2}")
                mock = [badBatch.append(file) for file in [s, s2]]
            # check size
            else: 
                too_small_event = format_event(location=in_dir, sample=s, event_type="fastq_too_small")
                stats = os.stat(in_dir + "/" + s)
                if stats.st_size < 10**7 and s not in badBatch:
                    happened = event_count_then_add(too_small_event)
                    comment = f"## The size of the file: {s} is inferior to 10 Mb. Stopping further processing for files {s},{s2}."
                    logging.error(comment)
                    if happened == 0:
                        send_mail(sample_name, "organize_sample", comment="final fastq file too small. " + s + " and " + s2 + " files processing stopped. ", error=True)
                    mock = [badBatch.append(sample) for sample in [s, s2]]
                else:
                    events.delete(too_small_event)
    
    badBatch = sorted(list(set(badBatch)))
    sample_files = [ file for file in fastq_list if file not in badBatch ]
    sample_list = sorted(list(set([ s.split(".")[0] for s in sample_files ])))
    if len(sample_list) == 0:
        comment="Fastq files on hold for organization step: {} (concatenation not over, missing pair or final file too small).".format(",".join(badBatch))
        logging.info(comment)
        sys.exit(0)
    logging.info(f"{in_dir} file search recap: ")
    badBatch_names = sorted(list(set([s.split(".")[0] for s in badBatch])))
    if len(badBatch_names) != 0:
        logging.info("Incomplete samples or samples in error: {}".format(",".join(badBatch_names)))
    logging.info("Complete samples whose familial structure will be examined: {}".format(",".join(sample_list)))
    
    # check that familial structure is complete
    data = {}
    server_context = labkey.utils.create_server_context(domain=args.labkeyserver, container_path="home/GAD/Génétique moléculaire", context_path="labkey")
    logging.info("Querying Suivi exomes dataset ... ")

    try:
        all_exome = labkey.query.select_rows(server_context, schema_name = "study", query_name = "Suivi exomes", timeout=120)
    except labkey.exceptions.ServerContextError as error_text:
        comment = f"labkey server interrogation failed."
        logging.exception(f"{comment} ({error_text})")
        send_mail(target="labkey", launcherflag="organize", comment=comment, error=True)
        sys.exit(1)
    else:
        logging.info("done.")

    all_exome = all_exome["rows"]
    without_fam_dict = { }
    # search for family members missing from concatenated files
    bad_samples = [ ] 
    for current_sample in sample_list:
        logging.debug(f"querying labkey status and searching for family members for sample: {current_sample}")
        missing_samples = [ ] 
        ped_id = [ line["PatientID"] for line in all_exome if line["dijexID"] == current_sample ]
        no_ped_event = format_event(location=in_dir, sample=current_sample, event_type="no_ped_id")
        no_dijex_event = format_event(location=in_dir, sample=current_sample, event_type="missing_dijex_id")
        # check PED id
        if len(ped_id) == 0:
            happened = event_count_then_add(no_ped_event)
            error_comment = f"no PED ID found for sample {current_sample}. Please verify that labkey entry is properly informed."
            logging.error(error_comment)
            bad_samples.append(current_sample)
            if happened == 0:
                send_mail(current_sample, "organize_sample", comment=error_comment, error=True)
            continue
        else:
            events.delete(no_ped_event)
        strict_ped = "".join(ped_id)
        logging.debug(f"{current_sample} - sample complete PED ID is: {strict_ped}")
        ped_id = [ PED.split(".")[0] for PED in ped_id ]
        ped_id = "".join(ped_id)
        # check dijex id
        dijex_ids = [line["dijexID"] for line in all_exome]
        analyzed = [line["dijexID"] for line in all_exome if line["date_analyse"]]
        bad_status = [line["dijexID"] for line in all_exome if (str(line["statut"]) in ["Annulé", "Echec CQ", "Echec séquençage"])]
        if current_sample not in dijex_ids:
            happened = event_count_then_add(no_dijex_event)
            error_comment = f"{current_sample}: sample dismissed because not found in labkey dijexIDs. Please verify that dijexID is properly informed in labkey for this sample."
            bad_samples.append(current_sample)
            logging.warning(error_comment)
            if happened == 0:
                send_mail(targetcurrent_sample, launcherflag="organize", comment=error_comment, error=True)
            continue
        else:
            events.delete(no_dijex_event)
        # check labkey status
        if current_sample in analyzed:
            happened = event_count_then_add(format_event(location=in_dir, sample=current_sample, event_type="already_analyzed"))
            comment = f"Sample {current_sample} was already analyzed (analysis date already informed in labkey)"
            logging.warning(comment)
            if happened == 0:
                send_mail(target=current_sample, launcherflag="organize", comment=comment, keyword="already_analyzed" )
        if current_sample in bad_status:
            happened = event_count_then_add(format_event(location=in_dir, sample=current_sample, event_type="labkey_status_bad"))
            error_comment = f"Sample {current_sample} was dismissed due to status in labkey (canceled or bad QC). Sample dismissed."
            logging.warning(error_comment)
            bad_samples.append(current_sample)
            if happened == 0:
                send_mail(target=current_sample, launcherflag="organize", comment=error_comment, error=True)
            continue
        # retrieve other family members
        for line in all_exome:
            line_dijex = line["dijexID"]
            line_ped = line["PatientID"].split(".")[0]
            if line_dijex == None or line_dijex == "Non renseigné" or  line_dijex == "None":
                continue
            # since we also want to avoid waiting for another iteration of the same sample : (verify strict_ped variable defintion):
            if (line["PatientID"] == strict_ped) and (line_dijex != current_sample):
                logging.info(f"{current_sample} - A sample from the same family was found: {line_dijex}, but it is another sample from the same patient ({strict_ped}), so it will not be waited for.")
            elif line_ped == ped_id and (line_dijex not in sample_list) and (line["PatientID"] != strict_ped):
                missing_samples.append(line_dijex)
                if (str(line["statut"]) in ["Annulé", "Echec CQ", "Echec séquençage"]):
                    logging.warning(f"{current_sample} - A sample from another family member: {line_dijex} was found but it will be dismissed because of bad status (canceled or bad QC)")
                    bad_samples.append(line_dijex)

        # see if there are samples with bad QC that do not need to be accounted for:
        missing_but_bad = [sample for sample in missing_samples if sample in bad_samples]
        if len(missing_but_bad) > 0:
            happened = event_count_then_add(format_event(location=in_dir, sample=current_sample, event_type="dismissed_family_members"))
            error_comment = "{} - found samples from the same family to be waited before launching organize data folder: {}. The sample(s) {} was(were) dismissed because of labkey status (bad QC) and will not be waited for.".format(current_sample, ",".join(missing_samples), ",".join(missing_but_bad))
            if happened == 0:
                send_mail(target=current_sample, launcherflag="organize", comment=error_comment, error=True)
            logging.debug("{} - removing bad qc samples {} from the missing samples list".format(current_sample, ",".join(missing_but_bad)))
            mock = [missing_samples.pop(missing_samples.index(sample)) for sample in missing_but_bad]
        if len(missing_samples) > 0:
            happened = event_count_then_add(format_event(location=in_dir, sample=current_sample, event_type="family_missing"))
            logging.warning("{} - found samples from the same family to be waited before launching organize data folder : {}".format(current_sample,",".join(missing_samples)))
            if ped_id not in without_fam_dict.keys():
                without_fam_dict[ped_id] = [current_sample]
            else:
                without_fam_dict[ped_id].append(current_sample)
        else:
            logging.info(f"no more other samples to wait concerning {current_sample}. Organization of data folder can be done.")
    
    # inform samples that will not be treated (missing family members, or status in labkey)
    logging.info("global labkey search recap:")
    if len(bad_samples) != 0:
        logging.info("sample(s) {} will not be waited for nor organized due to their status in labkey (bad QC, canceled).".format(",".join(bad_samples)))
    comments = [str("family {} = samples {} not organized now - on hold for other family members.".format(key, ",".join(value))) for key, value in without_fam_dict.items()]
    for sentence in comments:
        logging.warning(sentence)
    # proceed with samples fulfilling all conditions
    without_fam = [value for key, value in without_fam_dict.items()]
    without_fam = list(itertools.chain(*without_fam))
    sample_list = [ sample for sample in sample_list if (sample not in bad_samples) and (sample not in without_fam) ]
    if len(sample_list) > 0:
        logging.info("sample(s) that will be organized: {}".format(",".join(sample_list)))
        organize_file = os.path.join(in_dir, "samples_to_organize.list")
        with open(organize_file, "w") as f:
            f.write("\n".join(sample_list))
            f.write("\n")
        logging.debug(f"created {organize_file} containing list of samples to be organized")
        organize_out_dir = os.path.join(in_dir, "organize")
        check_output_dir(organize_out_dir)
        check_output_dir(os.path.join(organize_out_dir, "logs"))
        organize_log_file = os.path.join(organize_out_dir, "logs", f"organize_data_folder.{current_date}.log")
        organize_script = os.path.join(pipelinebase, "common/fastq/organize_data_folder.py")
        options_dict = {"-d" : in_dir, "-b" : labkey_adress, "-p" : pipelinebase, "-e" : organize_log_file, "-s" : organize_file, "-t" : targetlist , "-c" : False, "-u" : organize_out_dir}
        cmd =  "python3 {} {}".format(organize_script, " ".join([f"{k} {v}" for k,v in options_dict.items()])) 
        logging.info(f"Command: {cmd}")
        subprocess_fail_event = format_event(location=in_dir, sample="organize-subprocess", event_type="organize_subprocess_fail")
        sub = subprocess.run(cmd.split(" "), capture_output=True, text=True, encoding="UTF-8")
        if sub.returncode != 0:
            happened = event_count_then_add(subprocess_fail_event)
            comment=f"organize data folder step returned an error with exit code : {sub.returncode}"
            logging.error(comment)
            if sub.stdout != '' or sub.stderr != '':
                logging.error(f"error message:{sub.stderr} {sub.stdout}")
            if happened == 0:
                send_mail(target="novaseq-samples", launcherflag="organize", comment=comment, error=True)
            sys.exit(1)
        else:
            if sub.stdout != '':
                logging.info(f"command output: {sub.stdout}")
            events.delete(subprocess_fail_event)
            comment = "organize data folders executed correctly for {} in {}".format(",".join(sample_list), organize_out_dir)
            logging.info(comment)
            send_mail("novaseq-samples", "organize", comment=comment, keyword="OK")
    else:
        logging.info("No valid samples for organization step.")
        sys.exit(0)




##### --infofile (check /work/work/shared/s-neomics/data/incoming/organize)
if args.infofile is not None:
    step_registered = "autolauncher_infofile"
    logging.info(f"--infofile option specified, attempting to update sample correspondance file in {in_dir}.")
    if unlocked_to_locked(in_dir):
        sample_paths = [ sample for sample in glob.glob(in_dir + "/*") if os.path.isdir(sample) and not sample.endswith("logs") ]
        sample_list = [ os.path.basename(sample) for sample in sample_paths ]
        if len(sample_list) > 0:
            output_file = os.path.join(in_dir, "sample_correspondance.info")
            logging.info("samples detected: {}. Attempting to update {}".format(",".join(sample_list), output_file))
            check_output_dir(os.path.join(in_dir, "logs"))
            infofile_log_file = os.path.join(in_dir, "logs", f"create_sample_information_file.{current_date}.log")
            infofile_script = os.path.join(pipelinebase, "common","fastq", "wrapper_create_sample_information_file.sh")
            sample_list_file = os.path.join(in_dir, "samples_to_infofile.list")
            with open(sample_list_file, "w") as f:
                f.write("\n".join(sample_list))
            logging.debug(f"created sample list file: {sample_list_file}")
            option_dict = {"INPUTFILE" : sample_list_file, "OUTPUTFILE" : output_file, "LOGFILE" : infofile_log_file, "CONFIGFILE" : configfile, "INPUTDIR" : in_dir}
            basic_args = ["bash", infofile_script]
            subprocess_fail_event = format_event(location=in_dir, sample="infofile_subprocess",event_type="infofile_subprocess_fail")
            cmd_log = "\"{}\" with exported arguments: {}".format(" ".join(basic_args), ",".join([f"{k}={v}" for k, v in option_dict.items()]))
            logging.info(f"Command: {cmd_log}")
            sub = subprocess.run(basic_args, env={**option_dict, **os.environ}, capture_output=True, text=True, encoding="UTF-8")
            if sub.returncode != 0:
                comment = f"sample information file creation step returned an error with exit code : {sub.returncode}"
                logging.error(f"{comment}")
                if sub.stdout != '' or sub.stderr != '':
                    logging.error(f"error message:{sub.stdout} {sub.stderr}")
                happened = event_count_then_add(subprocess_fail_event)
                if happened == 0:
                    send_mail("novaseq-samples", "sample_info", comment=comment, error=True)
                sys.exit(1)
            else:
                if sub.stdout != '':
                    logging.info(f"command output: {sub.stdout}")
                events.delete(subprocess_fail_event)
                comment = "sample information file step successfully launched for: {} samples in {}".format(",".join(sample_list), in_dir)
                logging.info(comment)
                infofile_sucess = format_event(location=in_dir, sample=",".join(sample_list), event_type="infofile_sucess")
                happened = event_count_then_add(infofile_sucess)
                if happened == 0:
                    send_mail("novaseq-sample", "infofile", comment=comment, keyword="OK")
        else:
            logging.info("No pending samples directories found. Waiting for next autolauncher round.")

##### --analyse (check /work/work/shared/s-neomics/data/incoming/organize)
if args.analysis is not None:
    step_registered = "autolauncher_analysis"
    logging.info(f"--analysis option specified, attempting to launch analysis if any sample(s) is ready in {in_dir}.")
    if unlocked_to_locked(in_dir):
        correspondance_file = in_dir + "/sample_correspondance.info"
        with open(correspondance_file, "r") as f:
            sample_list = [line.split("\t")[0] for line in f if not line.startswith("SAMPLE_NAME")]
        no_corresp_event = format_event(location = in_dir, sample="spl_correspondance_file", event_type="spl_corresp_file_missing")
        if not file_exist(correspondance_file, log=False):
            logging.error(f"no {correspondance_file} found. This file is required to launch analysis. Exiting.")
            happened = event_count_then_add(no_corresp_event)
            if happened == 0:
                send_mail(target="sample correspondance file", launcherflag="analysis", comment="sample correspondance file not found.", error=True)
            sys.exit(1)
        elif len(sample_list) != 0:
            logging.info("Samples registered in the correspondance file: {}. Launching analysis.".format(",".join(sample_list)))
            events.delete(no_corresp_event)
            check_output_dir(os.path.join(in_dir, "logs"))
            analysis_log_file = os.path.join(in_dir, "logs", f"dispatch_sample.{current_time}.log")
            analysis_script = os.path.join(pipelinebase, "common", "fastq", "dispatch_sample_and_mv.py")
            cmd = f"python3 {analysis_script} -i {correspondance_file} -d {in_dir} -n gpu -q neomics -r gpu -b {labkey_adress} -s slurm -t {analysis_out_dir} -e {analysis_log_file}"
            logging.info(f"Command: {cmd}")
            subprocess_fail_event = format_event(location=in_dir, sample="analysis_subprocess", event_type="analysis_launch_fail")
            sub = subprocess.run(cmd.split(" "), capture_output=True, text=True, encoding="UTF-8")
            if sub.returncode != 0:
                comment = "dispatch and launch analysis step returned an error with exit code : {} for repertoried samples {}".format(sub.returncode, ",".join(sample_list))
                logging.error(f"{comment}")
                if sub.stdout != '' or sub.stderr != '':
                    logging.error(f"error message:{sub.stderr} {sub.stdout}")
                happened = event_count_then_add(subprocess_fail_event)
                if happened == 0:
                    send_mail("novaseq-samples", "analysis", comment=comment, error=True)
                sys.exit(1)
            else:
                if sub.stdout != '':
                    logging.info(f"command output: {sub.stdout}")
                events.delete(subprocess_fail_event)
                comment = "analysis program sucessfully launched inside {} directory, with repertoried samples {}. Note : this does not ensure that each of those samples were dispatched, depending on the available resources".format(in_dir, ",".join(sample_list))
                logging.info(comment)
                analysis_launched = format_event(location=in_dir, sample=",".join(sample_list), event_type="analysis_launched")
                happened = event_count_then_add(analysis_launched)
                if happened == 0:
                    send_mail("novaseq-samples", "analysis", comment=comment, keyword="OK")
                # add an event per sample to control for samples stuck in organize and never launched
                for sample in sample_list:
                    found_event = format_event(location=in_dir, sample=sample, event_type="found_in_organize")
                    events.add(found_event)
        else:
            logging.info("no samples registered in the correspondance file. Waiting for next autolauncher cycle.")




# --check step in data/analyse
if args.check is not None:
    logging.info(f"--check option specified, verifying analysis folders in {in_dir}.")
    step_registered = "autolauncher_check"
if args.check is not None and unlocked_to_locked(in_dir):
    analysisdir_list = glob.glob(os.path.join(in_dir, "PED*")) + glob.glob(os.path.join(in_dir, "dij*"))
    analysisdir_list = [dir for dir in analysisdir_list if os.path.isdir(dir)]
    for dir in analysisdir_list:
        family = os.path.basename(dir)
        family_dir = dir
        logging.info(f"# Found analysis directory: {family_dir} ")
        
        # checking samples for which analysis was launched event "dispatch ok"
        dispatched = glob.glob(os.path.join(family_dir, "dij*"))
        dispatched = [os.path.basename(sampledir) for sampledir in dispatched if os.path.isdir(sampledir)]
        if len(dispatched) != 0:
            comment = "{}: dispatch - {} sample(s) were successfully dispatched in {}".format(family, ",".join(dispatched), family_dir)
            logging.info(comment)
            dispatch_event = format_event(location=family_dir, sample=",".join(dispatched), event_type="dispatch_ok")
            happened = event_count_then_add(dispatch_event)
            if happened == 0:
                send_mail(",".join(dispatched), "dispatch_check", comment=comment, keyword="OK")
            undispatched = False
        else:
            comment = f"{family}: dispatch - no sample found in {family_dir} directory ! check if dispatch is in progress."
            logging.error(comment)
            no_dispatch = format_event(location=family_dir, sample=family, event_type="no_dispatch")
            happened = event_count_then_add(no_dispatch)
            if happened == 0:
                send_mail(target=family, launcherflag="dispatch_check", comment=comment, error=True)
            undispatched = True
        
        # checking if analysis ended (status.tsv + parsing for exit codes)
        status_file = os.path.join(family_dir, "status.tsv")
        if os.path.isfile(status_file) and not undispatched:
            logging.info("{}: analysis - ended for {} (status.tsv found in {})".format(family, ",".join(dispatched), family_dir))
            format_event(location=family_dir, sample=family, event_type="analysis_ended")
            # parse status file
            with open(status_file, "r") as f:
                status = re.split("\n+", f.read())
            fail_stat = re.compile(r"^.*FAIL\t?")
            failed_list = list(filter(fail_stat.search, status))
            if len(failed_list) > 0:
                analysis_fail = format_event(location=family_dir, sample=family, event_type="analysis_failed")
                comment_list = []
                for failed in failed_list:
                    process = failed.split("\t")[0]
                    comment = f"{family} : analysis - process {process} has failed."
                    logging.warning(comment)
                    comment_list.append(comment)
                happened = event_count_then_add(analysis_fail)
                main_comment = "Analysis has failed for {} ({})".format(family, ",".join(dispatched))
                main_comment = "{}\n{}".format(main_comment, "\n".join(comment_list))
                if happened == 0:
                    send_mail(target=family, launcherflag="analysis", comment=main_comment, error=True)
            else:
                analysis_ok = format_event(location=family_dir, sample=family, event_type="analysis_ok")
                happened = event_count_then_add(analysis_ok)
                if happened == 0:
                    comment = "{}: analysis - OK ({})".format(family, ",".join(dispatched))
                    logging.info(comment)
                    send_mail(target=family, launcherflag="analysis_check", comment=comment, keyword="OK")
        elif not undispatched:
            logging.info(f"{family}: analysis - not ended yet")
            analysis_not_ended = format_event(location=family_dir, sample=family, event_type="analysis_not_ended")
            events.add(analysis_not_ended)
                
        # archiving check
        archivelog = os.path.join(family_dir, "archive.log")
        if os.path.isfile(archivelog) and not undispatched:
            with open(archivelog, "r") as f:
                log_content = f.read()
            end_stop = re.search(r"[Ss]topping execution$|exit code : [^0]", log_content)
            end_success = re.search(r"[Ee]xecution with success|exit code : 0", log_content)
            if end_success:
                archive_success_event = format_event(location=family_dir, sample=family, event_type="archive_success")
                happened = event_count_then_add(archive_success_event)
                comment = f"{family}: archive - Archiving done."
                logging.info(comment)
                if happened == 0:
                    send_mail(target=family, launcherflag="archiving_check", comment=comment, keyword="OK")
                # add 1 "archive_sucess" event for each sample for easier eventlog cleaning
                for sample in dispatched:
                    sample_event = format_event(location=family_dir, sample=sample, event_type="archive_success")
                    events.add(sample_event)
            elif end_stop:
                archive_fail_event = format_event(location=family_dir, sample=family, event_type="archive_fail")
                happened = event_count_then_add(archive_fail_event)
                comment = f"{family}: archive - Archiving stopped prematurely. Please check logs."
                logging.error(f"{comment}")
                if happened == 0:
                    send_mail(target=family, launcherflag="archiving_check", comment=comment, error=True)
            else :
                archive_in_progress_event = format_event(location=family_dir, sample=family, event_type="archive_in_progress")
                happened = event_count_then_add(archive_in_progress_event)
                comment = f"{family}: archive - Archiving in progress."
                logging.info(f"{comment}")
        elif not undispatched:
            no_archive_event = format_event(location=family_dir, sample=family, event_type="no_archive_log")
            happened = event_count_then_add(no_archive_event)
            comment = f"{family}: archive - no {archivelog} file found in {family_dir}."
            logging.info(f"{comment}")
    if len(analysisdir_list) == 0:
        logging.info(f"No analysis directory found in {in_dir}. Waiting for next autolauncher cycle")
    
    # control the number of events
    event_check = event_number_control(50)
    if len(event_check) > 0 :
        for event in event_check:
            event = event.split("\t")
            logging.warning(f"A mail alert will be sent for an abnormal number of events \"{event[2]}\" registered for {event[1]} at location {event[0]}")

sys.exit(0)

