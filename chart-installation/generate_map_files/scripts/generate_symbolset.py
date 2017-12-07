#!/usr/bin/env python
#-*- coding: utf-8 -*-
# by Will Kamp <manimaul!gmail.com>
# use this anyway you want

# Add Mapserver symbolset fil creation
# Simon Mercier 

# python gen_symbolset.py [day|dark|dusk] [output_directory]

from xml.dom.minidom import parseString
import os
import sys

if sys.argv[1]=="update":
    os.popen("wget https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/rastersymbols-day.png -O rastersymbols-day.png")
    os.popen("wget https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/rastersymbols-dark.png -O rastersymbols-dark.png")
    os.popen("wget https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/rastersymbols-dusk.png -O rastersymbols-dusk.png")
    os.popen("wget https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/chartsymbols.xml -O chartsymbols.xml")
    exit()            

if len(sys.argv) > 1:
    symboltype = sys.argv[1]
    output_directory = sys.argv[2]

    if symboltype == "day":
        OCPN_source_symbol_file = "rastersymbols-day.png"
    elif symboltype == "dark":
        OCPN_source_symbol_file = "rastersymbols-dark.png"
    elif symboltype == "dusk":
        OCPN_source_symbol_file = "rastersymbols-dusk.png"
    else:
        print("Usage : python generate_symbolsea.py [day|dark|dusk] [output_directory]")
        exit()     
else:
    print("Usage : python generate_symbolset.py [day|dark|dusk] [output_directory]")
    exit()

#Init variables
OCPN_lookuptable = "chartsymbols.xml"
symbolefile = "%s/symbols-%s.map" %(output_directory, symboltype)

#Create output directory
os.popen("mkdir -p %s/symbols-%s" %(output_directory, symboltype))

#Read lookup table
f = open(OCPN_lookuptable, "r")
lines = f.read()
f.close()

## our mapfile symbol template
symbol_template = """
SYMBOL
     NAME "[symname]"
     TYPE PIXMAP
     IMAGE "symbols-%s/[symname].png" 
END""" %(symboltype)

f_symbols = open(symbolefile,"w")

# Include original symbols file
f_symbols.write( "SYMBOLSET\nINCLUDE 'symbols/symbols.sym'\n") 

dom = parseString(lines)
for symEle in dom.getElementsByTagName("symbol"):
    name = symEle.getElementsByTagName("name")[0].firstChild.nodeValue
    btmEle = symEle.getElementsByTagName("bitmap")
    if len(btmEle) > 0:
        locEle = btmEle[0].getElementsByTagName("graphics-location")
        width = int( btmEle[0].attributes["width"].value )
        height = int( btmEle[0].attributes["height"].value )
        x = locEle[0].attributes["x"].value
        y = locEle[0].attributes["y"].value
        print "creating: %s" %(name)
        #imagemagick to the rescue
        cmd = "convert %s -crop %sx%s+%s+%s %s/symbols-%s/%s.png" %(OCPN_source_symbol_file, width, height, x, y, output_directory, symboltype, name)
        os.popen(cmd)
	str_to_add = symbol_template.replace( "[symname]",name )
        f_symbols.write( str_to_add )

f_symbols.write( "\nEND")
f_symbols.close()
