# read class obj csv file.  For each of them
# creat an add in objlst.txt file


# install with sudo apt-get install python-gdal
# sudo wget https://raw2.github.com/smercier/mapsforge-senc-rendertheme/master/opencpn.org-S57-reference/s57objectclasses.csv

import csv
import os

gl_csv_file_obj = "s57objectclasses.csv"
gl_objlist_file = "objlist.txt"
# fields csv file
# "Code","ObjectClass","Acronym","Attribute_A","Attribute_B","Attribute_C","Class","Primitives"

f_obj = open(gl_objlist_file, "w")
ifile = open(gl_csv_file_obj, "r")
reader = csv.reader(ifile)
i = 0
for row in reader:
    if i != 0:
        # read field in array
        str_fld = row[3] + row[4] + row[5]
        shp_fld = str_fld.split(";")

        # read accronyme Uper lower case is realy important
        shp_name = row[2]

        # read type geom avaible
        shp_type = row[7].split(";")

        # for each type geom of ObjectClass, create a shapefiles
        for type_ in shp_type:

            # we need to transform primitive
            if type_ == "Area":
                s_prim = "POLYGON"
            elif type_ == "Point":
                s_prim = "POINT"
            elif type_ == "Line":
                s_prim = "LINESTRING"
            else:
                s_prim = ""

            if s_prim != "":
                f_obj.write(shp_name+","+s_prim+"\n")

    i = + 1

f_obj.close()
ifile.close()
