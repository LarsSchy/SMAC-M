# Create service based on NOAA free data

Here's a process to install NOAA ENC web service

### Build dataset

1) Create a folder that contains all your S-57 files and run the conversion script by specifying 
input S-57 dataset files and output shapefiles

```
mkdir ../noaa_enc/
cd ../noaa_enc/
wget https://www.charts.noaa.gov/ENCs/All_ENCs.zip
unzip All_ENCs.zip
mkdir shp
```

2) Create config file

```
cd ../SMAC-M
python3 bin/generate_toml_config.py \
          --chart ../noaa_enc/ENC_ROOT \
          -rule-default-color IHO \
          --chartsymbols ./chart-installation/generate_map_files/resources/chartsymbols/chartsymbols_S57.xml \
          -enhancedchartdata ../noaa_enc/shp \
          --tablename Paper \
          --displaycategory Standard \
          --rule-set-path ./chart-installation/generate_map_files/resources/layer_rules/rules/ \
          -o configfile.toml
```

3) Convert source data to shapefiles

```
python3 bin/generate_shapefiles.py configfile.toml
```

### Generating mapfiles

This script will generate the NOAA ENC WMS service.  The mapfiles are placed in 
a new directory created by the script in `-enhancedchartdata` config option,  along 
with the converted data. In this example, it will be in `../noaa_enc/map`

```
python3 chart-installation/generate_map_files/generate_map_config.py configfile.toml
```

### Configure web service

Update variable on this URL to test your NOAA service:

http://[yourservername]/cgi-bin/mapserv?map=[your_path_on_enhancedchartdata_option]/map/SeaChart_DAY_BRIGHT.map&SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&FORMAT=application/openlayers&TRANSPARENT=true&LAYERS=default&WIDTH=1024&HEIGHT=1024&CRS=EPSG%3A3857&STYLES=&BBOX=-9069712.02694336%2C3649409.477939453%2C-9064820.05713379%2C3654301.4477490233
