#!/bin/bash
#
#  Lars Schylberg, 2016-01-25
#
#  process_aml_layers.sh  
#
#  Purpose: Create mapserver files based on AML data
#           Handle day, dusk and night mode
#           Substitute colors, paths, msd and groups in template files 
#           according rules in color and group in the csv files.
#           
#           Read layer structure from a xxx_layer_groups.csv file.
#           where xxx stands for the AML type letter combination
#
#  Evaluate arguments
#
if [ $# != 5 ]
then
    echo
    echo Usage: $(basename $0) 
    echo '      aml_file=<aml_file>'
    echo '      color_table_csv=<color table file in csv format>'
    echo '      rule_path<path to the rule files>"'
    echo '      map_path=<the url to find the mapfile>' 
    echo '      debug=<yes|no (add debug option in mapfile)>'   
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
        color_table_csv=*)
            COLOR_TABLE_CSV=`echo $i | sed s/color_table_csv=//` ;;
        ct=*)
            COLOR_TABLE_CSV=`echo $i | sed s/ct=//` ;;
        rule_path=*)
            RULE_PATH=`echo $i | sed s/rule_path=//` ;;
        rp=*)
            RULE_PATH=`echo $i | sed s/rp=//` ;;    
        map_path=*)
            MAP_PATH=`echo $i | sed s/map_path=//` ;;            
        mp=*)
            MAP_PATH=`echo $i | sed s/mp=//` ;;  
        debug=*)
            DEBUG=`echo $i | sed s/debug=//` ;;
        d=*)
            DEBUG=`echo $i | sed s/d=//` ;;
        *)
            echo ""
            echo "Unrecognized option: $i"
            echo "Options: "
            echo "  aml_file=<aml_file>"
            echo "  color_table_csv=<color table file in csv format> "
            echo "  rule_path<path to the rule files>"
            echo "  map_path=<the url to find the mapfile>"
            echo "  debug=<yes|no (add debug option in mapfile)>" 
            echo ""
            exit 1
    esac
done
#
#  Check if files exists otherwise exit
#
if [ ! -f ${AML_FILE} ] ; then
    echo "Error - File is now found: ${AML_FILE}"
    exit 1
fi

if [ ! -f ${COLOR_TABLE_CSV} ] ; then
    echo "Error - Color table file is not found: ${COLOR_TABLE_CSV}"
    exit 1
fi

#
#  Determine the AML type
#  Third character shows which type it is
#
FILENAME=$(basename ${AML_FILE})
echo "Processing file $FILENAME"
AML_TYPE_LETTER=${FILENAME:2:1}    # third letter, count starts from 0

case "$AML_TYPE_LETTER" in
    C)
        AML_TYPE="CLB"
        AML_GROUP_TITLE="Contour Line Bathymetry" ;;
    E)
        AML_TYPE="ESB"
        AML_GROUP_TITLE="Environment Seabed & Beach" ;;
    L)
        AML_TYPE="LBO"
        AML_GROUP_TITLE="Large Bottom Objects" ;;
    M)
        AML_TYPE="MFF"
        AML_GROUP_TITLE="Maritime Foundation & Facilities" ;;
    R)
        AML_TYPE="RAL"
        AML_GROUP_TITLE="Routes Areas & Limits" ;;
    S)
        AML_TYPE="SBO"
        AML_GROUP_TITLE="Small Bottom Objects" ;;
    *)
        echo "Unknown AML layer type"
        exit 1
esac
#
#  Set the group variable to aml type
#
GROUP=${AML_TYPE}
#
#  Find rule file with layers for this AML type
#
LAYER_RULES="${RULE_PATH}/layer_rules/AML_${AML_TYPE}_layer_order.csv"
if [ ! -f $LAYER_RULES ] ; then
    echo "Couldn't find layer rule file:  AML_${AML_TYPE}_layer_order.csv"
    exit 1
fi
#
# Remove header first line in input file with the layer rules.
#
sed '1d' $LAYER_RULES > IF_CSV_temp.csv
#
#  Prepare final output file
#  Make sure map_path directory exists and create an empty mapfile
#
THEME=$(basename $COLOR_TABLE_CSV .csv)
echo "Theme: $THEME"
AML_FILE_NAME=$(basename $FILENAME .000)
#
#  Get filename for output file
#
mkdir -p ${MAP_PATH}/includes
FINAL_FILE=${MAP_PATH}/includes/${THEME}_${AML_FILE_NAME}.map   
if [ -f  $FINAL_FILE ] ; then
   /bin/rm $FINAL_FILE
fi
touch $FINAL_FILE
#
#   Handle the paths for the S57 aml csv files
#   Note: it seems like the aml_csv file for runtime have an abosolute path
#   The processing can be a relative path
#   The CSV files have been edited to fit the Swedish test data since features
#   and attributes where missing in the orignal onces that are located at
#   /usr/share/gdal/1.10
#   
AML_CSV_PROC=../resources/aml_csv_files
AML_CSV_RUNTIME=${MAP_PATH}/aml_csv_files
#
#  Make an associative array with colors based on the color CSV file
#
declare -A color
declare -A color_rgb
while IFS=, read -r name rgb hex;
do
    color["$name"]="$hex"
    color_rgb["$name"]="$rgb"
done < <(sed 's/, /,/g' "$COLOR_TABLE_CSV")
#
#  Set shape path to current diretory
#
SHAPEPATH="."

#
#  Extract feature and feature type from input csv file
#  special handling of the M_COVR layer 
#
while IFS=, read -r FEATURE FEATURE_TYPE LAYER_DESC; do

    if [ "${FEATURE_TYPE}" == "poly" ] ; then  
        FT="POLYGON"
    fi
    if [ "${FEATURE_TYPE}" == "line" ] ; then 
        FT="LINESTRING"
    fi
        if [ "${FEATURE_TYPE}" == "point" ]; then 
        FT="POINT"
    fi
    
    FEATURE_USC=${FEATURE// /_}
    FEATUREandTYPE=${FEATURE_USC}-${FEATURE_TYPE}_AML_${AML_TYPE}
    echo ""
    echo "FEATURE $FEATURE  FEATURE_TYPE: $FEATURE_TYPE FEATUREandTYPE: $FEATUREandTYPE "
    
    NUM=$(ogrinfo -ro --config "S57_PROFILE" "aml" --config S57_CSV $AML_CSV_PROC ${AML_FILE} -sql "SELECT * FROM '${FEATURE}' WHERE OGR_GEOMETRY='$FT'" | grep 'Feature Count' | awk -F: '{print $2}' | sed -e 's/^[ \t]*//')
    
    #
    #  special case for SOUNDG since this is a 3D Multi Point Geometry type - it shows allways 1 feature 
    #
    if [ "$FEATURE" == "SOUNDG" ] ; then
        NUM=$(ogrinfo -ro --config "S57_PROFILE" "aml" --config S57_CSV $AML_CSV_PROC ${AML_FILE} -sql "SELECT * FROM SOUNDG" | grep 'Feature Count' | awk -F: '{print $2}' | sed -e 's/^[ \t]*//')
    fi
    echo "Number of features found in $FEATURE layer: $NUM"
    
    if [ "$NUM" -gt "0" ]; then
        # Check if template file template is available
        TEMPLATE=../resources/templates/aml_templates/${AML_TYPE}/${FEATUREandTYPE}_inc_template.map

        if [ -f $TEMPLATE ]; then
            echo "Process template $TEMPLATE"
 
            sed "s#{AML_PATH}#${AML_FILE}#g ; \
            s/{GROUP}/${GROUP}/g ; \
            s/{wms_group_title}/$AML_GROUP_TITLE/g ; \
            s/{LAYER_DESC}/${LAYER_DESC}/g ; \
            s/{NODTA}/${color[NODTA]}/g ; \
            s/{CURSR}/${color[CURSR]}/g ; \
            s/{CHBLK}/${color[CHBLK]}/g ; \
            s/{CHGRD}/${color[CHGRD]}/g ; \
            s/{CHGRF}/${color[CHGRF]}/g ; \
            s/{CHRED}/${color[CHRED]}/g ; \
            s/{CHGRN}/${color[CHGRN]}/g ; \
            s/{CHYLW}/${color[CHYLW]}/g ; \
            s/{CHMGD}/${color[CHMGD]}/g ; \
            s/{CHMGF}/${color[CHMGF]}/g ; \
            s/{CHBRN}/${color[CHBRN]}/g ; \
            s/{CHWHT}/${color[CHWHT]}/g ; \
            s/{SCLBR}/${color[SCLBR]}/g ; \
            s/{CHCOR}/${color[CHCOR]}/g ; \
            s/{LITRD}/${color[LITRD]}/g ; \
            s/{LITGN}/${color[LITGN]}/g ; \
            s/{LITYW}/${color[LITYW]}/g ; \
            s/{ISDNG}/${color[ISDNG]}/g ; \
            s/{DNGHL}/${color[DNGHL]}/g ; \
            s/{TRFCD}/${color[TRFCD]}/g ; \
            s/{TRFCF}/${color[TRFCF]}/g ; \
            s/{LANDA}/${color[LANDA]}/g ; \
            s/{LANDF}/${color[LANDF]}/g ; \
            s/{CSTLN}/${color[CSTLN]}/g ; \
            s/{SNDG1}/${color[SNDG1]}/g ; \
            s/{SNDG2}/${color[SNDG2]}/g ; \
            s/{DEPSC}/${color[DEPSC]}/g ; \
            s/{DEPCN}/${color[DEPCN]}/g ; \
            s/{DEPDW}/${color[DEPDW]}/g ; \
            s/{DEPMD}/${color[DEPMD]}/g ; \
            s/{DEPMS}/${color[DEPMS]}/g ; \
            s/{DEPVS}/${color[DEPVS]}/g ; \
            s/{DEPIT}/${color[DEPIT]}/g ; \
            s/{RADHI}/${color[RADHI]}/g ; \
            s/{RADLO}/${color[RADLO]}/g ; \
            s/{ARPAT}/${color[ARPAT]}/g ; \
            s/{NINFO}/${color[NINFO]}/g ; \
            s/{RESBL}/${color[RESBL]}/g ; \
            s/{ADINF}/${color[ADINF]}/g ; \
            s/{RESGR}/${color[RESGR]}/g ; \
            s/{SHIPS}/${color[SHIPS]}/g ; \
            s/{PSTRK}/${color[PSTRK]}/g ; \
            s/{SYTRK}/${color[SYTRK]}/g ; \
            s/{PLRTE}/${color[PLRTE]}/g ; \
            s/{APLRT}/${color[APLRT]}/g ; \
            s/{UINFD}/${color[UINFD]}/g ; \
            s/{UINFF}/${color[UINFF]}/g ; \
            s/{UIBCK}/${color[UIBCK]}/g ; \
            s/{UIAFD}/${color[UIAFD]}/g ; \
            s/{UINFR}/${color[UINFR]}/g ; \
            s/{UINFG}/${color[UINFG]}/g ; \
            s/{UINFO}/${color[UINFO]}/g ; \
            s/{UINFB}/${color[UINFB]}/g ; \
            s/{UINFM}/${color[UINFM]}/g ; \
            s/{UIBDR}/${color[UIBDR]}/g ; \
            s/{UIAFF}/${color[UIAFF]}/g ; \
            s/{OUTLW}/${color[OUTLW]}/g ; \
            s/{OUTLL}/${color[OUTLL]}/g ; \
            s/{RES01}/${color[RES01]}/g ; \
            s/{RES02}/${color[RES02]}/g ; \
            s/{RES03}/${color[RES03]}/g ; \
            s/{BKAJ1}/${color[BKAJ1]}/g ; \
            s/{BKAJ2}/${color[BKAJ2]}/g" \
            $TEMPLATE >> $FINAL_FILE  
            printf "Done with template: %s\n" $TEMPLATE
        else
            printf "Template file missing: %s\n" $TEMPLATE
        fi
    fi    
done < IF_CSV_temp.csv  
#
#  Include Legend and process colors
#  
#LEGEND_FILE=../resources/templates/aml_templates/Legend_inc_template.map
#if [ -f $LEGEND_FILE ]; then
#    echo ""
#    echo "Process Legend"
# 
#    sed "s/{SNDG1}/${color[SNDG1]}/g ; \
#         s/{SNDG2}/${color[SNDG2]}/g ; \
#         s/{DEPDW}/${color[DEPDW]}/g" \
#    $LEGEND_FILE >> $FINAL_FILE  
#else
#    printf "Legend template file missing: %s\n" $LEGEND_FILE
#fi

# clean up
/bin/rm IF_CSV_temp.csv

echo $AML_TYPE
