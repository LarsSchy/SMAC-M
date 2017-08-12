#!/bin/sh
#
#  convert_colors_xml2csv
#
#  Convert color tables in XML format to CSV format
#  A csv file with color name, rbg and hex color is created.
#  input tables are from opencpn project
#
#  Lars Schylberg, 2015-09-20
#
#  Evaluate arguments
#
if [ $# != 1 ]
then
    echo Usage: `basename $0` 
    echo '       input=xml_file_with_colors'
    exit 1
fi
#
#  parse input arguments
#
for i do
	case $i in
		input=*)
			INPUT=`echo $i | sed s/input=//` ;;
		i=*)
			INPUT=`echo $i | sed s/i=//` ;;			
		*)
			echo "Unrecognized option: $i"
			echo "Options: "
			echo "       input=xml_file_with_colors"
			exit 1
	esac
done
#
# convert the data
#
for color_mode in $(xmlstarlet sel -T -t \
					-m "//chartsymbols/color-tables/color-table" \
					-v @name -n $INPUT); do
  xmlstarlet sel -T -t \
    -m "//chartsymbols/color-tables" \
	-m "color-table[@name='$color_mode']" \
	-m "color" \
	-v "concat(@name,',',@r,' ',@g,' ',@b)" \
	-n $INPUT | \
  awk -F',' '{split($2,a," "); \
	  printf "%s,%s,#%02X%02X%02X\n", $1, $2, a[1],a[2],a[3]}' > \
  Chart_Color_${color_mode}.csv 
done
