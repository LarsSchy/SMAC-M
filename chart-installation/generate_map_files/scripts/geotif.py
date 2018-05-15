#!/usr/bin/python2

import os
import sys
script_dir = os.path.normpath(sys.path[0])
sys.path.append(os.path.abspath(os.path.join(script_dir, "../../utils/")))
import re
from osgeo import gdal
from osgeo import osr
from string import Template
import dirutils
import rasterutils

gdal.UseExceptions()

resource_dir = os.path.normpath(os.path.join(script_dir, "..", "resources"))

tif_suffix = [".tif", ".tiff"]
output_srs = 4326

debug_text = '''CONFIG "MS_ERRORFILE" "/tmp/geotif.log"
  DEBUG 5
  CONFIG "ON_MISSING_DATA" "LOG"'''


def create_main_dic(data_path, map_path, extent, srs, layers, use_debug):
    debug_string = ""
    if use_debug:
        debug_string = debug_text
    return {'DATA_PATH': "../data",
            'DEBUG': debug_string,
            'EXTENT': ' '.join(map(str, extent)),
            'SRS': srs,
            'SERVER_URL': 'http://mapserver/cgi-bin/mapserv.fcgi',
            'MAP_PATH': map_path,
            'LAYERS': '\n'.join(layers)}


def create_layer_dic(basename, group_name, srs, relative_tif_path):
    return {'GEO_TIF_NAME': basename,
            'GEO_TIF_GROUP_NAME': group_name,
            'SRS': srs,
            'GEO_TIF_PATH': relative_tif_path}


# Traverse the directory recursively looking for tif files
def create_layers(template, data_path, rasterfiles):
    layers = []
    for item in rasterfiles:
        file_name = item[1]
        name = os.path.splitext(item[1])[0]
        group = item[0] or os.path.splitext(item[1])[0]
        sub_dir = item[0] or ""
        source_srs = rasterutils.calculate_source_projection(
            os.path.join(data_path, sub_dir, file_name))
        dictionary = create_layer_dic(
            name, group, source_srs, os.path.join(sub_dir, file_name))
        layers.append(template.substitute(dictionary))
    return layers


def generate_tif_config(data_path, map_path, debug):
    main_template_path = os.path.join(
        resource_dir, "templates", "geotif_templates", "geotif_main.map")
    layer_template_path = os.path.join(
        resource_dir, "templates", "geotif_templates", "geotif_layer.map")

    if not os.path.isfile(main_template_path) or \
       not os.path.isfile(layer_template_path):
        print("No templates found for this data type")
        sys.exit(1)

    main_template = Template(open(main_template_path, 'r').read())
    layer_template = Template(open(layer_template_path, 'r').read())

    dirutils.clear_folder(map_path)

    rasterfiles = rasterutils.find_all_raster_files(data_path, tif_suffix)

    layers = create_layers(layer_template, data_path, rasterfiles)
    # Write output map file if layers is non-empty
    if layers:
        extent = rasterutils.calculate_total_extent(
            data_path, rasterfiles, output_srs)
        dictionary2 = create_main_dic(
            data_path, map_path, extent, output_srs, layers, debug)
        output = open(os.path.join(map_path, 'Geotif.map'), 'w')
        output.write(main_template.substitute(dictionary2))

        print("Generated:\n\t" + '\n\t'.join(os.listdir(map_path)))
    else:
        print("Error: No data found in " + data_path)
