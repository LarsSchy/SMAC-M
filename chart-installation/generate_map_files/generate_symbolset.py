#!/usr/bin/env python3

import argparse
from mapgen.generate_symbolset import (
    generate_symbolset,
    symbolsets,
    update_file,
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--update', '-u',
                        help='Update the symbol definition files',
                        action='store_true')
    parser.add_argument('symbolset', help='Symbolset to generate',
                        choices=symbolsets + ('all',))
    parser.add_argument('destination', help='Dataset destination folder')

    args = parser.parse_args()

    update_file('chartsymbols.xml', force=args.update)
    if args.symbolset == 'all':
        for symbolset in symbolsets:
            generate_symbolset(symbolset, args.destination, args.update)
    else:
        generate_symbolset(args.symbolset, args.destination, args.update)
