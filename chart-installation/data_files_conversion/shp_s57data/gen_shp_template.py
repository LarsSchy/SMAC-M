# read class obj csv file.  For each of them
# creat an empty Shapefile with all field find
# in csv file

# install with sudo apt-get install python-gdal

import csv
import os
import sys
from osgeo import ogr
import re

gl_csv_file_obj = "s57objectclasses.csv"
print "================================================================"
print "not full improve.  this script need to bu run into ./builddata"
print "usage: python gen_shp.py [database sqlite path]"
print "================================================================"
##print "running on " + str(sys.argv[1] + " database adding " + str(gl_csv_file_obj)  + "object class ...."

# fields csv file
#"Code","ObjectClass","Acronym","Attribute_A","Attribute_B","Attribute_C","Class","Primitives"

def create_shp(db,path,name,sufix,in_type_,fld):
    if in_type_ == '':
       return
    
    # create a shapefile with OGR    
    driver = ogr.GetDriverByName('Esri Shapefile')
    
    # base on primitive -> type geom
    if in_type_ == 'Area':
        shp_str = path+name+"_POLYGON"+sufix
        tbl_str = name+"_POLYGON"
        # remove if exist
        if os.path.isfile(shp_str+'.shp'):
             os.remove(shp_str+".shp")
             os.remove(shp_str+".shx")
             os.remove(shp_str+".dbf")

        ds = driver.CreateDataSource(shp_str+'.shp')
        layer = ds.CreateLayer('', None, ogr.wkbPolygon)
    elif  in_type_ == 'Point':
        shp_str = path+name+"_POINT"+sufix
        tbl_str = name+"_POINT"
        # remove if exist
        if os.path.isfile(shp_str+'.shp'):
             os.remove(shp_str+".shp")
             os.remove(shp_str+".shx")
             os.remove(shp_str+".dbf")

        ds = driver.CreateDataSource(shp_str+".shp")
        layer = ds.CreateLayer('', None, ogr.wkbPoint)
    elif  in_type_ == 'Line':
        shp_str = path+name+"_LINESTRING"+sufix
        tbl_str = name+"_LINESTRING"
        # remove if exist
        if os.path.isfile(shp_str+'.shp'):
             os.remove(shp_str+".shp")
             os.remove(shp_str+".shx")
             os.remove(shp_str+".dbf")

        ds = driver.CreateDataSource(shp_str+".shp")
        layer = ds.CreateLayer('', None, ogr.wkbLineString)
    else:
        return
   
    print("Create "+shp_str) 

    ## every shapefile need a PRIM field
    field_defn = ogr.FieldDefn( 'PRIM', ogr.OFTString )
    field_defn.SetWidth( 3 )
    layer.CreateField(field_defn)
    field_defn = ogr.FieldDefn( 'symbol', ogr.OFTString )
    field_defn.SetWidth( 15 )
    layer.CreateField(field_defn)
    field_defn = ogr.FieldDefn( 'label', ogr.OFTString )
    field_defn.SetWidth( 25 )
    layer.CreateField(field_defn)
    field_defn = ogr.FieldDefn( 'instruction', ogr.OFTString )
    field_defn.SetWidth( 3 )
    layer.CreateField(field_defn)


    # add all field
    for f in fld:
        if f != '':
            field_defn = ogr.FieldDefn( f, ogr.OFTString )
            field_defn.SetWidth( 3 )  
            layer.CreateField(field_defn)
              
    ds = None
    
    ## add this shp to sqlite seapal db
    #os.system("ogr2ogr -append " + db + " " + shp_str + ".shp -nln " + tbl_str +" -lco SPATIAL_INDEX=NO")


ifile  = open(gl_csv_file_obj, "rb")
reader = csv.reader(ifile)
i=0


for row in reader:
    if i !=0:
        # read field in array
        str_fld = row[3] + row[4] + row[5]
        shp_fld = str_fld.split(";")

        # read shapefiles name.  
        #  caution case sensitive objectname so we add '_lcase' because SQLite is not casesensitive
        shp_name = row[2]
        if re.match("^[a-z_]+$",shp_name) is not None:
             shp_name = shp_name + "_lcase"

        #read shapefile type geom
        shp_type = row[7].split(";")
 
        # for each type geom of ObjectClass, create a shapefiles
        ## gl_path="../../../data/1/shapefiles/shp/template/"
        for type_ in shp_type:
            create_shp(str(sys.argv[1]),"./shp_template/",shp_name,"",type_,shp_fld)
      
    i =+ 1

ifile.close()
