# SMAC-M   --- Smacm Map and Chart Manager

Scripts to convert nautical data and display it with Mapserver

Utility to convert data from S57 to a shape files and to 
create mapfiles for a Mapserver WMS service

This package uses the a python script and bash scripts to build a
complete mapfiles from a set of templates and styling information to enable display of nautical data in the format S57.
 
The package enables mapserver to display nautical charts in different color modes and with alternative color tables.
 
Currently only simplified S52 symbology is carried out. But future plans are to include paper chart symbology as a separate style.
 
The data handling is carried out with the OGR package.  For performance reasons all S57 data is converted into shape format and every object type is split into separate files. Separate files are also created for point, line and polygon features

The package also contains tools to create AML mapfiles for Mapserver

Furhter on a tool is provided to process tiff files and create mapfiles automaticly

Disclaimer: The package has only been tested with Swedish S57 sofar.
The displayed chart are only intended to be used for planning, not navigation.

Usage

./generate_map_config.py -h shows all options

How to generate a mapfile configuration 

./generate_map_config.py -rules ../resources/rules/layer_rules -basechartdata /data/New_Seachart2
