# Data for basic map service

Create a folder that contains all your S-57 files and run the conversion script by specifying 
input S-57 dataset files and output shapefiles

```
cd chart-installation/data_files_conversion
python3 ./S57_to_Shape.py [ENC_ROOT] [output_path]
```

# Generating mapfiles

Specify rules directory and shapefiles source directory.  The mapfiles are placed in /data/Chart_dir along with the converted data.

```
cd chart-installation/generate_map_files/scripts
python3 ./generate_map_config.py -rules ../resources/layer_rules/rules/ -basechartdata /data/Chart_dir
```
