#!/bin/bash
#
#  Lars Schylberg, 2015-09-22
#
#  process_all_layers.sh  
#  Purpose: Runs the script process_layer_colors.sh and set color and 
#  max scale denom
#
#
#  Evaluate arguments
#

if [ $# != 3 ]
then
    echo Usage: `basename $0` 
    echo '       target=/path/to/target/dir'
    echo '       data=/path/to/data'
    echo '       config=/path/to/config'

    exit 1
fi
#
#  parse input arguments
#
for i do
    case $i in
        target=*)
            TARGET_DIR=`echo $i | sed s/target=//` ;;
        data=*)
            DATA_DIR=`echo $i | sed s/data=//` ;;
        config=*)
            CONFIG_DIR=`echo $i | sed s/config=//` ;;
        *)
            echo "Unrecognized option: $i"
            echo "Options: "
            echo "       target=/path/to/target/dir"
            echo "       data=/path/to/data/dir"
            echo "       config=/path/to/config/dir"
            exit 1
    esac
done
#
#  Read max scale denom values from a resource file (layer_msd.csv)
#
INPUT_LAYER_MSD="${CONFIG_DIR}/layer_rules/layer_msd.csv"
declare -A msd
while IFS=, read -r layer_number scale
do
    msd[$layer_number]=$scale
done < <(sed 's/, /,/g' "$INPUT_LAYER_MSD")
#
#  Process all color themes
#
declare -a colorfiles=(`ls "$CONFIG_DIR/color_tables"`)
for COLOR_FILE in "${colorfiles[@]}" ; do
    THEME=`basename $COLOR_FILE .csv`
    for LAYER in `ls "$DATA_DIR/"` ; do
        INPUT_FILE="${CONFIG_DIR}/layer_rules/layer_groups.csv"
        ./process_layer_colors.sh chart_level=$LAYER color_table_csv="${CONFIG_DIR}/color_tables/${COLOR_FILE}" input_file_csv=$INPUT_FILE maxscaledenom=${msd[$LAYER]} data_dir=$DATA_DIR target=${TARGET_DIR} &
    done
done
wait
