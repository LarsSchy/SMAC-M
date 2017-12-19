#!/usr/bin/python2

import os
import sys
import csv
import re
script_dir = os.path.normpath(sys.path[0])
sys.path.append(os.path.abspath(os.path.join(script_dir, "../../utils/")))
import subprocess
import dirutils
from string import Template
from chartsymbols import ChartSymbols


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

def generate_basechart_config(data_path,map_path,rule_set_path,resource_dir,force_overwrite,debug, chartsymbols):

    # Generate new map files
    dirutils.clear_folder(map_path)

    if chartsymbols:
        process_all_layers(data_path, map_path, rule_set_path, chartsymbols)
    else:
        subprocess.call("./process_all_layers.sh data=" + data_path + " target=" + map_path + " config=" + rule_set_path, shell=True)

    fonts_path = os.path.join("./fonts", "fontset.lst")
    create_capability_files(os.path.join(resource_dir, "templates"), os.path.join(rule_set_path, "color_tables"), map_path, fonts_path, debug)
    create_legend_files(os.path.join(resource_dir, "templates"), os.path.join(rule_set_path, "color_tables"), map_path, fonts_path, debug)

    dirutils.copy_and_replace(os.path.join(resource_dir, "epsg"), os.path.join(map_path, "epsg"))
    dirutils.copy_and_replace(os.path.join(resource_dir, "symbols"), os.path.join(map_path, "symbols"))
    dirutils.copy_and_replace(os.path.join(resource_dir, "fonts"), os.path.join(map_path, "fonts"))

def get_maxscaledenom(config):

    #
    #  Read max scale denom values from a resource file (layer_msd.csv)
    #
    msd = {}
    with open(config + '/layer_rules/layer_msd.csv', 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            msd[row[0]] = row[1]

    return msd


def get_colors(color_table):

    #
    #  Make an associative array with colors based on the color CSV file
    #  code, rgb_color, hex_color
    #
    colors = {}
    with open(color_table, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            colors[row[0]] = (row[1], row[2])

    return colors
    

def process_all_layers(data, target, config, chartsymbols_file=None):

    # Reimplementation of the shel script of the same name
    msd = get_maxscaledenom(config)

    chartsymbols = None
    if chartsymbols_file:
        chartsymbols = ChartSymbols(chartsymbols_file, 'Simplified')

    #
    #  Process all color themes
    #

    for color in os.listdir(config + '/color_tables'):
        print "Loading " + color
        theme = os.path.splitext("path_to_file")[0]
        if chartsymbols:
            chartsymbols.load_colors(color[:-4])
        for layer in os.listdir(data):
            color_table = config + '/color_tables/' + color
            input_file = config + '/layer_rules/layer_groups.csv'
            process_layer_colors(layer, color_table, input_file, msd[layer], data, target, chartsymbols)


def get_layer_mapfile(layer, feature, group, color_table, msd):
    template = '../resources/templates/basechart_templates/{}_template_color.map'.format(feature)
    base = "CL{}-{}".format(layer, feature)
    mapfile = ''
    if not os.path.isfile(template):
        return mapfile

    colors = get_colors(color_table)
    def get_hex_color(match):
        return colors[match.group(1)][1]
    def get_rgb_color(match):
        return colors[match.group(1)][0]

    #print "Layer: {} Processing feature: {}.".format(layer, feature)
    with open(template, 'rb') as templ:
        mapfile = templ.read()
    mapfile = re.sub(r'{CL}', layer, mapfile)
    mapfile = re.sub(r'{PATH}', '{}/{}'.format(layer, base), mapfile)
    mapfile = re.sub(r'{PATH_OGR}', '{}/{}.shp'.format(layer, base), mapfile)
    mapfile = re.sub(r'{OGR_SQL_LAYER}', base, mapfile)
    mapfile = re.sub(r'{MAXSCALE}', msd, mapfile)
    mapfile = re.sub(r'{GROUP}', group, mapfile)
    mapfile = re.sub(r'{(.....)}', get_hex_color, mapfile)
    mapfile = re.sub(r'{(.....)_rgb}', get_rgb_color, mapfile)
    return mapfile


def process_layer_colors(layer, color_table, input_file, msd, data, target, chartsymbols=None):
    #  Reimplementation of the shell script of the same name

    # Create directory
    try:
        os.mkdir(target + '/includes')
    except OSError:
        # Already exist
        pass

    theme = os.path.splitext(os.path.basename(color_table))[0]


    # File that will contain the result
    final_file = open(
        '{}/includes/{}_layer{}_inc.map'.format(target, theme, layer), 'w')

    with open(input_file, 'rb') as if_csv:
        reader = csv.reader(if_csv)
        next(reader, None)  # skip the headers
        for row in reader:
            feature = row[0]
            group = row[1]
            data_file = '{0}/{1}/CL{1}-{2}.shp'.format(data, layer, feature)
            if os.path.isfile(data_file):
                mapfile = ''
                if chartsymbols:
                    if feature[:6] == 'point-':
                        mapfile = chartsymbols.get_point_mapfile(layer, feature[6:], group, msd)
                if not mapfile:
                    mapfile = get_layer_mapfile(layer, feature, group, color_table, msd)
                if mapfile:
                    final_file.write(mapfile)

    final_file.write("""
#
#  Dummy layer to flush the label cache
#
LAYER
   NAME "force_label_draw_CL${CL}"
   GROUP "base"
   TYPE POINT
   PROCESSING FORCE_DRAW_LABEL_CACHE=FLUSH
   TRANSFORM FALSE
   STATUS ON
   FEATURE
      POINTS 1 1 END
   END
END
    """)
    final_file.close()
