#!/usr/bin/env python3
"""Convert an S57 chart to shapefile."""
import argparse
from collections import ChainMap
import errno
import os
import subprocess
import sys
from tempfile import TemporaryDirectory
import toml


def config_relative(path, args):
    return os.path.abspath(os.path.normpath(os.path.join(args.base_dir, path)))


def get_dir_size(path):
    from os import scandir
    from collections import deque
    total = 0
    dirs = deque([path])
    while dirs:
        try:
            for entry in scandir(dirs.popleft()):
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir():
                        dirs.append(entry.path)
                    else:
                        total += entry.stat().st_size
                except OSError:
                    continue
        except OSError:
            continue
    return total


def get_free_space(path):
    from os import statvfs
    stat = statvfs(path)
    return stat.f_frsize * stat.f_bfree


def check_preconditions(data_path, tmp_path):
    usage = get_dir_size(data_path)
    free_space = get_free_space(tmp_path)
    if usage > free_space:
        print('Not enough space to create the shapefiles. Aborting...',
              file=sys.stderr)
        sys.exit(errno.ENOSPC)

    tmp_dev = os.stat(tmp_path).st_dev
    data_dev = os.stat(data_path).st_dev
    if tmp_dev != data_dev:
        print('Data and temp directory are on different devices. Aborting...',
              file=sys.stderr)
        sys.exit(errno.EXDEV)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'config_file',
        help='Chart configuration in TOML format',
    )
    interactivity = parser.add_mutually_exclusive_group()
    interactivity.add_argument(
        '--interactive', action='store_true',
        default=sys.stdout.isatty(), dest='interactive'
    )
    interactivity.add_argument(
        '--non-interactive', action='store_const',
        const=False, dest='interactive'
    )

    tmp_dir = None

    try:
        args = parser.parse_args()
        args.base_dir = os.path.dirname(args.config_file)
        args.config = toml.load(args.config_file)
    except Exception as err:
        parser.print_help()
        print(str(err), file=sys.stderr)
        return errno.EINVAL

    try:
        chart_path = config_relative(args.config['paths']['chart'], args)
    except KeyError:
        print('Chart path missing from configuration file', file=sys.stderr)
        return errno.EINVAL

    try:
        data_path = config_relative(args.config['paths']['data'], args)
    except KeyError:
        print('Data path missing from configuration file', file=sys.stderr)
        return errno.EINVAL

    try:
        tmp_path = config_relative(args.config['paths']['tmp'], args)
    except KeyError:
        tmp_path = data_path

    for path in (data_path, tmp_path):
        try:
            os.makedirs(path)
        except FileExistsError:
            pass

    use_tmp_path = not os.path.samefile(data_path, tmp_path)

    if use_tmp_path:
        check_preconditions(data_path, tmp_path)
        tmp_dir = TemporaryDirectory(dir=tmp_path)
        export_path = tmp_dir.name + '/export'
        os.mkdir(export_path)
    else:
        export_path = data_path

    interactive = sys.stdout.isatty()

    if interactive:
        stdout = sys.stdout
        stderr = sys.stderr
        env = os.environ
    else:
        stderr = subprocess.PIPE
        stdout = subprocess.PIPE
        env = ChainMap({'QUIET': '1'}, os.environ)

    try:
        # TODO: Convert the actual script to python
        os.chdir(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../chart-installation/data_files_conversion/shp_s57data'
        ))
        resp = subprocess.run(
            ['bash', './generateShapefile.sh', chart_path, export_path],
            stdout=stdout, stderr=stderr, env=env
        )

        if resp.returncode == 0 and use_tmp_path:
            with TemporaryDirectory(dir=tmp_path) as old_files:
                os.rename(data_path, old_files)
                os.rename(export_path, data_path)
        elif resp.returncode != 0 and not interactive:
            print('An error occured while converting the S57', file=sys.stdout)
            print('Standard out was:', file=sys.stdout)
            print(resp.stdout.decode('utf-8'), file=sys.stdout)
            print('Error out was:', file=sys.stderr)
            print(resp.stderr.decode('utf-8'), file=sys.stderr)

        return resp.returncode
    finally:
        if tmp_dir is not None:
            tmp_dir.cleanup()


if __name__ == '__main__':
    sys.exit(main())
