#!/bin/bash
#
#  Lars Schylberg, 2015-09-22
#
#  process_layer_colors.sh  
#
#  Purpose: Substitute colors, paths, msd and groups in template files 
#           according rules in color, group and msd csv files.
#
#  Evaluate arguments
#
if [ $# != 6 ]
then
    echo
    echo Usage: `basename $0` 
    echo '       chart_level=<level> (1-6)'
    echo '       color_table_csv=<color table file in csv format>'
    echo '       input_file_csv=<csv file with files and maxscaledenom>'
    echo '       maxscaledenom=<max scale denominator for the layer>'
    echo '       data_dir=<data directory>'
    echo '       target=<target directory>'
    echo ' '
    exit 1
fi
#
#  parse input arguments
#
for i do
    case $i in
        chart_level=*)
            CL=`echo $i | sed s/chart_level=//` ;;
        cl=*)
            CL=`echo $i | sed s/cl=//` ;;           
        color_table_csv=*)
            COLOR_TABLE_CSV=`echo $i | sed s/color_table_csv=//` ;;
        ct_csv=*)
            COLOR_TABLE_CSV=`echo $i | sed s/ct_csv=//` ;;
        input_file_csv=*)
            IF_CSV=`echo $i | sed s/input_file_csv=//` ;;
        if_csv=*)
            IF_CSV=`echo $i | sed s/if_csv=//` ;;           
        maxscaledenom=*)
            MSD=`echo $i | sed s/maxscaledenom=//` ;;
        msd=*)
            MSD=`echo $i | sed s/msd=//` ;;
        data_dir=*)
            DATA_DIR=`echo $i | sed s/data_dir=//` ;;
        d=*)
            DATA_DIR=`echo $i | sed s/d=//` ;;
        target=*)
            TARGET_DIR=`echo $i | sed s/target=//` ;;
        t=*)
            TARGET_DIR=`echo $i | sed s/t=//` ;;
        *)
            echo ""
            echo "Unrecognized option: $i"
            echo "Options: "
            echo "       chart_level=<level> (1-6) "
            echo "       color_table_csv=<color table file in csv format>"
            echo "       input_file_csv=<csv file with files and maxscaledenom>"
            echo "       maxscaledenom=<max scale denominator for the layer>"
            echo "       data_dir=<data directory>"
            echo "       target=<target directory>"
            echo ""
            exit 1
    esac
done
#
##  Make an associative array with colors based on the color CSV file
#
declare -A color
declare -A color_rgb
while IFS=, read -r name rgb hex;
do
    color["$name"]="$hex"
    color_rgb["$name"]="$rgb"
done < <(sed 's/, /,/g' "$COLOR_TABLE_CSV")
#
# Remove header first line in input file and store in
# a temporary file. $RANDOM generates a different file for each thread running this script.
#
TEMP_CSV_FILE="IF_CSV_${RANDOM}.csv"
sed '1d' $IF_CSV > $TEMP_CSV_FILE
#
##  Prepare final output file
#
THEME=`basename $COLOR_TABLE_CSV .csv`
echo "Theme: $THEME"
#
mkdir -p ${TARGET_DIR}/includes
FINAL_FILE=${TARGET_DIR}/includes/${THEME}_layer${CL}_inc.map   
if [ -f  $FINAL_FILE ] ; then
   /bin/rm $FINAL_FILE
fi
touch $FINAL_FILE
#
#  process each layer in the list CHART_LAYERS if it exists as real layer
#  update info in template and append the real include mapfile
#  The MSD is set in the command line argument now and not from the csv-file
#

while IFS=, read -r FEATURE GROUP;do
    printf 'Layer: %s Processing feature: %s:\n' ${CL} ${FEATURE}
    if [ -f ${DATA_DIR}/${CL}/CL${CL}-${FEATURE}.shp ]; then
        BASE="CL${CL}-${FEATURE}"
        TEMPLATE=../resources/templates/basechart_templates/${FEATURE}_template_color.map
        if [ -f $TEMPLATE ]; then 
            sed "s/{CL}/${CL}/g ; \
            s/{PATH}/${CL}\/${BASE}/g ; \
            s/{PATH_OGR}/${CL}\/${BASE}.shp/g ; \
            s/{OGR_SQL_LAYER}/${BASE}/g ; \
            s/{MAXSCALE}/${MSD}/g; \
            s/{GROUP}/${GROUP}/g; \
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
            s/{BKAJ2}/${color[BKAJ2]}/g ; \
            s/{NODTA_rgb}/${color_rgb[NODTA]}/g ; \
            s/{CURSR_rgb}/${color_rgb[CURSR]}/g ; \
            s/{CHBLK_rgb}/${color_rgb[CHBLK]}/g ; \
            s/{CHGRD_rgb}/${color_rgb[CHGRD]}/g ; \
            s/{CHGRF_rgb}/${color_rgb[CHGRF]}/g ; \
            s/{CHRED_rgb}/${color_rgb[CHRED]}/g ; \
            s/{CHGRN_rgb}/${color_rgb[CHGRN]}/g ; \
            s/{CHYLW_rgb}/${color_rgb[CHYLW]}/g ; \
            s/{CHMGD_rgb}/${color_rgb[CHMGD]}/g ; \
            s/{CHMGF_rgb}/${color_rgb[CHMGF]}/g ; \
            s/{CHBRN_rgb}/${color_rgb[CHBRN]}/g ; \
            s/{CHWHT_rgb}/${color_rgb[CHWHT]}/g ; \
            s/{SCLBR_rgb}/${color_rgb[SCLBR]}/g ; \
            s/{CHCOR_rgb}/${color_rgb[CHCOR]}/g ; \
            s/{LITRD_rgb}/${color_rgb[LITRD]}/g ; \
            s/{LITGN_rgb}/${color_rgb[LITGN]}/g ; \
            s/{LITYW_rgb}/${color_rgb[LITYW]}/g ; \
            s/{ISDNG_rgb}/${color_rgb[ISDNG]}/g ; \
            s/{DNGHL_rgb}/${color_rgb[DNGHL]}/g ; \
            s/{TRFCD_rgb}/${color_rgb[TRFCD]}/g ; \
            s/{TRFCF_rgb}/${color_rgb[TRFCF]}/g ; \
            s/{LANDA_rgb}/${color_rgb[LANDA]}/g ; \
            s/{LANDF_rgb}/${color_rgb[LANDF]}/g ; \
            s/{CSTLN_rgb}/${color_rgb[CSTLN]}/g ; \
            s/{SNDG1_rgb}/${color_rgb[SNDG1]}/g ; \
            s/{SNDG2_rgb}/${color_rgb[SNDG2]}/g ; \
            s/{DEPSC_rgb}/${color_rgb[DEPSC]}/g ; \
            s/{DEPCN_rgb}/${color_rgb[DEPCN]}/g ; \
            s/{DEPDW_rgb}/${color_rgb[DEPDW]}/g ; \
            s/{DEPMD_rgb}/${color_rgb[DEPMD]}/g ; \
            s/{DEPMS_rgb}/${color_rgb[DEPMS]}/g ; \
            s/{DEPVS_rgb}/${color_rgb[DEPVS]}/g ; \
            s/{DEPIT_rgb}/${color_rgb[DEPIT]}/g ; \
            s/{RADHI_rgb}/${color_rgb[RADHI]}/g ; \
            s/{RADLO_rgb}/${color_rgb[RADLO]}/g ; \
            s/{ARPAT_rgb}/${color_rgb[ARPAT]}/g ; \
            s/{NINFO_rgb}/${color_rgb[NINFO]}/g ; \
            s/{RESBL_rgb}/${color_rgb[RESBL]}/g ; \
            s/{ADINF_rgb}/${color_rgb[ADINF]}/g ; \
            s/{RESGR_rgb}/${color_rgb[RESGR]}/g ; \
            s/{SHIPS_rgb}/${color_rgb[SHIPS]}/g ; \
            s/{PSTRK_rgb}/${color_rgb[PSTRK]}/g ; \
            s/{SYTRK_rgb}/${color_rgb[SYTRK]}/g ; \
            s/{PLRTE_rgb}/${color_rgb[PLRTE]}/g ; \
            s/{APLRT_rgb}/${color_rgb[APLRT]}/g ; \
            s/{UINFD_rgb}/${color_rgb[UINFD]}/g ; \
            s/{UINFF_rgb}/${color_rgb[UINFF]}/g ; \
            s/{UIBCK_rgb}/${color_rgb[UIBCK]}/g ; \
            s/{UIAFD_rgb}/${color_rgb[UIAFD]}/g ; \
            s/{UINFR_rgb}/${color_rgb[UINFR]}/g ; \
            s/{UINFG_rgb}/${color_rgb[UINFG]}/g ; \
            s/{UINFO_rgb}/${color_rgb[UINFO]}/g ; \
            s/{UINFB_rgb}/${color_rgb[UINFB]}/g ; \
            s/{UINFM_rgb}/${color_rgb[UINFM]}/g ; \
            s/{UIBDR_rgb}/${color_rgb[UIBDR]}/g ; \
            s/{UIAFF_rgb}/${color_rgb[UIAFF]}/g ; \
            s/{OUTLW_rgb}/${color_rgb[OUTLW]}/g ; \
            s/{OUTLL_rgb}/${color_rgb[OUTLL]}/g ; \
            s/{RES01_rgb}/${color_rgb[RES01]}/g ; \
            s/{RES02_rgb}/${color_rgb[RES02]}/g ; \
            s/{RES03_rgb}/${color_rgb[RES03]}/g ; \
            s/{BKAJ1_rgb}/${color_rgb[BKAJ1]}/g ; \
            s/{BKAJ2_rgb}/${color_rgb[BKAJ2]}/g" \
            $TEMPLATE >> $FINAL_FILE  
        else
            printf "Template file missing: %s\n" $TEMPLATE
        fi
    fi
done < $TEMP_CSV_FILE
#
#  Add dummy layer to fluch the label cache
#  
cat << EOF >> $FINAL_FILE

#
#  Dummy layer to flush the label cache
#
LAYER
   NAME "force_label_draw_CL${CL}"
   GROUP "base"
   TYPE POINT
   PROCESSING FORCE_DRAW_LABEL_CACHE=FLUSH
   TRANSFORM FALSE
   STATUS ON
   FEATURE
      POINTS 1 1 END
   END
END
EOF

#
# clean up
#
/bin/rm $TEMP_CSV_FILE
