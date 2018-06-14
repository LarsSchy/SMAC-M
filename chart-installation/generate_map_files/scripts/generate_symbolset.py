#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# by Will Kamp <manimaul!gmail.com>
# use this anyway you want

# Add Mapserver symbolset fil creation
# Simon Mercier

# python3 gen_symbolset.py [day|dark|dusk] [output_directory]

from __future__ import print_function

import argparse
import os
from subprocess import call
import xml.dom.minidom

from wand.image import Image


def generate_symbolset(symboltype, output_directory, force_update):
    if symboltype == "day":
        OCPN_source_symbol_file = "rastersymbols-day.png"
    elif symboltype == "dark":
        OCPN_source_symbol_file = "rastersymbols-dark.png"
    elif symboltype == "dusk":
        OCPN_source_symbol_file = "rastersymbols-dusk.png"

    update_file(OCPN_source_symbol_file, force=force_update)

    # Init variables
    OCPN_lookuptable = "chartsymbols.xml"
    symbolefile = "%s/symbols-%s.map" % (output_directory, symboltype)

    # Create output directory
    try:
        os.makedirs("%s/symbols-%s" % (output_directory, symboltype))
    except os.error:
        pass

    # our mapfile symbol template
    symbol_template = """
    SYMBOL
        NAME "[symname]"
        TYPE PIXMAP
        IMAGE "symbols-%s/[symname].png"
    END""" % (symboltype)

    f_symbols = open(symbolefile, "w")

    f_symbols.write("SYMBOLSET\n")

    dom = xml.dom.minidom.parse(OCPN_lookuptable)
    with Image(filename=OCPN_source_symbol_file) as source_symbols:
        for symEle in dom.getElementsByTagName("symbol"):
            name = symEle.getElementsByTagName("name")[0].firstChild.nodeValue
            btmEle = symEle.getElementsByTagName("bitmap")
            if len(btmEle):
                locEle = btmEle[0].getElementsByTagName("graphics-location")
                width = int(btmEle[0].attributes["width"].value)
                height = int(btmEle[0].attributes["height"].value)
                x = locEle[0].attributes["x"].value
                y = locEle[0].attributes["y"].value
                print("creating: %s" % (name), end='\r', flush=True)
                # imagemagick to the rescue
                left = int(x)
                top = int(y)
                right = left + int(width)
                bottom = top + int(height)
                with source_symbols[left:right, top:bottom] as symbol:
                    symbol_path = '{}/symbols-{}/{}.png'.format(
                        output_directory, symboltype, name)
                    symbol.save(filename=symbol_path)

                str_to_add = symbol_template.replace("[symname]", name)
                f_symbols.write(str_to_add)

        for symEle in dom.getElementsByTagName("line-style"):
            name = symEle.getElementsByTagName("name")[0].firstChild.nodeValue
            hpgl = symEle.getElementsByTagName("HPGL")
            if hpgl:
                hpgl = hpgl[0].firstChild.nodeValue
                vector = symEle.getElementsByTagName('vector')[0]
                origin = vector.getElementsByTagName('origin')[0]
                offset_x = int(origin.attributes['x'].value)
                offset_y = int(origin.attributes['y'].value)
                symbol = parse_vector_symbol(name, hpgl, offset_x, offset_y)
                f_symbols.write(symbol)

    # Include original symbols file
    f_symbols.write("""

    INCLUDE "symbols/symbols.sym"
    """)

    f_symbols.write("\nEND")
    f_symbols.close()


def parse_vector_symbol(name, hpgl, offset_x, offset_y):
    vector_template = """
    SYMBOL
        NAME "{symname}"
        TYPE VECTOR
        FILLED {filled}
        POINTS
        {points}
        END
    END"""

    filled = False
    points = []
    for instruction in hpgl.split(';'):
        if not instruction:
            continue

        command, args = instruction[:2], instruction[2:]
        if command in ('SP', 'SW'):
            # Select Pen
            # Set Width
            pass
        elif command in ('PD', 'PU'):
            # Pen Down
            # Pen Up
            if command == 'PU':
                points += [-99, -99]

            coordinates = map(int, args.split(','))

            for x, y in zip(coordinates, coordinates):
                points += [x - offset_x, y - offset_y]
        elif command == 'CI':
            # Circle
            pass
        elif command == 'FP':
            # Fill Polygon
            filled = True
        else:
            import warnings
            warnings.warn('Not implemented: ' + command)

    str_to_add = vector_template.format(symname=name,
                                        filled=filled,
                                        points=' '.join(map(str, points)))
    return str_to_add


def update_file(file, force=False):
    url = "https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/"  # noqa
    if force or not os.path.exists(file):
        call(["wget", url + file, "-O", file])


if __name__ == '__main__':
    symbolsets = ('day', 'dusk', 'dark')
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
