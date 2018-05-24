#!/bin/bash
# Description
#
# TODO : translate this script to python for portability
#
die () {
    echo >&2 "$@"
    exit 1
}

[ "$#" -eq 2 ] || die "2 argument are required, $# provided -> bash generateShapefiles.sh [ENC_source_path] [output_path]"

## Load local configs (edit this file to set your local input and output path settings, etc.)
## update the following paths for your local installation
 # ../S57_chart_updater/input/PEC-ALL-S57ENCs-Complete/20170630/ENC_ROOT/
ENCPATH=$1 # where to find ENC s57 source files
CATPATH=$2 # where to save sqlite database
TMPPATH=/tmp # tmp files

# IMPORTANT for Depth data SOUNDG,POINT,  recode_by_dssi is important for UTF8 encoding
export OGR_S57_OPTIONS=SPLIT_MULTIPOINT=ON,ADD_SOUNDG_DEPTH=ON,RECODE_BY_DSSI=ON
export S57_PROFILE

# Step 1
# create needed directories
mkdir -p $CATPATH/1
mkdir -p $CATPATH/2
mkdir -p $CATPATH/3
mkdir -p $CATPATH/4
mkdir -p $CATPATH/5
mkdir -p $CATPATH/6
wget https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/s57objectclasses.csv -O s57objectclasses.csv
wget https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/s57attributes.csv -O s57attributes.csv

# Step 2
# we need to build an S-57 object list.  
# Run gen_Obj.py script to build objlist.txt file used in loop
python3 gen_obj.py

# Step 3
# generate catalogues of S-57 source dataset 
find $ENCPATH/ -name *.000 > $TMPPATH/FILELIST

while read _FILE
do
    echo Processing $_FILE

    # The third pine on the file name indicate the navigation purpose usage.
    # This $usage variable will be used for files and directories mapping. 
    filename=`echo $(basename $_FILE)`
    usage=`echo ${filename:2:1}`

    # loop each objfind in s-57 datasource directory
    while read _OBJ
    do
        IFS=',' read -a array <<< "$_OBJ"
        name="${array[0]}"
        type="${array[1]}"

        # We will use the type definition proposed by OpenCPN to extract only data mapped by lookup table 
        # Because all datatypes are stored in the S-57 source file, we need to add where clause
        # to filter properly data in the ogr2ogr command line.
        if [ "$type" = "POINT" ]; then
            where="-where PRIM=1"
        elif [ "$type" = "LINESTRING" ]; then
            where="-where PRIM=2"
        elif [ "$type" = "POLYGON" ]; then
            where="-where PRIM=3"
        fi
 
        # We will process only if feature object exist in source S-57 file.
        ogrinfo -ro $where $_FILE "$name" | awk '/Feature Count: /{if ($3 > 0) print "'"$name"'"}' > $TMPPATH/layers 
        lnr=$(cat $TMPPATH/layers | awk -F: '{print $1}')
                
        # Now we can loop ...
        if [[ "$lnr" != "" ]]
        then
            # name is case sensitive for mapping purpose and SQlite doesnt support case sensitive
            ## We need to test with regex it and add '_lcase_' in table name for lcase s-57 objectclasse 
            if ! [[ "$name" =~ [^a-z_] ]]; then
                output_shp=${CATPATH}/${usage}/CL${usage}_${name}_lcase_${type}.shp
            else
                output_shp=${CATPATH}/${usage}/CL${usage}_${name}_${type}.shp
            fi
                        
            ## ogr2ogr s-57 to shapefiles
            echo ogr2ogr -append -skipfailures -f "ESRI Shapefile" -lco FID=OGC_FID $output_shp $where $_FILE $name    
            ogr2ogr -append -skipfailures -f "ESRI Shapefile" --config S57_PROFILE iw $output_shp $where $_FILE $name >> /tmp/errors 2>&1 

            # add a special dataset to support Lignts signature...
            if [[ "${name}" == "LIGHTS" ]]
            then
                cat=CL${usage}_${name}_${type}

                # using cast(${cat}.HEIGHT as numeric(30,5)) -> https://trac.osgeo.org/gdal/ticket/6803
                echo ogr2ogr -sql "SELECT ${cat}.VALNMR as VALNMR, ${cat}.LITCHR as LITCHR, ${cat}.SIGGRP as SIGGRP, cast(${cat}.SIGPER as numeric(4,1)) as SIGPER, cast(${cat}.HEIGHT as numeric(30,5))  as HEIGHT, ${cat}.COLOUR as COLOUR, ${cat}.EXCLIT as EXCLIT,litchr_code.Meaning as Meaning,colour_code.Colour_code as Colour_cod FROM '${output_shp}'.${cat} LEFT JOIN 'litchr_code.csv'.litchr_code litchr_code ON ${cat}.LITCHR = litchr_code.ID LEFT JOIN 'colour_code.csv'.colour_code colour_code ON ${cat}.COLOUR = colour_code.ID" ${CATPATH}${usage}/CL${usage}_${name}_${type}_SIGNATURE.shp ${output_shp}
                ogr2ogr -sql "SELECT ${cat}.VALNMR as VALNMR,  ${cat}.LITCHR as LITCHR, ${cat}.SIGGRP as SIGGRP, cast(${cat}.SIGPER as numeric(4,1)) as SIGPER, cast(${cat}.HEIGHT as numeric(30,5))  as HEIGHT, ${cat}.COLOUR as COLOUR, ${cat}.EXCLIT as EXCLIT,litchr_code.Meaning as Meaning,colour_code.Colour_code as Colour_cod FROM '${output_shp}'.${cat} LEFT JOIN 'litchr_code.csv'.litchr_code litchr_code ON ${cat}.LITCHR = litchr_code.ID LEFT JOIN  'colour_code.csv'.colour_code colour_code ON ${cat}.COLOUR = colour_code.ID" ${CATPATH}${usage}/CL${usage}_${name}_${type}_SIGNATURE.shp ${output_shp}
            fi
        fi
    done < objlist.txt
done < $TMPPATH/FILELIST

# Run script to build light sector shapefiles
# TODO: build a better integration.  Need modification on python script
python3 generate_light_sector.py ${CATPATH}/1/CL1_LIGHTS_POINT.shp 3000
python3 generate_light_sector.py ${CATPATH}/2/CL2_LIGHTS_POINT.shp 3000
python3 generate_light_sector.py ${CATPATH}/3/CL3_LIGHTS_POINT.shp 3000
python3 generate_light_sector.py ${CATPATH}/4/CL4_LIGHTS_POINT.shp 3000
python3 generate_light_sector.py ${CATPATH}/5/CL5_LIGHTS_POINT.shp 3000
python3 generate_light_sector.py ${CATPATH}/6/CL6_LIGHTS_POINT.shp 3000
