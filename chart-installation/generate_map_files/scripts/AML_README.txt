Test urls for AML charts

SWE6U700.000  
SWM6U700.000  
SWS0U700.000
SWC6U700.000  
SWL0U700.000  
SWR0U700.000

LBO

./process_aml_layers.sh aml=../../../aml/data/ENC_ROOT/SWL0U700.000 ct=../../../rules/color_tables/DAY_BRIGHT.csv su=http://localhost/cgi-bin/mapserv mp=/home/lars/Maps/SeaChart4/aml/map d=yes

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart4/aml/map/DAY_BRIGHT_SWL0U700.map
&SERVICE=WMS&REQUEST=GetMap&VERSION=1.1.1
&LAYERS=LBO&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart4/aml/map/DAY_BRIGHT_SWL0U700.map
&SERVICE=WMS&REQUEST=GetLegendGraphic&VERSION=1.1.1
&LAYERS=LBO&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=image/png&WIDTH=2000&HEIGHT=1100

SBO

./process_aml_layers.sh aml=../../../aml/data/ENC_ROOT/SWS0U700.000 ct=../../../rules/color_tables/DAY_BRIGHT.csv su=http://localhost/cgi-bin/mapserv mp=/home/lars/Maps/SeaChart4/aml/map d=yes

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart4/aml/map/DAY_BRIGHT_SWS0U700.map
&SERVICE=WMS&REQUEST=GetMap&VERSION=1.1.1
&LAYERS=SBO&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart4/aml/map/DAY_BRIGHT_SWS0U700.map
&SERVICE=WMS&REQUEST=GetLegendGraphic&VERSION=1.1.1
&LAYERS=SBO&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=image/png&WIDTH=2000&HEIGHT=1100

MFF

./process_aml_layers.sh aml=../../../aml/data/ENC_ROOT/SWM6U700.000 ct=../../../rules/color_tables/DAY_BRIGHT.csv su=http://localhost/cgi-bin/mapserv mp=/home/lars/Maps/SeaChart4/aml/map d=yes

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart4/aml/map/DAY_BRIGHT_SWM6U700.map
&SERVICE=WMS&REQUEST=GetMap&VERSION=1.1.1
&LAYERS=MFF&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart4/aml/map/DAY_BRIGHT_SWM6U700.map
&SERVICE=WMS&REQUEST=GetLegendGraphic&VERSION=1.1.1
&LAYERS=MFF&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=image/png&WIDTH=2000&HEIGHT=1100

RAL

./process_aml_layers.sh aml=../../../aml/data/ENC_ROOT/SWR0U700.000 ct=../../../rules/color_tables/DAY_BRIGHT.csv su=http://localhost/cgi-bin/mapserv mp=/home/lars/Maps/SeaChart4/aml/map d=yes

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart4/aml/map/DAY_BRIGHT_SWR0U700.map 
&SERVICE=WMS&REQUEST=GetMap&VERSION=1.1.1
&LAYERS=RAL&srs=EPSG:4326&BBOX=5.000000,53.000000,21.000000,61.008581
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart4/aml/map/DAY_BRIGHT_SWR0U700.map 
&SERVICE=WMS&REQUEST=GetLegendGraphic&VERSION=1.1.1
&LAYERS=RAL&srs=EPSG:4326&BBOX=5.000000,53.000000,21.000000,61.008581
&FORMAT=image/png&WIDTH=2000&HEIGHT=1100


NEW:

./process_aml_layers.sh \
aml=/home/lars/Maps/SeaChart/charts/aml/data/ENC_ROOT/SWR0U700.000 \
ct=/home/lars/Maps/SeaChart/charts/rules/color_tables/DAY_BRIGHT.csv \
rp=/home/lars/Maps/SeaChart6/chart-installation/generate_map_files/resources \
mp=/home/lars/Maps/SeaChart/charts/aml/map \
debug=yes

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart/charts/aml/map/AML_DAY_BRIGHT.map 
&SERVICE=WMS&REQUEST=GetMap&VERSION=1.1.1
&LAYERS=RAL&srs=EPSG:4326&BBOX=5.000000,53.000000,21.000000,61.008581
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart/charts/aml/map/AML_DAY_BRIGHT.map
&SERVICE=WMS&REQUEST=GetLegendGraphic
&VERSION=1.1.1&LAYER=RAL&srs=EPSG:4326&FORMAT=image/png

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart/charts/aml/map/AML_DAY_BRIGHT.map
&SERVICE=WMS&REQUEST=GetLegendGraphic&VERSION=1.1.1
&LAYER=RAL&srs=EPSG:4326&BBOX=5.000000,53.000000,21.000000,61.008581
&FORMAT=image/png&WIDTH=2000&HEIGHT=1100



================================================================================================================================================================================
CLB

./process_aml_layers.sh aml=../../../aml/data/ENC_ROOT/SWC6U700.000 ct=../../../rules/color_tables/DAY_BRIGHT.csv su=http://localhost/cgi-bin/mapserv mp=/home/lars/Maps/SeaChart4/aml/map d=yes

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart4/aml/map/DAY_BRIGHT_SWC6U700.map
&SERVICE=WMS&REQUEST=GetMap&VERSION=1.1.1
&LAYERS=CLB&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart4/aml/map/DAY_BRIGHT_SWC6U700.map
&SERVICE=WMS&REQUEST=GetLegendGraphic&VERSION=1.1.1
&LAYERS=CLB&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=image/png&WIDTH=2000&HEIGHT=1100

ESB


./process_aml_layers.sh aml=../../../aml/data/ENC_ROOT/SWE6U700.000 ct=../../../rules/color_tables/DAY_BRIGHT.csv su=http://localhost/cgi-bin/mapserv mp=/home/lars/Maps/SeaChart4/aml/map d=yes

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart4/aml/map/DAY_BRIGHT_SWE6U700.map
&SERVICE=WMS&REQUEST=GetMap&VERSION=1.1.1
&LAYERS=ESB&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart/charts/aml/map/DAY_BRIGHT_SWE6U700.map
&SERVICE=WMS&REQUEST=GetMap&VERSION=1.1.1
&LAYERS=ESB&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart/charts/aml/map/AML_DAY_BRIGHT.map&
&SERVICE=WMS&REQUEST=GetLegendGraphic&VERSION=1.1.1
&LAYERS=ESB&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=image/png&WIDTH=2000&HEIGHT=1100

####

RUN separate conversion:


./process_aml_layers.sh \
aml=/home/lars/Maps/SeaChart/charts/aml/data/ENC_ROOT/SWE6U700.000 \
ct=/home/lars/Maps/SeaChart/charts/rules/color_tables/DAY_BRIGHT.csv \
rp=/home/lars/Maps/SeaChart6/chart-installation/generate_map_files/resources \
mp=/home/lars/Maps/SeaChart/charts/aml/map \
debug=yes

./process_aml_layers.sh \
aml=/home/lars/Maps/SeaChart/charts/aml/data/ENC_ROOT/SWR0U700.000 \
ct=/home/lars/Maps/SeaChart/charts/rules/color_tables/DAY_BRIGHT.csv \
rp=/home/lars/Maps/SeaChart6/chart-installation/generate_map_files/resources \
mp=/home/lars/Maps/SeaChart/charts/aml/map \
debug=yes

How to examine the layers in each file:

./examine-AML-data_2.sh aml=/home/lars/Maps/SeaChart/charts/aml/data/ENC_ROOT/SWE6U700.000


http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart/charts/aml/map/AML_DAY_BRIGHT.map
&SERVICE=WMS&REQUEST=GetMap&VERSION=1.1.1
&LAYERS=ESB&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/SeaChart/charts/aml/map/AML_DAY_BRIGHT.map
&SERVICE=WMS&REQUEST=GetLegendGraphic&VERSION=1.1.1
&LAYERS=ESB&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=image/png&WIDTH=2000&HEIGHT=1100


==========================================================================

CLB

# Getmap with all layers

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/GE2015_5_1/map/DAY_BRIGHT_SWC6U700.map
&SERVICE=WMS&REQUEST=Getmap&VERSION=1.1.1
&LAYERS=CLB&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/GE2015_5_1/map/DUSK_SWC6U700.map
&SERVICE=WMS&REQUEST=Getmap&VERSION=1.1.1
&LAYERS=CLB&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100

# GetCapabilities

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/GE2015_5_1/map/DAY_BRIGHT_SWC6U700.map
&SERVICE=WMS
&REQUEST=GetCapabilities
&VERSION=1.1.1

# Getmap with individual layers

http://localhost/cgi-bin/mapserv?map=/home/lars/Maps/GE2015_5_1/map/DAY_BRIGHT_SWC6U700.map
&SERVICE=WMS&REQUEST=Getmap&VERSION=1.1.1
&LAYERS=DEPARE,DEPCNT,SOUNDG&srs=EPSG:4326&BBOX=15.5,56.0,16.0,56.25
&FORMAT=application/openlayers&WIDTH=2000&HEIGHT=1100


==============================================================================================


./generate_map_config.py -rules ~/Maps/SeaChart/charts -amldata ~/Maps/SeaChart/charts/aml/ -rule-default-color SWE -f > generate-2016-05-19-13-01.log




