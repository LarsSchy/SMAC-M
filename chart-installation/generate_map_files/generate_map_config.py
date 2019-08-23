#!/usr/bin/env python
"""Generate a mapserver configuration for different kinds of geographical data.

The resulting mapserver configuration will be put in the folder 'map' in the
same folder as the geographical data."""

from __future__ import print_function

import argparse
from enum import Enum
import os
import sys
import toml

from mapgen.basechart import generate_basechart_config
from mapgen.generate_symbolset import symbolsets, generate_symbolset
from utils import dirutils
from utils.ruleutils import create_layer_rules, create_color_rules

RESOURCES_PATH = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(__file__), 'resources')
    )
)


class Format(Enum):
    Chart = 'chart'
    BaseChart = 'basechart'
    GeoTIF = 'geotif'
    Elevation = 'elevation'
    AML = 'aml'

    def __str__(self):
        return self.value


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'config_file',
        help='Chart configuration in TOML format',
    )
    parser.add_argument(
        'format',
        metavar='format',
        choices=list(Format),
        type=Format,
        help='Format of data: {%(choices)s} (Default: %(default)s)',
        nargs='?',
        default=Format.Chart.value,
    )
    parser.add_argument(
        '--force', '-f', '--force-overwrite',
        action='store_true',
        help="Force overwrite the rule set at RULE_SET_PATH"
    )

    try:
        args = parser.parse_args()
        args.base_dir = os.path.dirname(args.config_file)
        args.config = toml.load(args.config_file)
    except Exception as err:
        parser.print_help()
        print(str(err), file=sys.stderr)
        sys.exit(1)

    return args


def config_relative(path, args):
    return os.path.abspath(os.path.normpath(os.path.join(args.base_dir, path)))


if __name__ == '__main__':
    args = parse_arguments()

    debug = args.config.get('debug', False)

    try:
        data_path = args.config['paths']['data']
    except KeyError:
        print('Data path missing from configuration file', file=sys.stderr)
        sys.exit(1)

    point_table = args.config.get('point_table', 'Simplified')
    if 'tablename' in args.config:
        print('WARNING: `tablename` configuration option is deprecated. '
              'Use point_table instead\n')
        point_table = args.config['tablename']

    area_table = args.config.get('area_table', 'Plain')

    data_path = config_relative(data_path, args)

    map_path = args.config['paths'].get('map')

    rule_set_path = args.config['paths'].get('ruleset')

    color_tables_exist =os.path.join(rule_set_path, 'color_table')

    chartsymbols = args.config['paths'].get('chartsymbols')
    
    displaycategory = args.config.get('displaycategory',
                                      'Standard').split(',')
    displaycategory += ['Displaybase']

    topmar_type = args.config.get('topmark_type', 'rigid').lower()
    if topmar_type == 'rigid':
        os.environ['TOPMAR_FLOATING'] = ''
    elif topmar_type == 'floating':
        os.environ['TOPMAR_FLOATING'] = '1'
    else:
        print('topmark_type must be either floating or rigid')
        sys.exit(2)

    if args.format is Format.Chart:
        layer_definitions_exist = dirutils.does_layer_rules_exist(
            rule_set_path)

        # TODO: Let this script run from anywhere and skip the chdir
        os.chdir(os.path.dirname(__file__))
        print("\n=========================================================")
        print("   Configuration variables")
        print("data_path: %s" % data_path)
        print("rule_set_path: %s" % rule_set_path)
        print("RESOURCES_PATH: %s" % RESOURCES_PATH)
        print("point_table: %s" % point_table)
        print("area_table: %s" % area_table)
        print("debug: %s" % debug)
        print("force: %s" % args.force)
        print("map_path: %s" % map_path)
        print("displaycategory:%s" % displaycategory)
        print("chartsymbols: %s" % chartsymbols)
        print("layer_definitions_exist : %s " % layer_definitions_exist)
        print("=========================================================\n")
        generate_basechart_config(data_path, map_path, rule_set_path,
                                  RESOURCES_PATH, args.force,
                                  debug, point_table, area_table,
                                  displaycategory, chartsymbols)
    else:
        print('Data format "{}" has not yet been ported to the configuration '
              'file. Use the old script to generate your mapfiles'
              .format(args.format),
              file=sys.stderr)
        sys.exit(1)

    # TODO we should manage creating or not symbolset.
    print("Generating symbolset ...")
    for symbolset in symbolsets:
        generate_symbolset(symbolset, os.path.join(map_path, 'symbols'), False,chartsymbols)
