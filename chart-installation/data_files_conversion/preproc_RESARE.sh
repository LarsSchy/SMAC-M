#!/bin/sh
#
#  JOIN polygons in RESARE layers
#
ORIG_FILE=${1}.shp
TARGET_FILE=${1}-U.shp
TABLE=$1
#
ogr2ogr ${SHP_DIR}/${CL}/${TARGET_FILE} ${SHP_DIR}/${CL}/${ORIG_FILE} \
    -dialect SQLITE -sql \
    "SELECT ST_union(geometry), 
 CATREA, RESTRN, INFORM, NINFOM, PERSTA, PEREND, SCAMIN 
  FROM '`basename $TABLE`' group by CATREA, RESTRN, INFORM"

