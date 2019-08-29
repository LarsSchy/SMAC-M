#!/usr/bin/python2
from __future__ import print_function

import os
import csv
import re
import subprocess
from string import Template

from osgeo import ogr

from .chartsymbols import ChartSymbols
from utils import dirutils


def generate_includes(includes_dir, theme):
    # Get all includefiles with the correct theme
    includes = [inc for inc in os.listdir(
        includes_dir) if inc.startswith(theme)]
    # We need to sort them to have them appear in correct order in the target
    # map file
    includes.sort()

    rel_includes_path = os.path.basename(includes_dir)

    # Update the list, adding mapserver keyword and relative path to the
    # include files
    for i, item in enumerate(includes):
        includes[i] = str.format("INCLUDE \"{}/{}\"", rel_includes_path, item)
    return "\n    ".join(includes)


def get_dictionary(theme, map_path, fonts_path, debug_string):
    return {'THEME': theme,
            'HOST': 'http://localhost/cgi-bin/mapserv.fcgi',
            'DEBUG': debug_string,
            'MAP_PATH': map_path,
            'FONTS_PATH': fonts_path,
            'INCLUDES': generate_includes(os.path.join(map_path, "includes"),
                                          theme),
            'SHAPEPATH': "../shape/"
            }


debug_template = '''CONFIG "MS_ERRORFILE" "/tmp/SeaChart_{0}.log"
    DEBUG 5
    CONFIG "ON_MISSING_DATA" "LOG"'''


def create_capability_files(template_path, themes_path, map_path, fonts_path,
                            use_debug, shapepath):
    template = Template(
        open(os.path.join(template_path, "SeaChart_THEME.map"), 'r').read())
    for theme in os.listdir(themes_path):
        # Remove file suffix
        theme = os.path.splitext(theme)[0]

        debug_string = ""
        if use_debug:
            debug_string = str.format(debug_template, theme)

        d = get_dictionary(theme, map_path, fonts_path, debug_string)
        if shapepath:
            d['SHAPEPATH'] = shapepath
        fileout = open(os.path.join(
            map_path, "SeaChart_" + theme + ".map"), 'w')

        fileout.write(template.substitute(d))


def create_legend_files(template_path, themes_path, map_path, fonts_path,
                        use_debug):
    with open(os.path.join(template_path, "SeaChart_Legend_THEME.map")) as f:
        template = Template(f.read())

    for theme in os.listdir(themes_path):
        # Remove file suffix
        theme = os.path.splitext(theme)[0]

        debug_string = ""
        if use_debug:
            debug_string = str.format(debug_template, theme)

        d = get_dictionary(theme, map_path, fonts_path, debug_string)

        legend_path = dirutils.force_sub_dir(map_path, "legends")

        fileout = open(os.path.join(
            legend_path, "SeaChart_Legend_" + theme + ".map"), 'w')
        fileout.write(template.substitute(d))


def generate_basechart_config(data_path, map_path, rule_set_path, resource_dir,
                              force_overwrite, debug, point_table, area_table,
                              displaycategory, chartsymbols, excluded_lookups):

    # Generate new map files
    dirutils.clear_folder(map_path)

    if chartsymbols:
        shapepath = data_path
        process_all_layers(data_path, map_path, rule_set_path, point_table,
                           area_table, displaycategory, chartsymbols,
                           excluded_lookups)

    fonts_path = os.path.join("./fonts", "fontset.lst")
    create_capability_files(os.path.join(resource_dir, "templates"),
                            os.path.join(rule_set_path, "color_tables"),
                            map_path, fonts_path, debug, shapepath)
    create_legend_files(os.path.join(resource_dir, "templates"),
                        os.path.join(rule_set_path, "color_tables"),
                        map_path, fonts_path, debug)

    dirutils.copy_and_replace(os.path.join(
        resource_dir, "epsg"), os.path.join(map_path, "epsg"))
    dirutils.copy_and_replace(os.path.join(
        resource_dir, "symbols"), os.path.join(map_path, "symbols"))
    dirutils.copy_and_replace(os.path.join(
        resource_dir, "fonts"), os.path.join(map_path, "fonts"))


def get_maxscaledenom(config):

    #
    #  Read max scale denom values from a resource file (layer_msd.csv)
    #
    msd = {}
    with open(config + '/layer_rules/layer_msd.csv', 'r') as csvfile:
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
    with open(color_table, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            colors[row[0]] = (row[1], row[2])

    return colors


def process_all_layers(data, target, config, point_table='Simplified',
                       area_table='Plain', displaycategory=None,
                       chartsymbols_file=None, excluded_lookups=None):

    # Reimplementation of the shel script of the same name
    msd = get_maxscaledenom(config)

    chartsymbols = None
    if chartsymbols_file:
        chartsymbols = ChartSymbols(
            chartsymbols_file, point_table, area_table, displaycategory,
            excluded_lookups=excluded_lookups
        )

    # Test if the shapefile is of the right Geometry
    shp_types = {}
    shp_fields = {}
    if chartsymbols:
        geometries = {
            'Point': 'POINT',
            'Line': 'LINESTRING',
            'Polygon': 'POLYGON',
            '3D Point': 'POINT',
        }
        print("Check geometry of all layers...")
        for (dirpath, dirnames, filenames) in os.walk(data):
            for filename in filenames:
                if filename.endswith('.shp'):
                    level = filename[2:3]
                    print("checking {}".format(filename),
                          end=(' ' * 18 + '\r'), flush=True)
                    output = subprocess.check_output(
                        ["ogrinfo", "-al", "-so",
                            '{}/{}/{}'.format(data, level, filename)],
                        stderr=subprocess.STDOUT).decode()
                    geomtype = re.search(
                        r'Geometry: (.+)$', output, re.IGNORECASE)
                    if geomtype:
                        try:
                            shp_types[filename] = geometries[geomtype.group(1)]
                        except KeyError:
                            shp_types[filename] = 'UNKNOWN'
                    ds = ogr.Open('{}/{}/{}'.format(data, level, filename))
                    try:
                        layer = ds.GetLayer()
                        defn = layer.GetLayerDefn()
                        shp_fields[filename] = [
                            defn.GetFieldDefn(i).GetName()
                            for i in range(defn.GetFieldCount())
                        ]
                    finally:
                        ds.Destroy()

    #
    #  Process all color themes
    #

    for color in os.listdir(config + '/color_tables'):
        print("Loading " + color)
        # theme = os.path.splitext("path_to_file")[0]
        if chartsymbols:
            chartsymbols.load_colors(color[:-4])
        for layer in os.listdir(data):
            if not layer.isdigit():
                continue
            color_table = config + '/color_tables/' + color
            input_file = config + '/layer_rules/layer_groups.csv'
            process_layer_colors(layer, color_table, input_file,
                                 msd[layer], data, target, chartsymbols,
                                 shp_types, shp_fields)


def get_layer_mapfile(layer, feature, group, color_table, msd):
    enhanced = False
    # enhanced feature name
    template_path = '../resources/templates/basechart_templates/'
    if feature[-5:] == 'POINT':
        enhanced = True
        template = template_path + 'point-{}_template_color.map'.format(
            feature[:-6])
    elif feature[-10:] == 'LINESTRING':
        enhanced = True
        template = template_path + 'line-{}_template_color.map'.format(
            feature[:-11])
    elif feature[-7:] == 'POLYGON':
        enhanced = True
        template = template_path + 'poly-{}_template_color.map'.format(
            feature[:-8])
    else:
        template = template_path + '{}_template_color.map'.format(feature)

    if not enhanced:
        base = "CL{}-{}".format(layer, feature)
    else:
        base = "CL{}_{}".format(layer, feature)
    mapfile = ''

    if not os.path.isfile(template):
        return mapfile

    colors = get_colors(color_table)

    def get_hex_color(match):
        return colors[match.group(1)][1]

    def get_rgb_color(match):
        return colors[match.group(1)][0]

    # print "Layer: {} Processing feature: {}.".format(layer, feature)
    with open(template, 'r') as templ:
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


def process_layer_colors(layer, color_table, input_file, msd, data, target,
                         chartsymbols=None, shp_types={}, shp_fields={}):
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

    if not chartsymbols:
        with open(input_file, 'r') as if_csv:
            reader = csv.reader(if_csv)
            next(reader, None)  # skip the headers
            for row in reader:
                feature = row[0]
                group = row[1]
                data_file = '{0}/{1}/CL{1}-{2}.shp'.format(
                    data, layer, feature)
                if os.path.isfile(data_file):
                    mapfile = get_layer_mapfile(
                        layer, feature, group, color_table, msd)
                    if mapfile:
                        final_file.write(mapfile)
    else:
        layers = []
        for (base, dirs, filenames) in os.walk('{0}/{1}/'.format(data, layer)):
            for filename in filenames:
                if filename.endswith('.shp'):
                    feature = os.path.splitext(filename)[0][4:10]
                    geom = os.path.splitext(filename)[0][11:]
                    if shp_types and not shp_types[filename] in geom:
                        print("{} does not match geometry: {} in {}".format(
                            filename, shp_types[filename], geom))
                        continue

                    if geom == 'POINT':
                        layer_obj = chartsymbols.get_point_mapfile(
                            layer, feature, 'default', msd,
                            shp_fields[filename])
                    elif geom == 'LINESTRING':
                        layer_obj = chartsymbols.get_line_mapfile(
                            layer, feature, 'default', msd,
                            shp_fields[filename])
                    elif geom == 'POLYGON':
                        layer_obj = chartsymbols.get_poly_mapfile(
                            layer, feature, 'default', msd,
                            shp_fields[filename])
                    else:
                        continue

                    layers.append(layer_obj)

        final_file.write('\n'.join(l.mapfile for l in sorted(layers) if l))

    final_file.write("""
#
#  Dummy layer to flush the label cache
#
LAYER
   NAME "force_label_draw_CL${CL}"
   GROUP "default"
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
