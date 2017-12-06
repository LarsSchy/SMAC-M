#!/bin/bash
#
#  Scritps to examine AML data and write a stub for the layer_groups file
#  that will be used in later scripts.
#  The layer_groups file is edited before it is used by adding the description
#  and reorder the layer order so that polygons are shown first
#
#   Lars Schylberg, 2016-01-19
#-----------------------------------------------------------------------
#  Evaluate arguments
#
if [ $# != 1 ]
then
    echo
    echo Usage: $(basename $0) 
    echo '      aml_file=<aml file>'  
    echo ' '
    exit 1
fi
#
#  parse input arguments
#
for i do
    case $i in
        aml_file=*)
            AML_FILE=`echo $i | sed s/aml_file=//` ;;
        aml=*)
            AML_FILE=`echo $i | sed s/aml=//` ;;        
        *)
            echo ""
            echo "Unrecognized option: $i"
            echo "Options: "
            echo "  aml_file=<aml_file>" 
            echo ""
            exit 1
    esac
done
#
#  Check if file exists otherwise exit
#
# AML_PATH_FILE=../../../aml/data/ENC_ROOT/${AML_FILE}

AML_PATH_FILE=${AML_FILE}

if [ ! -f ${AML_PATH_FILE} ] ; then
    echo "Error - File is now found: ${AML_FILE}"
    exit 1
fi
# AML_FILE=SWR0U700.000

AML_FILE_NAME=$(basename $AML_FILE)

AML_TYPE_LETTER=${AML_FILE_NAME:2:1}    # third letter, count starts from 0
case "$AML_TYPE_LETTER" in
    C)
        AML_TYPE="CLB" ;;
    E)
        AML_TYPE="ESB" ;;
    L)
        AML_TYPE="LBO" ;;
    M)
        AML_TYPE="MFF" ;;
    R)
        AML_TYPE="RAL" ;;                
    S)
        AML_TYPE="SBO" ;;
    *)
        echo "Unknown AML layer type"
        exit 1
esac
#
#  Set custom AML csv file
#
AML_CSV_PROC=../resources/aml_csv_files

OUTFILE=${AML_TYPE}_layer_groups.txt
if [ -f ${OUTFILE} ] ; then
    /bin/rm $OUTFILE
fi
touch $OUTFILE
#
ogrinfo -ro --config "S57_PROFILE" "aml" --config "S57_CSV" "$AML_CSV_PROC" ${AML_PATH_FILE} -summary -q | tail -n +2 |  awk -F: '{print $2}' | sed 's/(\w\+//g' | sed 's/)//' > layer.list
while read layer 
do
    stipped_layer=$(echo $layer | sed 's/ *$//')  # strip trailing blank
    echo ""
    echo "Analysing layer: : $stipped_layer"
    if [[ "$stipped_layer" !=  "SOUNDG Multi Point" ]] ; then
        NUM_POINTS=$(ogrinfo -ro --config S57_PROFILE aml --config "S57_CSV" "$AML_CSV_PROC" ${AML_PATH_FILE} -summary -sql "SELECT * FROM '${stipped_layer}' WHERE OGR_GEOMETRY='POINT'" | grep 'Feature Count' | awk -F: '{print $2}')
        printf "Number of point objects: %d in layer: %s\n" $NUM_POINTS "${stipped_layer}"
        if [ "$NUM_POINTS" -gt "0" ]; then
            printf "%s,point,%s,\n" "${stipped_layer}" "${AML_TYPE}" >> $OUTFILE
        fi
        NUM_LINES=$(ogrinfo -ro --config S57_PROFILE aml --config "S57_CSV" "$AML_CSV_PROC" ${AML_PATH_FILE} -summary -sql "SELECT * FROM '${stipped_layer}' WHERE OGR_GEOMETRY='LINESTRING' " | grep 'Feature Count' | awk -F: '{print $2}')
        printf "Number of line objects: %d in layer: %s\n" $NUM_LINES "${stipped_layer}"
        if [ "$NUM_LINES" -gt "0" ]; then
            printf "%s,line,%s,\n" "${stipped_layer}" "${AML_TYPE}"  >> $OUTFILE
        fi
        NUM_POLY=$(ogrinfo -ro --config S57_PROFILE aml --config "S57_CSV" "$AML_CSV_PROC" ${AML_PATH_FILE} -summary -sql "SELECT * FROM '${stipped_layer}' WHERE OGR_GEOMETRY='POLYGON'" | grep 'Feature Count' | awk -F: '{print $2}')
        printf "Number of polygon objects: %d in layer: %s\n" $NUM_POLY "${stipped_layer}"
        if [ "$NUM_POLY" -gt "0" ]; then
            printf "%s,poly,%s,\n" "${stipped_layer}" "${AML_TYPE}"   >> $OUTFILE
        fi
    else
        #
        #  special case for SOUNDG since this is a 3D Multi Point Geometry type - it shows allways 1 feature 
        #
        NUM=$(ogrinfo -ro --config "S57_PROFILE" "aml" --config "S57_CSV" "$AML_CSV_PROC" ${AML_PATH_FILE} -sql "select * from SOUNDG" | grep 'Feature Count' | awk -F: '{print $2}' | sed -e 's/^[ \t]*//')
        echo "Number of features found in ${stipped_layer} layer: $NUM"
        printf "SOUNDG,point,%s,\n" "${AML_TYPE}" >> $OUTFILE
    fi
done < layer.list    

echo ""
echo "The stub for layer cofiguration is created in file: $OUTFILE"
echo ""
