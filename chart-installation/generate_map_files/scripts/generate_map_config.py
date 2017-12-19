#!/usr/bin/python2

import argparse
import os
import sys
script_dir = os.path.normpath(sys.path[0])
sys.path.append(os.path.abspath(os.path.join(script_dir, "../../utils/")))
import dirutils
from ruleutils import create_layer_rules, create_color_rules

from basechart import generate_basechart_config
from geotif import generate_tif_config
from elevation import generate_elevation_config
from aml import generate_aml_config

resource_dir = os.path.normpath(os.path.join(script_dir, "..", "resources"))

def parse_arguments():
    parser = argparse.ArgumentParser(prog="generate_map_config.py",
            description="This program generates mapserver configuration for different kinds of geographical data. The resulting mapserver configuration will be put in the folder 'map' in the same folder as the geographical data. For the basechart option , the layer and color rules are fetched from the rule-set-path. If they are not present the script will create a default one at this location.")
    parser.add_argument("-f", "--force-overwrite", action="store_true", help="Force overwrite the rule set at RULE_SET_PATH")
    basechartgroup = parser.add_argument_group("BaseChart arguments:")
    basechartgroup.add_argument("-basechartdata", "--basechart-data-path", nargs=1, help="Directory where your converted chart data is stored. The subfolder needs to be named 'shape'.")
    geotifgroup = parser.add_argument_group("GeoTif arguments:")
    geotifgroup.add_argument("-geotifdata", "--geotif-data-path", nargs=1, help="Directory where your Geotif files are stored. The subfolder needs to be named 'data'.")
    elevationgroup = parser.add_argument_group("Elevation arguments:")
    elevationgroup.add_argument("-elevationdata", "--elevation-data-path", nargs=1, help="Directory where your Elevation data files are stored. The subfolder needs to be named 'data'.")
    amlgroup = parser.add_argument_group("AML arguments:")
    amlgroup.add_argument("-amldata", "--aml-data-path", nargs=1, help="Directory where your AML data files are stored. The subfolder needs to be named 'data'.")
    parser.add_argument("-rules", "--rule-set-path", nargs=1, help="Path to map configuration rule set", required=True)
    parser.add_argument("-rule-default-color", nargs=1, help="Substring that uniquely identifies a color table")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug on the mapserver")
    parser.add_argument("-c", "--chartsymbols", nargs=1, help="Use OpenCPN chartsymbols.xml file to generate layers")
    args = parser.parse_args()
    if not ((args.basechart_data_path and args.rule_set_path) or args.geotif_data_path or args.elevation_data_path or args.aml_data_path):
        parser.print_help()
        sys.exit(2)
    return args

def main():
    args = parse_arguments()

    # Set up the paths to use
    rule_set_path = dirutils.force_sub_dir(os.path.abspath(args.rule_set_path[0]), "rules")
    data_path = None
    if args.basechart_data_path:
        data_path = dirutils.force_sub_dir(os.path.abspath(os.path.normpath(args.basechart_data_path[0])), "shape")
    elif args.geotif_data_path:
        data_path = dirutils.force_sub_dir(os.path.abspath(os.path.normpath(args.geotif_data_path[0])), "data")
    elif args.elevation_data_path:
        data_path = dirutils.force_sub_dir(os.path.abspath(os.path.normpath(args.elevation_data_path[0])), "data")
    elif args.aml_data_path:
        data_path = dirutils.force_sub_dir(os.path.abspath(os.path.normpath(args.aml_data_path[0])), "data")

    if not data_path:
        print "No data found"
        sys.exit(1)

    chartsymbols = None
    if args.chartsymbols and not os.path.isfile(args.chartsymbols[0]):
        print "chartsymbols.xml not found at: " + args.chartsymbols[0]
        sys.exit(1)
    elif args.chartsymbols:
        chartsymbols = args.chartsymbols[0]

    if not os.path.exists(data_path):
        os.makedirs(data_path)
    map_path = os.path.normpath(os.path.join(data_path, "..", "map"))
    # Move context to the script dir and run from there
    os.chdir(script_dir)

    # Check if color tables exist and create them if not
    color_tables_exist = dirutils.does_color_tables_exist(rule_set_path)
    if not color_tables_exist or args.force_overwrite:
        if args.rule_default_color:
            color_table = args.rule_default_color[0]
        else:
            color_table = None
        create_color_rules(resource_dir, os.path.join(rule_set_path, "color_tables"), color_table)

    if args.basechart_data_path:
        # Check if layer definitions exist and create them if not
        layer_definitions_exist = dirutils.does_layer_rules_exist(rule_set_path)
        if not layer_definitions_exist or args.force_overwrite:
           create_layer_rules(resource_dir, os.path.join(rule_set_path, "layer_rules"))
        # Generate the BaseChart config ...
        generate_basechart_config(data_path, map_path, rule_set_path, resource_dir, args.force_overwrite, args.debug, chartsymbols)
    elif args.geotif_data_path:
        # ... or the TIF config
        generate_tif_config(data_path, map_path, args.debug)
    elif args.elevation_data_path:
        # ... or Elevation config
        generate_elevation_config(data_path, map_path, args.debug)
    elif args.aml_data_path:
        # ... or AML config
        layer_definitions_exist = dirutils.does_layer_rules_exist(rule_set_path)
        if not layer_definitions_exist or args.force_overwrite:
           create_layer_rules(resource_dir, os.path.join(rule_set_path, "layer_rules"))
        generate_aml_config(data_path, map_path, rule_set_path, resource_dir, args.force_overwrite, args.debug)
        

if __name__ == "__main__":
    main()
