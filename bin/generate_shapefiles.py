#!/usr/bin/env python3
"""Convert an S57 chart to shapefile."""
import argparse
import os
import subprocess
import sys
import toml


def config_relative(path, args):
    return os.path.abspath(os.path.normpath(os.path.join(args.base_dir, path)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'config_file',
        help='Chart configuration in TOML format',
    )

    try:
        args = parser.parse_args()
        args.base_dir = os.path.dirname(args.config_file)
        args.config = toml.load(args.config_file)
    except Exception as err:
        parser.print_help()
        print(str(err), file=sys.stderr)
        sys.exit(1)

    try:
        chart_path = config_relative(args.config['paths']['chart'], args)
    except KeyError:
        print('Chart path missing from configuration file', file=sys.stderr)
        sys.exit(1)

    try:
        data_path = config_relative(args.config['paths']['data'], args)
    except KeyError:
        print('Data path missing from configuration file', file=sys.stderr)
        sys.exit(1)

    # TODO: Convert the actual script to python
    os.chdir(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '../chart-installation/data_files_conversion/shp_s57data'
    ))
    return subprocess.call(['bash', './generateShapefile.sh',
                            chart_path, data_path])


if __name__ == '__main__':
    sys.exit(main())
