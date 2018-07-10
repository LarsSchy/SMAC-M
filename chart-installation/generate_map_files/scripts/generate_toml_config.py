"""Generate a TOML configuration for the equivalent call to generate_map_config

This program takes the same arguments as generate_map_config and generates a
file that generate_map_config_v2 can use to generate the same mapfiles.
"""

import argparse
import os
import sys
import toml

DEFAULTS = {
    'tablename': 'Simplified',
    'displaycategory': 'Standard',
    'paths': {
    }
}


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument(
        "-f", "--force-overwrite", action="store_true",
        help="Force overwrite the rule set at RULE_SET_PATH (Ignored)")
    basechartgroup = parser.add_argument_group("BaseChart arguments:")
    basechartgroup.add_argument(
        "-basechartdata", "--basechart-data-path",
        help="Directory where your converted chart data is stored.")
    enhancedchartgroup = parser.add_argument_group("Enhanced Chart arguments:")
    enhancedchartgroup.add_argument(
        "-enhancedchartdata", "--enhanced-data-path",
        help="Directory where your converted enhanced chart data is stored.")
    geotifgroup = parser.add_argument_group("GeoTif arguments:")
    geotifgroup.add_argument(
        "-geotifdata", "--geotif-data-path",
        help="Directory where your Geotif files are stored.")
    elevationgroup = parser.add_argument_group("Elevation arguments:")
    elevationgroup.add_argument(
        "-elevationdata", "--elevation-data-path",
        help="Directory where your Elevation data files are stored.")
    amlgroup = parser.add_argument_group("AML arguments:")
    amlgroup.add_argument(
        "-amldata", "--aml-data-path",
        help="Directory where your AML data files are stored.")
    parser.add_argument(
        "-rules", "--rule-set-path",
        help="Path to map configuration rule set", required=True)
    parser.add_argument(
        "-rule-default-color",
        help="Substring that uniquely identifies a color table")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Enable debug on the mapserver")
    parser.add_argument(
        "-c", "--chartsymbols",
        help="Use OpenCPN chartsymbols.xml file to generate layers")
    parser.add_argument(
        "-y", "--displaycategory",
        help="Comma separated list of OpenCPN Display Category to load. "
        "Displaybase is always loaded, default is Standard.")
    parser.add_argument(
        "-t", "--tablename",
        help="Which OpenCPN chartsymbols.xml table to generate. "
        "Default is Simplified.")
    parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                        required=True,
                        help='Configuration file to create')

    args = parser.parse_args()
    if not ((args.basechart_data_path and args.rule_set_path) or
            (args.enhanced_data_path and args.rule_set_path) or
            args.geotif_data_path or
            args.elevation_data_path or
            args.aml_data_path):
        parser.print_help()
        sys.exit(2)
    return args


if __name__ == '__main__':
    params = DEFAULTS
    args = parse_arguments()

    config_file_dir = os.path.dirname(args.output.name)
    if config_file_dir:
        def rel_path(path):
            return os.path.relpath(os.path.abspath(os.path.normpath(path)),
                                   config_file_dir)

    else:
        def rel_path(path):
            return os.path.abspath(os.path.normpath(path))

    params['debug'] = args.debug

    if args.tablename:
        params['tablename'] = args.tablename

    if args.displaycategory:
        params['displaycategory'] = args.displaycategory

    if args.chartsymbols:
        params['paths']['chartsymbols'] = os.path.abspath(args.chartsymbols)

    if args.rule_set_path:
        params['paths']['ruleset'] = os.path.abspath(args.rule_set_path)

    if args.basechart_data_path:
        data_path = rel_path(os.path.join(args.basechart_data_path, "shape"))
    elif args.geotif_data_path:
        data_path = rel_path(os.path.join(args.geotif_data_path, "data"))
    elif args.elevation_data_path:
        data_path = rel_path(os.path.join(args.elevation_data_path, "data"))
    elif args.aml_data_path:
        data_path = rel_path(os.path.join(args.aml_data_path, "data"))
    elif args.enhanced_data_path:
        data_path = rel_path(args.enhanced_data_path)
    else:
        print('No data path', file=sys.stderr)
        sys.exit(1)

    params['paths']['data'] = data_path
    params['paths']['map'] = os.path.normpath(os.path.join(
        data_path, '..', 'map'))

    toml.dump(params, args.output)
