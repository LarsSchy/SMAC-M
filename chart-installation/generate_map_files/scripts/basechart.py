#!/usr/bin/python2

import os
import sys
script_dir = os.path.normpath(sys.path[0])
sys.path.append(os.path.abspath(os.path.join(script_dir, "../../utils/")))
import subprocess
import dirutils
from string import Template

def generate_includes(includes_dir, theme):
    # Get all includefiles with the correct theme
    includes = [inc for inc in os.listdir(includes_dir) if inc.startswith(theme)]
    # We need to sort them to have them appear in correct order in the target map file
    includes.sort()

    rel_includes_path = os.path.basename(includes_dir)

    # Update the list, adding mapserver keyword and relative path to the include files
    for i, item in enumerate(includes):
        includes[i] = str.format("INCLUDE \"{}/{}\"", rel_includes_path, item)
    return "\n    ".join(includes)


def get_dictionary(theme, map_path, fonts_path, debug_string):
    return  { 'THEME': theme,
              'HOST': 'http://localhost/cgi-bin/mapserv.fcgi',
              'DEBUG': debug_string,
              'MAP_PATH': map_path,
              'FONTS_PATH': fonts_path,
              'INCLUDES': generate_includes(os.path.join(map_path, "includes"), theme)}

debug_template = '''CONFIG "MS_ERRORFILE" "/tmp/SeaChart_{0}.log"
    DEBUG 5
    CONFIG "ON_MISSING_DATA" "LOG"'''

def create_capability_files(template_path, themes_path, map_path, fonts_path, use_debug):
    template = Template( open( os.path.join(template_path, "SeaChart_THEME.map"), 'r' ).read() )
    for theme in os.listdir(themes_path):
        # Remove file suffix
        theme = os.path.splitext(theme)[0]

        debug_string = ""
        if use_debug:
            debug_string = str.format(debug_template, theme)

        d = get_dictionary(theme, map_path, fonts_path, debug_string)

        fileout = open( os.path.join(map_path, "SeaChart_" + theme + ".map"), 'w' )
        fileout.write( template.substitute(d) )

def create_legend_files(template_path, themes_path, map_path, fonts_path, use_debug):
    template = Template( open( os.path.join(template_path, "SeaChart_Legend_THEME.map"), 'r' ).read() )
    for theme in os.listdir(themes_path):
        # Remove file suffix
        theme = os.path.splitext(theme)[0]

        debug_string = ""
        if use_debug:
            debug_string = str.format(debug_template, theme)

        d = get_dictionary(theme, map_path, fonts_path, debug_string)

        legend_path = dirutils.force_sub_dir(map_path, "legends")

        fileout = open( os.path.join(legend_path, "SeaChart_Legend_" + theme + ".map"), 'w' )
        fileout.write( template.substitute(d) )

def generate_basechart_config(data_path,map_path,rule_set_path,resource_dir,force_overwrite,debug):

    # Generate new map files
    dirutils.clear_folder(map_path)
    subprocess.call("./process_all_layers.sh data=" + data_path + " target=" + map_path + " config=" + rule_set_path, shell=True)

    fonts_path = os.path.join("./fonts", "fontset.lst")
    create_capability_files(os.path.join(resource_dir, "templates"), os.path.join(rule_set_path, "color_tables"), map_path, fonts_path, debug)
    create_legend_files(os.path.join(resource_dir, "templates"), os.path.join(rule_set_path, "color_tables"), map_path, fonts_path, debug)

    dirutils.copy_and_replace(os.path.join(resource_dir, "epsg"), os.path.join(map_path, "epsg"))
    dirutils.copy_and_replace(os.path.join(resource_dir, "symbols"), os.path.join(map_path, "symbols"))
    dirutils.copy_and_replace(os.path.join(resource_dir, "fonts"), os.path.join(map_path, "fonts"))
