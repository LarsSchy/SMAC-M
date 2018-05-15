#!/usr/bin/python2

import os
import argparse
import subprocess
import shutil
import time

def parse_arguments():
    parser = argparse.ArgumentParser(prog="cache_monitor.py", description="This program monitors a  directory and clears it if the size is above a certain limit")
    parser.add_argument("path", nargs=1, help="The cache directory to watch");
    parser.add_argument("-t", "--time-in-seconds", nargs=1, help="The interval time, in seconds, with which to watch the folder", required=True)
    parser.add_argument("-l", "--limit", help="Set the limit for the folder size in kilobytes (1GB = \"1,000,000\"), if the watched folder is larger than this limit, it will be removed", required=True)
    return parser.parse_args();

def watch_folder(limit_string):
    # Get folders with sizes at current directory
    # The 'du' command does not tolerate an empty directory, thus checking the len(listdir) before continuing
    if len(os.listdir('.')) > 0:
        disk_usage = subprocess.check_output("du -s *", shell=True).splitlines()
        limit = int(limit_string.replace(',', ''))

        # Loop over all folders and folder sizes
        for entry in disk_usage:
            size, folder =  entry.split('\t')
            if(int(size) > limit):
                print("Clearing cache at " + os.path.join(os.getcwd(), folder))

                try:
                    shutil.rmtree(folder)
                except OSError:
                    pass

def main():
    args = parse_arguments()
    watch_dir = args.path[0]

    if not os.path.exists(watch_dir):
        os.makedirs(watch_dir)

    os.chdir(args.path[0])

    while(True):
        watch_folder(args.limit)
        time.sleep(float(args.time_in_seconds[0]))

if __name__ == "__main__":
    main()
