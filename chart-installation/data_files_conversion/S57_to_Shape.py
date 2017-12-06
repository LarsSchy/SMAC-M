#!/usr/bin/python2 -u

import multiprocessing as mp
import argparse
import time
import datetime
import os
import sys
import process_level
script_dir = os.path.normpath(sys.path[0])
sys.path.append(os.path.abspath(os.path.join(script_dir, "../utils/")))
from subprocess import call
import dirutils

def parse_arguments():
    parser = argparse.ArgumentParser(prog="S57_to_Shape", description="This program converts a S57 source to Shape that is parseable by the map generating scripts")
    parser.add_argument("src_dir", nargs=1, help="Directory of your S57 files")
    parser.add_argument("out_dir", nargs=1, help="Directory of your Shape output")
    parser.add_argument("-progress_addr", default='', help="Where to send progress information")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug for this operation")
    parser.add_argument("-log", choices=['no','tmp','stdout'], default='no', help="Choose if you want 'no' logging, logging to /tmp or logging to standard out")
    return parser.parse_args()

def get_levels_from_source(directory):
    s57_list = []
    for _, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".000") and f[2].isdigit():
#               The level is the third character (index 2) in the file name according to S57 naming standard
                s57_list.append(f[2])
#   Return a list with all layers present in the data set
    return sorted(set(s57_list))

def get_logfile_name():
    now = datetime.datetime.now()
    hms = datetime.time(now.hour, now.minute, now.second)
    return "/tmp/S57_to_shape_" + str(hms) + ".log"

def main():
    args = parse_arguments()

    source_path = os.path.abspath(args.src_dir[0])
    output_path = dirutils.force_sub_dir(os.path.abspath(args.out_dir[0]), "shape")
    dirutils.clear_folder(output_path)

    if not os.path.exists(source_path):
        print "That source folder does not exist"
        sys.exit(1)

    levels = get_levels_from_source(source_path)
    
    debug_val = "no"
    if args.debug:
        debug_val = "yes"
    
    processes = []

    os.chdir(script_dir)
    for level in levels:
        logstuff = []
        if args.log == "tmp":
            logstuff =[">>", get_logfile_name(), "2>&1"]
        elif args.log == "no":
            logstuff = ["> /dev/null 2>&1"]

        processes.append(mp.Process(target=process_level.process,
            args=(level, source_path, output_path, args.progress_addr)))

    #start
    for p in processes:
        p.start()

    #join
    for p in processes:
        p.join()

if __name__ == "__main__":
    start_time = time.time()
    main()
    print "Execution took %s seconds" % (time.time() - start_time)
