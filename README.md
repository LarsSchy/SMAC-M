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

XMLStarlet should be installed to run the scripts to create color tables.

Disclaimer: The package has only been tested with Swedish S57 sofar.
The displayed chart are only intended to be used for planning, not navigation.
The package has been tested on linux Debian 8.

How TO:

First you should convert your data:

I have a folder that contains all S57 files in /data/S57-data
and I would like to build the converted files in /data/Chart_dir. 
So first I run the conversion script:

./S57_to_Shape.py /data/S57-data /data/Chart_dir

Second step is to generate the mapfile configuration files

./generate_map_config.py -h   ---  shows all options

Example:

./generate_map_config.py -rules ../resources/layer_rules/rules/ -basechartdata /data/Chart_dir

or 

./generate_map_config.py  -rule-default-color IHO -rules ../resources/layer_rules/rules/ -basechartdata /data/Chart_dir

The mapfiles are placed in /data/Chart_dir along with the converted data.

Then You should be able to test the configuration in the built in open layers viewer with:

http://localhost/cgi-bin/mapserv?map=/data/Chart_dir/map/SeaChart_DAY_BRIGHT.map
&SERVICE=WMS
&REQUEST=Getmap
&VERSION=1.1.1
&LAYERS=SeaChart_DAY_BRIGHT
&srs=EPSG:3006
&BBOX=133870,5798110,1541520,7459340
&FORMAT=application/openlayers
&WIDTH=2000
&HEIGHT=1100

You should adjust to EPSG:3857 and a suitable BBOX for your data.

Good Luck

