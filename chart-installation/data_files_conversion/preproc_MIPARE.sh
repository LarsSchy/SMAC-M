#!/bin/bash

ORIG_FILE=${1}.shp
TARGET_FILE=${1}-U.shp
TABLE=$1

ogr2ogr $TARGET_FILE $ORIG_FILE \
    -dialect SQLITE -sql "select ST_Union(Geometry), OBJNAM, INFORM, NINFOM
 FROM '`basename $TABLE`' GROUP BY OBJNAM, INFORM" 

