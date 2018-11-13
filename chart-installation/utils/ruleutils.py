#!/usr/bin/python2

import os
import subprocess

try:
    from dirutils import clear_folder, copy_and_replace, force_sub_dir
    from userutils import ask_user
except ImportError:
    from .dirutils import clear_folder, copy_and_replace, force_sub_dir
    from .userutils import ask_user


def index_containing_substring(the_list, substring):
    for i, s in enumerate(the_list):
        if substring in s:
            return i
    return None


def create_color_rules(resource_dir, path, default_color_table):
    print("Overwrite color tables in " + path)
    choices = os.listdir(os.path.join(resource_dir, "chartsymbols"))
    if default_color_table:
        selection = index_containing_substring(choices, default_color_table)
    else:
        selection = ask_user("Select color definition: ", choices)
    print("Using color table " + choices[selection])
    path_to_selection = os.path.join(
        resource_dir, "chartsymbols", choices[selection])
    clear_folder(force_sub_dir(path, "color_tables"))
    bashCmd = ' '.join(["./convert_colors_xml2csv.sh",
                        "input=" + path_to_selection, " target=" + path])
    subprocess.call(bashCmd, shell=True)


def create_layer_rules(resource_dir, config_path):
    print("Overwrite color tables in " + config_path)
    copy_and_replace(os.path.join(resource_dir, "layer_rules"),
                     force_sub_dir(config_path, "layer_rules"))
