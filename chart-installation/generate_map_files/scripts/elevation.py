#!/usr/bin/python2

import os
import sys
script_dir = os.path.normpath(sys.path[0])
sys.path.append(os.path.abspath(os.path.join(script_dir, "../../utils/")))
import re
from multiprocessing import Process
from glob import iglob
from subprocess import call
from itertools import groupby
import operator
from string import Template
import dirutils
import rasterutils

resource_dir = os.path.normpath(os.path.join(script_dir, "..", "resources"))
no_data_value = "-9999"
elevation_folder_name = "../gen_data/elevation"
hillshade_folder_name = "../gen_data/hillshades"

known_elev_filetypes = [".dt1", ".tif", ".adf"]
compression_levels = ["2", "4", "8", "16"]
output_srs = 4326

debug_text = '''CONFIG "MS_ERRORFILE" "/tmp/elevation.log"
  DEBUG 5
  CONFIG "ON_MISSING_DATA" "LOG"'''

# Look for a know filetype in <path>


def get_file_type_of_data_in(path):
    _, files = dirutils.get_dirs_and_files_in(path)
    if files:
        for f in files:
            _, filesuffix = os.path.splitext(f)
            if filesuffix in known_elev_filetypes:
                return filesuffix
    return "Unknown file type"


def create_main_dic(data_path, map_path, extent, srs, layers, use_debug):
    debug_string = ""
    if use_debug:
        debug_string = debug_text
    return {'DATA_PATH': os.path.relpath(data_path, map_path),
            'DEBUG': debug_string,
            'EXTENT': ' '.join(map(str, extent)),
            'SRS': srs,
            'NO_DATA_VALUE': no_data_value,
            'SERVER_URL': 'http://mapserver/cgi-bin/mapserv.fcgi',
            'MAP_PATH': map_path,
            'LAYERS': '\n'.join(layers)}


def create_layer_dic(basename, group_name, vrt_path, source_srs):
    return {'NAME': basename,
            'GROUP_NAME': group_name,
            'PATH': vrt_path,
            'SRS': source_srs}


def create_layers(template, files, data_path):
    layers = []
    for f in files:
        file_name = f[1]
        sub_dir = f[0] or ""
        group_name = f[0] or os.path.splitext(file_name)[0]
        file_path = os.path.join(data_path, sub_dir, file_name)
        source_srs = rasterutils.calculate_source_projection(file_path)
        dictionary = create_layer_dic(file_name, group_name, os.path.relpath(
            file_path, data_path), source_srs or output_srs)
        layers.append(template.substitute(dictionary))
    return layers


def generate_virtual_and_overview(elev_gen_path, hill_gen_path, sub_dir, vrt_name, vrtlist_file):
    #   Create a .vrt and .ovr file in all valid directories
    try:
        vrt_filename = (sub_dir or vrt_name) + ".vrt"
        print("Generating " + vrt_filename)
        sys.stdout.flush()
        vrt_file = os.path.join(elev_gen_path, sub_dir or "", vrt_filename)
        bashCmd = ' '.join(["gdalbuildvrt", "-q", "-vrtnodata",
                            no_data_value, "-input_file_list", vrtlist_file, vrt_file])
        call(bashCmd, shell=True)

        tif_filename = (sub_dir or vrt_name) + ".tif"
        print("Warping " + vrt_filename + " -> " + tif_filename)
        sys.stdout.flush()
        tif_file = os.path.join(elev_gen_path, sub_dir or "", tif_filename)
        bashCmd = ' '.join(["gdalwarp", "-q", vrt_file, tif_file, "-r bilinear", "-t_srs EPSG:" + str(output_srs), "--config GDAL_CACHEMAX 500",
                            "-wm 500", "-multi", "-co TILED=YES", "-co COMPRESS=DEFLATE", "-co predictor=2", "-dstnodata " + no_data_value])
        call(bashCmd, shell=True)

        print("Creating overview for " + tif_filename)
        sys.stdout.flush()
        bashCmd = ' '.join(["gdaladdo", "-q", "-ro", tif_file, " ".join(
            compression_levels), "--config", "COMPRESS_OVERVIEW", "DEFLATE"])
        call(bashCmd, shell=True)

        generate_hillshade_and_overview(hill_gen_path, sub_dir, tif_file)

        print("Elevation and hillshade finished for " + tif_filename)
    except Exception as e:
        print(e)
        print("Could not process data %s" % vrt_filename)


def generate_hillshade_and_overview(hill_gen_path, sub_dir, tif_file):
    hs_path = os.path.join(hill_gen_path, sub_dir or "")
    if not os.path.exists(hs_path):
        os.makedirs(hs_path)
    try:
        hs_filename = os.path.basename(tif_file)
        print("Generating hillshade for " + hs_filename)
        sys.stdout.flush()
        hillshade_file = os.path.join(hs_path, hs_filename)
        azimuth = rasterutils.get_proper_azimuth_for_file(tif_file)
        bashCmd = ' '.join(["gdaldem", "hillshade", "-q", tif_file, hillshade_file, "-az", str(
            azimuth), "-alt 60", "-z 5", "-s 111120", "-co compress=deflate", "-compute_edges"])
        call(bashCmd, shell=True)

        print("Generating hillshade overview for " + hs_filename)
        sys.stdout.flush()
        bashCmd = ' '.join(["gdaladdo", "-q",  "-ro", hillshade_file, " ".join(
            compression_levels), "--config", "COMPRESS_OVERVIEW", "DEFLATE"])
        call(bashCmd, shell=True)

    except Exception as e:
        print(e)
        print("Could not process data %s" % hs_filename)

# Create vrt and ovr files for all elevation data sets, in parallel


def prepare_data(data_path, elev_gen_path, hill_gen_path):
    processes = []
    files = rasterutils.find_all_raster_files(data_path, known_elev_filetypes)
    for folder, group in groupby(files, operator.itemgetter(0)):
        #       Handle files in subfolder
        if folder:
            dirutils.clear_folder(os.path.join(elev_gen_path, folder))
            filename = os.path.join(elev_gen_path, folder, folder + ".vrtlist")
            with open(filename, 'a') as vrttemp:
                for f in list(group):
                    vrttemp.write(os.path.join(data_path, f[0], f[1]) + '\n')
                processes.append(Process(target=generate_virtual_and_overview, args=(
                    elev_gen_path, hill_gen_path, folder, folder, filename)))
#       Handle files directly under the data dir
        else:
            for g in list(group):
                filename = os.path.join(elev_gen_path, g[1] + ".vrtlist")
                with open(filename, 'w') as vrttemp:
                    vrttemp.write(os.path.join(data_path, g[1]) + '\n')
                processes.append(Process(target=generate_virtual_and_overview, args=(
                    elev_gen_path, hill_gen_path, None, os.path.splitext(g[1])[0], filename)))

    for p in processes:
        p.start()
    for p in processes:
        p.join()


def create_map_file(data_path, map_path, mapfile_name, file_suffix, main_template, layer_template, debug):
    files = rasterutils.find_all_raster_files(data_path, file_suffix)
    layers = create_layers(layer_template, files, data_path)
    if layers:
        total_extent = rasterutils.calculate_total_extent(
            data_path, files, output_srs)
        dictionary = create_main_dic(
            data_path, map_path, total_extent, output_srs, layers, debug)
        output = open(os.path.join(map_path, mapfile_name), 'w')
        output.write(main_template.substitute(dictionary))

    else:
        print("Error: No data found in " + data_path)
        sys.exit(1)


def generate_elevation_config(data_path, map_path, debug):
    elev_gen_path = os.path.normpath(
        os.path.join(data_path, elevation_folder_name))
    hill_gen_path = os.path.normpath(
        os.path.join(data_path, hillshade_folder_name))

    print("Clearing folder with generated files")
    dirutils.clear_folder(map_path)
    dirutils.clear_folder(elev_gen_path)
    dirutils.clear_folder(hill_gen_path)

    templates_dir = os.path.join(
        resource_dir, "templates", "elevation_templates")
    main_template_path = os.path.join(templates_dir, "elevation_main.map")
    layer_template_path = os.path.join(templates_dir, "elevation_layer.map")
    hillshade_main_template_path = os.path.join(
        templates_dir, "hillshade_main.map")
    hillshade_layer_template_path = os.path.join(
        templates_dir, "hillshade_layer.map")

    if not os.path.isfile(main_template_path) or \
       not os.path.isfile(layer_template_path) or \
       not os.path.isfile(hillshade_main_template_path) or \
       not os.path.isfile(hillshade_layer_template_path):
        print("No templates found for this data type")
        sys.exit(1)

    main_template = Template(open(main_template_path, 'r').read())
    layer_template = Template(open(layer_template_path, 'r').read())
    hillshade_main_template = Template(
        open(hillshade_main_template_path, 'r').read())
    hillshade_layer_template = Template(
        open(hillshade_layer_template_path, 'r').read())

#   Do data preparation
    prepare_data(data_path, elev_gen_path, hill_gen_path)

#   Create elevation map file
    create_map_file(elev_gen_path, map_path, 'Elevation.map', [
                    '.tif'], main_template, layer_template, debug)

#   Create hillshade map file
    create_map_file(hill_gen_path, map_path, 'Hillshade.map', [
                    '.tif'], hillshade_main_template, hillshade_layer_template, debug)

    print("Generated:\n\t" + '\n\t'.join(os.listdir(map_path)))
