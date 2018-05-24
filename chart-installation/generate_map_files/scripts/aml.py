#!/usr/bin/python2

import os
import sys
script_dir = os.path.normpath(sys.path[0])
sys.path.append(os.path.abspath(os.path.join(script_dir, "../../utils/")))
import dirutils
import re
from subprocess import call, check_output
from string import Template

# Regular expression to extract a double with decimals from a string
find_double_regexp = '\d+\.*\d*'


def calculate_total_extent(data_path, s57_definitions_path):
    total_extent = [sys.maxsize, sys.maxsize, -
                    sys.maxsize - 1, -sys.maxsize - 1]
    for f in dirutils.get_all_files_with_suffix(data_path, [".000"]):
        bashCmd = ' '.join(["ogrinfo", "-ro", f, "--config S57_PROFILE aml",
                            "--config S57_CSV", s57_definitions_path, "M_COVR", "-summary", "| grep Extent"])
        a = check_output(bashCmd, shell=True)
        for extentline in a.splitlines():
            extent = list(map(float, re.findall(
                find_double_regexp, extentline)))
            if extent[0] < total_extent[0]:
                total_extent[0] = extent[0]
            if extent[1] < total_extent[1]:
                total_extent[1] = extent[1]
            if extent[2] > total_extent[2]:
                total_extent[2] = extent[2]
            if extent[3] > total_extent[3]:
                total_extent[3] = extent[3]
    return total_extent


def generate_includes(includes_dir, theme):
    # The layers that implements surfaces has to be sorted last,
    # otherwise they might obstruct other features.
    CLB = []
    MFF = []
    all_layers = []

    # Get all includefiles with the correct theme
    for inc in os.listdir(includes_dir):
        if inc.startswith(theme):
            file_name = inc.replace(theme + "_", "")
            if file_name[2] == 'C':
                CLB.append(inc)
            elif file_name[2] == 'M':
                MFF.append(inc)
            else:
                all_layers.append(inc)
    # Append order dependent layers at the end
    all_layers.extend(MFF)
    all_layers.extend(CLB)

    rel_includes_path = os.path.basename(includes_dir)

    # Update the list, adding mapserver keyword and relative path to the include files
    for i, item in enumerate(all_layers):
        all_layers[i] = str.format(
            "INCLUDE \"{}/{}\"", rel_includes_path, item)
    return "\n    ".join(all_layers)


def get_dictionary(data_path, theme, s57_definitions_path, map_path, fonts_path, aml_type, debug_string):
    return {'THEME': theme,
            'HOST': 'http://mapserver/cgi-bin/mapserv.fcgi',
            'AML_CSV_RUNTIME': s57_definitions_path,
            'EXTENT': ' '.join(map(str, calculate_total_extent(data_path, s57_definitions_path))),
            'DEBUG': debug_string,
            'MAP_PATH': map_path,
            'FONTS_PATH': fonts_path,
            'AML_TYPE': aml_type,
            'INCLUDES': generate_includes(os.path.join(map_path, "includes"), theme)}


debug_template = '''CONFIG "MS_ERRORFILE" "/tmp/AML_{0}.log"
    DEBUG 5
    CONFIG "ON_MISSING_DATA" "LOG"'''


def create_capability_files(data_path, template_path, themes_path, s57_definitions_path, map_path, fonts_path, aml_type, use_debug):
    template = Template(
        open(os.path.join(template_path, "AML_THEME.map"), 'r').read())
    for theme in os.listdir(themes_path):
        # Remove file suffix
        theme = os.path.splitext(theme)[0]

        debug_string = ""
        if use_debug:
            debug_string = str.format(debug_template, theme)

        d = get_dictionary(data_path, theme, s57_definitions_path,
                           map_path, fonts_path, aml_type, debug_string)

        fileout = open(os.path.join(map_path, "AML_" + theme + ".map"), 'w')
        fileout.write(template.substitute(d))


def generate_aml_config(data_path, map_path, rule_set_path, resource_path, force_overwrite, debug):

    # Generate new map files
    dirutils.clear_folder(map_path)
    if debug:
        debug_string = "yes"
    else:
        debug_string = "no"
    color_tables_dir = os.path.join(rule_set_path, "color_tables")

    aml_type = ""
    for f in dirutils.get_all_files_with_suffix(data_path, [".000"]):
        for theme in os.listdir(color_tables_dir):
            bashCmd = ' '.join(["./process_aml_layers.sh", "aml_file=" + f, "rp=" + rule_set_path,
                                "ct=" + os.path.join(color_tables_dir, theme), "mp=" + map_path, "d=" + debug_string])
            output = check_output(bashCmd, shell=True)
            print(output)
            aml_type = output[-4:-1]

    if (aml_type):
        create_capability_files(data_path, os.path.join(resource_path, "templates"), os.path.join(rule_set_path, "color_tables"), os.path.join(
            resource_path, "aml_csv_files"), map_path, os.path.join(resource_path, "fonts", "fontset.lst"), aml_type, debug)

        dirutils.copy_and_replace(os.path.join(
            resource_path, "epsg"), os.path.join(map_path, "epsg"))
        dirutils.copy_and_replace(os.path.join(
            resource_path, "symbols"), os.path.join(map_path, "symbols"))
    else:
        print("There were no AML-files to be processed")
