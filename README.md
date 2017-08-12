# SMAC-M   --- Smacm Map and Chart Manager

Scripts to convert nautical data and display it with Mapserver

Utility to convert data from S57 to a shape files and to 
create mapfiles for a Mapserver WMS service

The package also contains tool to create AML mapfiles for Mapserver

Furhter on the a tool is provided to process tiff files and 
create mapfiles automaticly

The package is built with python and bash scripts

Usage

./generate_map_config.py -h shows all options

How to generate a mapfile configuration 

./generate_map_config.py -rules ../resources/rules/layer_rules -basechartdata /data/New_Seachart2
