# SMAC-M   --- Smacm Map and Chart Manager

This project allows you to convert nautical dataset and display it with Mapserver. It include all 
utilities to convert data from S57 to a shapefiles and to create mapfiles for a Mapserver WMS service.
This package uses the a python script and bash scripts to build a complete mapfiles from a set 
of templates and styling information to enable display of nautical data in the format S57.
 
The package enables mapserver to display nautical charts in different color modes and with 
alternative color tables.  Currently only simplified S52 symbology is carried out. But future 
plans are to include paper chart symbology as a separate style. The package also contains tools 
to create AML mapfiles for Mapserver.
 
The data handling is carried out with the OGR package.  For performance reasons all S57 data is 
converted into shape format and every object type is split into separate files. Separate files are 
also created for point, line and polygon features

Furhter on a tool is provided to process tiff files and create mapfiles automaticly.

## Requirement

 * XMLStarlet (to create color tables)
 * ImageMagic (to create symbolset files)
 * GDAL/OGR (to convert S-57 source dataset)
 * Running Linux OS (Ubuntu 16.04 / Debian 8 tested)

## Convert S-57 dataset

Create a folder that contains all your S-57 files and run the conversion script by specifying 
input S-57 dataset files and output shapefiles

    cd  chart-installation/generate_map_files/scripts/
    python ./S57_to_Shape.py /data/S57-data /data/Chart_dir

## Generating Symbolset

To create symbolset used in generated mapfile, we used source files download from s57data 
directory of OpenCPN Repository.

1) Need to download latest version of source files.  Up to datThose files
    
    cd  chart-installation/generate_map_files/scripts/
    python ./gen_symbolset.py update

2) Create symbolset mapfile and generate all png image symbols. 

    python ./gen_symbolset.py [day|dusk|dark] [output_directory]


## Generating mapfiles

Display all available options

    python ./generate_map_config.py -h   ---  shows all options

Specify rules directory and shapefiles source directory

    python ./generate_map_config.py -rules ../resources/layer_rules/rules/ -basechartdata /data/Chart_dir

TODO (describe this commandline)

    pythpn ./generate_map_config.py  -rule-default-color IHO -rules ../resources/layer_rules/rules/ -basechartdata /data/Chart_dir


The mapfiles are placed in /data/Chart_dir along with the converted data.  Then You should be able
to test the configuration in the built in open layers viewer with:

[http://localhost/cgi-bin/mapserv?map=/data/Chart_dir/map/SeaChart_DAY_BRIGHT.map&SERVICE=WMS&REQUEST=Getmap&VERSION=1.1.1&LAYERS=SeaChart_DAY_BRIGHT&srs=EPSG:3006&BBOX=133870,5798110,1541520,7459340&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100][1]

NOTE: You should adjust to EPSG:3857 and a suitable BBOX for your data.


## General information

IENC (S-57) data is compiled for a variety of navigational purposes.  This project is built to
mainely support all of them.  First version will support the first 6 navigation purpose.
At the end, all of thos levels will be converte to mapfiles.

* 1 S57 Overview - For route planning and oceanic crossing.
* 2 S57 General - For navigating oceans, approaching coasts and route planning.
* 3 S57 Coastal - For navigating along the coastline, either inshore or offshore.
* 4 S57 Approach - Navigating the approaches to ports or mayor channels or through intricate or congested waters.
* 5 S57 Harbour - Navigating within ports, harbours, bays, rivers and canals, for anchorages.
* 6 S57 Berthing - Detailed data to aid berthing. 

The following directory structure is mandatory.  On each volume within an exchange set there must
be a root directory called ENC_ROOT.  Data is publish throught .000 source file and data update
are store into .001, .002 and so on.  OGR2OGR software is able to read all this data.

NL600021.000
NL600021.001
NL600021.002

A valid data set file must be uniquely identified world wide by its name.  The data set files are
named according to the specifications given below: 

```
 CCPRRRRR.EEE
 | | |    |
 | | |    |------------ EEE = update number
 | | |
 | | |----------------- RRRRR = waterway code and waterway distance (kilometre) or
 | |                            identification of the equivalent paper chart number
 | |
 | |------------------- P = navigational purpose
 | 
 |--------------------- CC = producer code 
```


