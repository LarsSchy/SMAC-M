#!/bin/bash
#
#
#
#  Evaluate arguments
#
if [ $# != 2 ]
then
    echo
    echo Usage: `basename $0` 
    echo '       data_dir=/path/to/data/dir'
    echo '       config_dir=/path/to/data/dir'
    echo ' '
    exit 1
fi
#
#  parse input arguments
#
for i do
	case $i in
		data_dir=*)
			DATA_DIR=`echo $i | sed s/data_dir=//` ;;
		data=*)
			DATA_DIR=`echo $i | sed s/data=//` ;;
        config_dir=*)
            CONFIG_DIR=`echo $i | sed s/config_dir=//` ;;
        config=*)
            CONFIG_DIR=`echo $i | sed s/config=//` ;;
		*)
			echo ""
			echo "Unrecognized option: $i"
			echo 'Options: '
			echo '      data_dir=/path/to/data/dir'
            echo '      config_dir=/path/to/data/dir'
			echo ''
			exit 1
	esac
done
#

for CL in `ls $DATA_DIR`; do
    FILE=${CONFIG_DIR}/chart_list_${CL}.csv
    if [ -f ${FILE} ]; then
        rm ${FILE}
    fi
    echo "LAYER" > $FILE
    # List all files without extension | take second and remaining word | sort unique and output to file
    ls -1 ${DATA_DIR}/${CL}/*.shp | xargs -n1 basename | awk -F. '{ print $1 }' | sed -r 's/.{4}//' | sort -u >>${FILE}
    echo "New layer file created: $FILE"
done
