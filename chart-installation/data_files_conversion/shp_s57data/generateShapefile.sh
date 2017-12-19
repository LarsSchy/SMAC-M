#!/bin/bash
# Autor : Simon Mercier
#         Mapgears (www.mapgears.com)

# NOTE 1: Need to install gdal-bin 1.11 or more and sqlite3 package on your server
# NOTE 2: Need to compile gdal to support spatialite package.  see readme for instructions

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

# IMPORTANT for Depth data SOUNDG,POINT,  recode_by_dssi is important for duch encoding
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
mkdir -p $CATPATH/shp_template
wget https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/s57objectclasses.csv -O s57objectclasses.csv
wget https://raw.githubusercontent.com/OpenCPN/OpenCPN/master/data/s57data/s57attributes.csv -O s57attributes.csv

# Step 2
# we need to build an S-57 object list.  
# Run gen_Obj.py script to build this file
python gen_obj.py

# NOTE: This will create objlist.txt use in loop 

# Step 3
#We need to copy shapefiles template into all map navigation purpose
# This will garantied us to have all field used in IHO standard define 
# in look up OpenCPN file
python gen_shp_template.py ./

find shp_template/ -name '*' > /tmp/FILELIST
while read _FILE
do
    echo Processing $_FILE
    filename=`echo $(basename $_FILE)`
    cp $_FILE ${CATPATH}1/CL1_${filename}
    cp $_FILE ${CATPATH}2/CL2_${filename}
    cp $_FILE ${CATPATH}3/CL3_${filename}
    cp $_FILE ${CATPATH}4/CL4_${filename}
    cp $_FILE ${CATPATH}5/CL5_${filename}
    cp $_FILE ${CATPATH}6/CL6_${filename}

done < /tmp/FILELIST

# Step 4
# generate catalogues of S-57 source dataset 
find $ENCPATH/ -name *.000 > $TMPPATH/FILELIST

while read _FILE
do
    echo Processing $_FILE

    #usage type aus dem dateinamen (3. Stelle) ermitteln
    filename=`echo $(basename $_FILE)`
    usage=`echo ${filename:2:1}`	

    #  This switche is to map in the same datasource directory data from 
    # Overview and Habour purpose http://ienc.openecdis.org/files/ProdSpec_IENC_2_3.pdf
    #  s57 data from 'Harbour'(5), Berthing(6) and 'River'(7) navigational purpose
    if [ "$usage" == "5" ]||[ "$usage" == "6" ]||[ "$usage" == "7" ];
    then
           echo "Switched for Harbour usage..."
           usage='5'
           shp='harbour'
    #  s57 data from 'Overview'(1) navigational purpose
    elif [ "$usage" == "1" ]
    then
       echo "Overview usage..."
       shp='overview'
    #  s57 data from  'Coastal'(3) navigational purpose
    elif [ "$usage" == "3" ]
    then
       echo "Coastal usage..."
       shp='coastal'
    #  s57 data from 'Approach'(4) navigational purpose
    elif [ "$usage" == "4" ]
    then
       echo "Approach usage..."
       shp='approach'
    #  s57 data from General(2) navigational purpose
    elif [ "$usage" == "2" ]
    then
       echo "Genaral usage..."
       shp='general'
    fi

    # loop each objfind in s-57 datasource directory
    while read _OBJ
        do
                IFS=',' read -a array <<< "$_OBJ"
                name="${array[0]}"
                type="${array[1]}"

                ## to minimize the output error, we add ogr filter.  If this clause is not 
                ## added, it's not an error cause corresponding type 
                ## from -nlt type will be add in output spatial table and others print as error type....
                if [ "$type" = "POINT" ]; then
                      where="-where PRIM=1"
                elif [ "$type" = "LINESTRING" ]; then
                      where="-where PRIM=2"
                elif [ "$type" = "POLYGON" ]; then
                      where="-where PRIM=3"
                fi
 
                # process only if object exist
                ogrinfo -ro $_FILE | grep "$name" > $TMPPATH/layers 
                lnr=$(cat $TMPPATH/layers | awk -F: '{print $1}')
                
                # 
                if [[ "$lnr" != "" ]]
                then
                        # name is case sensitive for mapping purpose and SQlite doesnt support case sensitive
                        ## We need to test with regex it and add '_lcase_' in table name for lcase s-57 objectclasse 
                        if ! [[ "$name" =~ [^a-z_] ]]; then
                            output_shp=${CATPATH}${usage}/CL${usage}_${name}_lcase_${type}.shp
                        else
                            output_shp=${CATPATH}${usage}/CL${usage}_${name}_${type}.shp
                        fi
                        
                        ## ogr2ogr s-57 to shapefiles
                        echo ogr2ogr -append -skipfailures -f ESRI Shapefile -lco FID=OGC_FID $output_shp $where $_FILE $name    
                        ogr2ogr -append -skipfailures -f "ESRI Shapefile" -lco FID=OGC_FID $output_shp $where $_FILE $name >> /tmp/errors 2>&1 

                        # add a special dataset to support Lignts signature...
                        if [[ "${name}" == "LIGHTS" ]]
                        then
                            cat=CL${usage}_${name}_${type}

                            echo ogr2ogr -sql "SELECT ${cat}.VALNMR as VALNMR, ${cat}.LITCHR as LITCHR, ${cat}.SIGGRP as SIGGRP, cast(${cat}.SIGPER as numeric(4,1)) as SIGPER, cast(${cat}.HEIGHT as numeric(4,1))  as HEIGHT, ${cat}.COLOUR as COLOUR, ${cat}.EXCLIT as EXCLIT,litchr_code.Meaning as Meaning,colour_code.Colour_code as Colour_cod FROM '${output_shp}'.${cat} LEFT JOIN 'litchr_code.csv'.litchr_code litchr_code ON ${cat}.LITCHR = litchr_code.ID LEFT JOIN 'colour_code.csv'.colour_code colour_code ON ${cat}.COLOUR = colour_code.ID" ${CATPATH}${usage}/CL${usage}_${name}_${type}_SIGNATURE.shp ${output_shp}


                             ogr2ogr -sql "SELECT ${cat}.VALNMR as VALNMR,  ${cat}.LITCHR as LITCHR, ${cat}.SIGGRP as SIGGRP, cast(${cat}.SIGPER as numeric(4,1)) as SIGPER, cast(${cat}.HEIGHT as numeric(4,1))  as HEIGHT, ${cat}.COLOUR as COLOUR, ${cat}.EXCLIT as EXCLIT,litchr_code.Meaning as Meaning,colour_code.Colour_code as Colour_cod FROM '${output_shp}'.${cat} LEFT JOIN 'litchr_code.csv'.litchr_code litchr_code ON ${cat}.LITCHR = litchr_code.ID LEFT JOIN  'colour_code.csv'.colour_code colour_code ON ${cat}.COLOUR = colour_code.ID" ${CATPATH}${usage}/CL${usage}_${name}_${type}_SIGNATURE.shp ${output_shp}

                        fi

                fi

    done < objlist.txt

done < $TMPPATH/FILELIST

