# -*- coding: utf-8 -*-
# by Will Kamp <manimaul!gmail.com>
# use this anyway you want

# Add Mapserver symbolset fil creation
# Simon Mercier

# python3 gen_symbolset.py [day|dark|dusk] [output_directory]

from __future__ import print_function

import os
from subprocess import call
import xml.etree.ElementTree as etree

from wand.image import Image

from .symbol import VectorSymbol, Pattern

__all__ = ['symbolsets', 'generate_symbolset', 'update_file']

here = os.path.dirname(__file__)

symbolsets = ('day', 'dusk', 'dark')


def generate_symbolset(symboltype, output_directory, force_update,OCPN_lookuptable):
    if symboltype == "day":
        OCPN_source_symbol_file = "rastersymbols-day.png"
    elif symboltype == "dark":
        OCPN_source_symbol_file = "rastersymbols-dark.png"
    elif symboltype == "dusk":
        OCPN_source_symbol_file = "rastersymbols-dusk.png"

    update_file(OCPN_source_symbol_file, force=force_update)
    OCPN_source_symbol_file = os.path.join(here, OCPN_source_symbol_file)

    # Init variables
    # OCPN_lookuptable = "../resources/chartsymbols/chartsymbols_S57.xml"
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

    root = etree.parse(os.path.join(here, OCPN_lookuptable))

    with Image(filename=OCPN_source_symbol_file) as source_symbols:
        base_path = '{}/symbols-{}/'.format(
            output_directory, symboltype)
        for symEle in root.iter('symbol'):
            name = symEle.find('name').text
            btmEle = symEle.find('bitmap')
            if btmEle is not None:
                locEle = btmEle.find("graphics-location")
                width = int(btmEle.attrib['width'])
                height = int(btmEle.attrib['height'])
                x = locEle.attrib["x"]
                y = locEle.attrib["y"]
                print("creating: %s" % (name), end='\r', flush=True)
                # imagemagick to the rescue
                left = int(x)
                top = int(y)
                right = left + int(width)
                bottom = top + int(height)
                with source_symbols[left:right, top:bottom] as symbol:
                    symbol_path = '{}/{}.png'.format(
                        base_path, name)
                    symbol.save(filename=symbol_path)

                str_to_add = symbol_template.replace("[symname]", name)
                f_symbols.write(str_to_add)

        for symEle in root.iter("line-style"):
            symbol = VectorSymbol(symEle)
            if symbol is not None:
                f_symbols.write(symbol.as_symbol)

        for symEle in root.iter("pattern"):
            symbol = Pattern.from_element(symEle)
            if symbol is not None:
                symbol.generate_bitmap(source_symbols, base_path)
                f_symbols.write(symbol.as_symbol(symboltype))

    # Include original symbols file
    f_symbols.write("""

    INCLUDE "symbols/symbols.sym"
    """)

    f_symbols.write("\nEND")
    f_symbols.close()


def update_file(file, force=False):
    url = "https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/"  # noqa
    if force or not os.path.exists(os.path.join(here, file)):
        call(["wget", url + file, "-O", os.path.join(here, file)])
