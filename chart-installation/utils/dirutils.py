#!/usr/bin/python2

import os
from glob import glob
import shutil

def does_color_tables_exist(path):
    # Try to verify that that rule set direcory exists and is OK
    if (os.path.exists(path + "/color_tables") and
       os.listdir(path + "/color_tables") != []):
            print "Existing color tables found at " + path + "/color_tables"
            return True

    return False

def does_layer_rules_exist(path):
    rules_path = os.path.join(path, "layer_rules")
    # Try to verify that that rule set direcory exists and is OK
    if (os.path.exists(rules_path) and
       os.listdir(rules_path) != []):
            print "Existing layers found in " + rules_path
            return True

    return False

def copy_and_replace(src,dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

def clear_folder(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)

def clear_folder_content(path):
    for l in os.listdir(path):
        full_path = os.path.join(path, l)
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)

def remove_files_from_folder(folder_name, file_suffix):
    for root, dirs, files in os.walk(folder_name):
        for f in files:
            if f.endswith(file_suffix):
                os.remove(os.path.join(root,f))
                print "\t" + f + " was removed!"

# Forces a path to end with '/sub_folder'
def force_sub_dir(folder_name, sub_folder):
    if not os.path.basename(folder_name) == sub_folder:
        folder_name = os.path.normpath(os.path.join(folder_name, sub_folder))
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
    return folder_name

# This returns absolute path to all files with suffix in suffix_array
# It traverses "path" and all sub dirs of "path"
def get_all_files_with_suffix(path, suffix_array):
    files_array = []
    for root, subdir, files in os.walk(path):
        files_array.extend([os.path.join(root,f) for f in files if os.path.splitext(f)[1] in suffix_array])
    # Return array of all files where the file suffix mathes any in suffixe
    return files_array

# Returns files and directories placed in folder "path"
# Does NOT traverse subdirs
def get_dirs_and_files_in(path):
    all_files=[f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
    all_dirs =[d for d in os.listdir(path) if os.path.isdir(os.path.join(path,d))]
    return all_dirs,all_files

