# SMAC-M   - Scripts for Map And Chart Manager

This project allows you to convert nautical dataset and display it with Mapserver. It include all 
utilities to convert data from S57 to a shapefiles and to create mapfiles for a Mapserver WMS service.
This package uses the a python script and bash scripts to build a complete mapfiles from a set 
of templates and styling information to enable display of nautical data in the format S57.
 
![S-57-overview](/doc/S-57-overview.png)
![S-57-boy](/doc/S-57-boy.png)

The package enables mapserver to display nautical charts in different color modes and with 
alternative color tables.  Currently only simplified S52 symbology is carried out. But future 
plans are to include paper chart symbology as a separate style. The package also contains tools 
to create AML mapfiles for Mapserver.
 
The data handling is carried out with the OGR package.  For performance reasons all S57 data is 
converted into shape format and every object type is split into separate files. Separate files are 
also created for point, line and polygon features

Furhter on a tool is provided to process tiff files and create mapfiles automaticly.

## Requirement

 * Your own S-57 dataset source files
 * XMLStarlet (to create color tables)
 * ImageMagic (to create symbolset files)
 * GDAL/OGR (to convert S-57 source dataset)
 * Running Linux OS (Ubuntu 16.04 / Debian 8 tested)
 * Up to date GDAL/OGR S-57 metadata
 * Python 3.5 with pipenv


```
sudo apt install python3 python3-pip python3-venv gdal-bin python3-gdal build-essential libgdal-dev imagemagick xmlstarlet
git clone https://github.com/LarsSchy/SMAC-M
```
 
## Python 3 virtual environment

A good way to run and test this tool is to create a development virtual 
environment available only for the active user.  Before running the scripts for 
the first time, you must install their dependencies. This project uses 
[Pipenv](https://docs.pipenv.org/) to manage its virtual environment.

After downloading a new version of the code, run `pipenv install` in the root
directory to install the bulk of the dependencies.

Due to the way GDAL works, it must be installed separately with the version that
matches the version of GDAL installed on the system. To install GDAL in the
virtual environment, run `pipenv run pip install "GDAL<=$(gdal-config --version)"`

Once the packages have been installed, use `pipenv shell` to activate the
environment.

```
cd ./SMAC-M
echo 'PATH="$HOME/.local/bin/:$PATH"' >>~/.bashrc
pip3 install --user pipenv
pipenv install
pipenv run pip install "GDAL<=$(gdal-config --version)"
pipenv shell
```

## Up to date GDAL/OGR

GDAL/OGR used OpenCPN configuration file to read and extract data from S-57 dataset. If you don't have up to date metadata file on your system, you will be unable to read all the data available in S-57 dataset. You have to make sure to update those files on your system to make run properly data converter script.  In [S-57 OGR driver](http://www.gdal.org/drv_s57.html) documentation said: _The S-57 reader depends on having two supporting files, s57objectclasses.csv, and s57attributes.csv available at runtime in order to translate features in an object class specific manner. These should be in the directory pointed to by the environment variable S57_CSV, **or in the current working directory**_

For your setup and future usage, be sure to find GDAL/OGR S-57 configuration file, and update them like this:

```
$ ogrinfo --version
GDAL 2.2.2, released ...
$ ls /usr/share/gdal/
2.2
```
Create up to date s57 object files in GDAL data folder `/usr/share/gdal/2.2/`
```
$ wget https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/s57objectclasses.csv
$ wget https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/s57attributes.csv
$ cp s57objectclasses.csv /usr/share/gdal/2.2/s57objectclasses_iw.csv
$ cp s57attributes.csv /usr/share/gdal/2.2/s57attributes_iw.csv
```
Add extra OGR environment variable on your system
```
export S57_PROFILE
```
To process sound depth points properly and other Multipoint dataset, you have to set OGR environment variable on your system
```
export OGR_S57_OPTIONS=SPLIT_MULTIPOINT=ON,ADD_SOUNDG_DEPTH=ON
```
You can test your setup by using `ogrinfo` and other `ogr2ogr` tools with S57 profile like this:
```
$ ogrinfo --config S57_PROFILE iw -ro ./datatest/US5OH10M/US5OH10M.000 | grep "SLOTOP"
48: SLOTOP
```

## Generating the mapfile

### Generate a configuration file

This configuration file contains the options for a particular map generation.
It is in [TOML](https://github.com/toml-lang/toml/wiki) format.

You can easily generate a configuration file with the `generate_toml_config.py`
script. 
This script accepts the same options as the legacy
`generate_map_config.py` and creates a toml file with these options.

```
 python3 bin/generate_toml_config.py \
     --chart ./shp_s57data/ENC_ROOT \
     -rule-default-color IHO \
     --chartsymbols ./chartsymbols_S57.xml \
     -enhancedchartdata ./shp_s57data/shp \
     --tablename Paper \
     --displaycategory Standard \
     --rule-set-path ../resources/layer_rules/rules/ \
     -o configfile.toml
```

If you prefer to create your configuration file manually, 
you can use [config.sample.toml](config.sample.toml) as a base.

For the rest of these instructions, 
the configuration file will be referred to as `configfile.toml`

### Convert S-57 dataset

This script will build all data needed for nautical charts map service 
based on OpenCPN configuration file 
and support light sectors layers. 

The script will create shapefiles for S-57 objects 
ONLY if data is found in your source files.

```
python3 bin/generate_shapefiles.py configfile.toml
```

This same script can be used whenever the S-57 dataset is updated 
to regenerate the shapefiles.


### Light sector

This project will automatically create lights sector shapefiles based on LIGHTS dataset when generating the shapefiles

![S-57-lioghts_sector](/doc/S-57-lights_sector.png)

In case you need to update Lights sector or change the default radius, you can simply run this script:

```
cd chart-installation/data_files_conversion/shp_s57data
python3 generate_light_sector.py [input_lights_shp_path] [radius]
  # NOTE 1: input shapefile must be named as *_LIGHTS_*.shp
  # NOTE 2: if radius = valnmr keyword, distance will be take from data
```

### Generating mapfiles

The mapfiles can be generated from the information in the configuration file.

```
python3 chart-installation/generate_map_files/generate_map_config.py configfile.toml
```

#### Enhanced data mapfile limitations

Working with enhanced data allows to create mapfiles from the chartsymbols.xml file. This file contains all the specification of all symbols of the IENC symbology and is provided by OpenCPN. The file provided by OpenCPN does contains a few errors or limitation that are not currently handled.

 - Layers are ordered by Display Priority. Layers with the same display priority
   are displayed in a undefined order. If a layer has lookups belonging to
   different display priorities, the entire layer is displayed at that priority.
 - The data files contain a MinScale / MaxScale information and this is not directly used. We currently separate in only 6 levels:
   - 2000000
   - 600000
   - 150000
   - 50000
   - 25000
 - Basic symbology is created from SY, TE, TX, LC, LS, AP and AC instructions.
   CS instructions are implemented as a series of these basic instructions
   subject to the following limitations:
   - TOPMAR does not check other features for floating or rigid platforms. 
     All top marks are displayed as rigid by default.
     You can choose to display all top marks as floating instead 
     by changing `topmark_style` from `rigid` to `floating` in the configuration file 
     or by setting the `TOPMARK_FLOATING` environment variable.
   - SYMINS does not attempt to use the instructions found in the features'
     SYMINS attribute. 
     All NEWOBJ features will use the generic symbolization
   - LEGLIN does not take into account the DISTANCE_TAGS value selected by the mariner 
     and does not display the course.
   - OWNSHP always symbolizes as the OWNSHP01 symbol.
   - SOUNDG are drawn as special MapServer labels 
     instead of Presentation Library instructions
   - SNDFRM: 
     All layers with a defined VALSOU field 
     are combined into a single layer
     that is drawn using the SOUNDG rules.
     It is not currently possible to exclude layers
     from this special layer.
   - LIGHTS only selects the color of the symbol.
     Light arcs are written directly to the mapfile.
   - DEPARE only takes into account the DRVAL2 attribute and renders a flat color.
   - DEPCNT does not draw the contour labels.
   - OBSTRN does not take into account the underwater hazard procedure 
     or low accuracy symbols, 
     and assumes a safety depth of 30 metres
   - WRECKS does not take into account the underwater hazard procedure 
     or low accuracy symbols, 
     and assumes a safety depth of 30 metres
 - Symbols in MapServer are anchored to the map in the center vs in the top-left corner for OpenCPN. This brings a disparity in the symbol placement when they are stacked together.
 - Current implementation stack levels as you zoom in so you get level 1 features and labels in level 2 maps.
 - Symbology can be created from vector and bitmaps. We are only supporting bitmap symbology for points and vector symbology for lines and polygons.
 - TOWERSxx symbols are present twice in the chartsymbols.xml. We only use the second one.
 - SOUNDG labels are set with FORCE TRUE. This make to many appear in the map at small scale.
 - Some layers are excluded from the map as they are useful in a WMS context. Right now only M_QUAL is excluded.
 - Some layers are exported as LINE instead of POLYGON
 - Some layers defined in the chartsymbols.xml are pointing to non-existing data columns:
   - BCNSPP layer (lookup #1781) uses BOYSHP == 1 Expression, but this field is not present. We replaced it by BCNDHP == 1.
   - BCNSPP layer (lookup #1784) uses CATLAM == 1 Expression, but this field is not present. We replaced it by CATSPM == 1.
   - LNDELV layer (lookup #2210) uses HEIGHT TX instruction, but this field is not present. The instruction was removed.
   - RADSTA layer (lookup #1222, #2340) uses COMCHA field for label, but this field is not present. We replaced it by OBJNAM.
   - RDOSTA layer (lookup #2350) uses DGPS field for label, but this field is not present. We replaced it by OBJNAM.
   - RESARE layer (lookup #164) uses SY(ESSARE01) and SY(PSSARE01) symbols, but those symbols are not present. They were removed.
   - TOPMAR layer uses OBJNAM field for label, but this field is not present
   - SOUNDG layer is in display-cat Other, it has been transfered to Standard

### Generating Symbolset

The symbols are automatically generated from the OpenCPN symbols 
when the mapfiles are updated.
They do not need to be generated manually

### Testing

Follow those steps to get mapserver up and running.
https://github.com/mapserver/mapserver/wiki/Install-mapserver-on-ubuntu-18.04-from-official-repository

Then You should be able to test the configuration in the built in open layers viewer with:

[http://localhost/cgi-bin/mapserv?map=/data/Chart_dir/map/SeaChart_DAY_BRIGHT.map&SERVICE=WMS&REQUEST=Getmap&VERSION=1.1.1&LAYERS=SeaChart_DAY_BRIGHT&srs=EPSG:3006&BBOX=133870,5798110,1541520,7459340&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100](http://localhost/cgi-bin/mapserv?map=/data/Chart_dir/map/SeaChart_DAY_BRIGHT.map&SERVICE=WMS&REQUEST=Getmap&VERSION=1.1.1&LAYERS=SeaChart_DAY_BRIGHT&srs=EPSG:3006&BBOX=133870,5798110,1541520,7459340&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100)

NOTE: You should adjust to EPSG:3857 and a suitable BBOX for your data.

### NOAA ENC service

The commands used to generate a basic NOAA ENC map service have been moved to 
[their separate readme](README.noaa.md).

##  General information

IENC (S-57) data is compiled for a variety of navigational purposes.  This project is built to
mainely support all of them.  First version will support the first 6 navigation purpose.
At the end, all of thos levels will be converte to mapfiles.

* 1 - Overview - For route planning and oceanic crossing.
* 2 - General - For navigating oceans, approaching coasts and route planning.
* 3 - Coastal - For navigating along the coastline, either inshore or offshore.
* 4 - Approach - Navigating the approaches to ports or mayor channels or through intricate or congested waters.
* 5 - Harbour - Navigating within ports, harbours, bays, rivers and canals, for anchorages.
* 6 - Berthing - Detailed data to aid berthing. 

The following directory structure is mandatory.  On each volume within an exchange set there must
be a root directory called ENC_ROOT.  Data is publish throught .000 source file and data update
are store into .001, .002 and so on.  OGR2OGR software is able to read all this data.

```
NL600021.000
NL600021.001
NL600021.002
```

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


