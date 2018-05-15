###############################################################################
#
# Project:  SMAC-M - Scripts for Map And Chart Manager
# Author:   Simon Mercier (smercier@mapgears.com)
# Purpose:  This python script is based on Nexgis Navi2PG project
#           See CreateLightsSectorsStrategy() from
#           https://github.com/nextgis/navi2pg/blob/master/navi2pg.cpp
# Date:     Dec 2017
#
# TODO:     This script read a merged S-57 data base on SMAC-M enhance data.  We
#           should be able to read data from S-57 source data and merge result into
#           one dataset.
#
###############################################################################
from osgeo import ogr
from osgeo import osr
from osgeo.gdalconst import *
import os
import sys
import math
import csv

debugprint = 0
infile = None
pixel = None
line = None
#
# =============================================================================


def debug(str):
    if debugprint == 1:
        print(str)

# =============================================================================


def Usage():
    print('-----------------------------------------------------------------------------')
    print('This script let you create a light sector shapefiles based on LIGHTS dataset')
    print('')
    print(
        'Usage: python generate_light_sector.py [input_shapefile] [radius|"valmnr"]')
    print('       NOTE 1: input shapefile must be named as *_LIGHTS_*.shp')
    print('       NOTE 2: if radius = valmnr distance will be take in data')
    print('Output: [input_shapefile]_sector.shp')
    print('-----------------------------------------------------------------------------')
    sys.exit(1)

# =============================================================================


def GetRGBCode(id_):

    # code,id,colour,colour_code,rgb
    # 75,1,"white","W","255 240 99"

    csvFile = open('colour_code.csv', "r")
    reader = csv.reader(csvFile)

    for row in reader:
        if str(row[1]) == str(id_):
            return row[4]


def GetColourCode(id_):

    # code,id,colour,colour_code,rgb
    # 75,1,"white","W","255 240 99"

    csvFile = open('colour_code.csv', "r")
    reader = csv.reader(csvFile)

    for row in reader:
        if str(row[1]) == str(id_):
            return row[3]


def GetMeaning(id_):

    # "code","id","meaning"
    # 107,1,"F"
    csvFile = open('litchr_code.csv', "r")
    reader = csv.reader(csvFile)

    for row in reader:
        if str(row[1]) == str(id_):
            return row[2]


# =============================================================================
# Parse command line arguments.
# =============================================================================
if len(sys.argv) == 2:
    infile = sys.argv[1]
    radius = sys.argv[2]
else:
    Usage()

if infile is None:
    Usage()

# point light feature will need to be transform to 3857 later
source_srs = osr.SpatialReference()
source_srs.ImportFromEPSG(4326)
target_srs = osr.SpatialReference()
target_srs.ImportFromEPSG(3857)
srs_transformation = osr.CoordinateTransformation(source_srs, target_srs)


# Get driver
driver = ogr.GetDriverByName('ESRI Shapefile')

# Open input light dataset
ds_light_point = driver.Open(infile, GA_ReadOnly)


# Check to see if shapefile is found.
if ds_light_point is None:
    print(('Could not open %s' % (infile)))
    sys.exit(1)
else:
    print(('Opened %s' % (infile)))
    layer_light_point = ds_light_point.GetLayer()
    featureCount = layer_light_point.GetFeatureCount()
    print("Number of features in %s: %d" %
          (os.path.basename(infile), featureCount))


# Create sector shapepath
index = infile.find('_LIGHTS_')
filepath = infile[0:index] + '_LIGHTS_LINESTRING_SECTOR.shp'

debug(filepath)

if os.path.exists(filepath):
    os.remove(filepath)
shapeData = driver.CreateDataSource(filepath)

if shapeData is None:
    print("Unable to create output shapefile!")
    sys.exit(1)

# Create layer
#layerName = os.path.splitext(os.path.split(filepath)[1])[0]
layerName = infile[0:index] + '_SECTOR'
debug('layerName: ' + layerName)
sector_layer = shapeData.CreateLayer(
    layerName, target_srs, ogr.wkbMultiLineString)

# add needed fields
field_name = ogr.FieldDefn("COLOURRGB", ogr.OFTString)
field_name.SetWidth(20)
sector_layer.CreateField(field_name)
field_name = ogr.FieldDefn("TYPE", ogr.OFTString)
field_name.SetWidth(10)
sector_layer.CreateField(field_name)
field_name = ogr.FieldDefn("COLOUR", ogr.OFTString)
field_name.SetWidth(10)
sector_layer.CreateField(field_name)
field_name = ogr.FieldDefn("COLOURCODE", ogr.OFTString)
field_name.SetWidth(10)
sector_layer.CreateField(field_name)
field_name = ogr.FieldDefn("MEANING", ogr.OFTString)
field_name.SetWidth(30)
sector_layer.CreateField(field_name)
sector_layer.CreateField(ogr.FieldDefn("VALNMR", ogr.OFTReal))
sector_layer.CreateField(ogr.FieldDefn("SECTR1", ogr.OFTReal))
sector_layer.CreateField(ogr.FieldDefn("SECTR2", ogr.OFTReal))
sector_layer.CreateField(ogr.FieldDefn("LITCHR", ogr.OFTInteger))
sector_layer.CreateField(ogr.FieldDefn("SIGGRP", ogr.OFTReal))
sector_layer.CreateField(ogr.FieldDefn("SIGPER", ogr.OFTReal))
sector_layer.CreateField(ogr.FieldDefn("HEIGHT", ogr.OFTReal))

sector_layerDefinition = sector_layer.GetLayerDefn()

#
numOfSector = 0

for light_feature in layer_light_point:

    valnmr = light_feature.GetFieldAsDouble("VALNMR")
    sectr1 = light_feature.GetFieldAsDouble("SECTR1")
    sectr2 = light_feature.GetFieldAsDouble("SECTR2")

    #  if no value, jump to next row
    if int(sectr1) == 0 and int(sectr2) == 0:
        continue

    debug("valnmr %d / sectr1 %f / sectr2 %f" % (valnmr, sectr1, sectr2))
    numOfSector = numOfSector + 1

    # Transform light point to web mercator
    light_feature_3857 = light_feature.GetGeometryRef()
    light_feature_3857.Transform(srs_transformation)

    # ====================
    # Create rays sector
    # ====================

    # set light sector value
    feature = ogr.Feature(sector_layer.GetLayerDefn())
    feature.SetField("TYPE", "RAYS")
    feature.SetField("COLOURRGB", GetRGBCode(
        light_feature.GetFieldAsInteger("COLOUR")))
    feature.SetField("VALNMR", valnmr)
    feature.SetField("SECTR1", sectr1)
    feature.SetField("SECTR2", sectr2)

    # Create the sector line geometry
    lineGeom = ogr.Geometry(ogr.wkbLineString)
    # create end point geometry
    x = light_feature_3857.GetX() - math.sin(math.radians(sectr1)) * valnmr * 1852
    y = light_feature_3857.GetY() - math.cos(math.radians(sectr1)) * valnmr * 1852
    lineGeom.AddPoint(x, y)

    # create central point geometry
    lineGeom.AddPoint(light_feature_3857.GetX(), light_feature_3857.GetY())

    # create start point geometry
    x = light_feature_3857.GetX() - math.sin(math.radians(sectr2)) * valnmr * 1852
    y = light_feature_3857.GetY() - math.cos(math.radians(sectr2)) * valnmr * 1852
    lineGeom.AddPoint(x, y)

    feature.SetGeometry(lineGeom)

    sector_layer.CreateFeature(feature)

    # ====================
    # Create arc sector
    # ====================
    delta = sectr2 - sectr1

    if delta >= 0:
        angleFrom = sectr1
        angleTo = sectr2
    else:
        angleFrom = sectr1
        angleTo = 360 + sectr2

    # to fix the arc at a specific radius
    if radius == 'valnmr':
        # to fix the arc at the end of rays
        radius = valnmr * 1852
    else:
        radius = int(radius)

    # add all needed values to build the light signature on the arc
    feature = ogr.Feature(sector_layer.GetLayerDefn())
    feature.SetField("TYPE", "ARC")
    feature.SetField("COLOURRGB", GetRGBCode(
        light_feature.GetFieldAsInteger("COLOUR")))
    feature.SetField("COLOURCODE", GetColourCode(
        light_feature.GetFieldAsInteger("COLOUR")))
    feature.SetField("VALNMR", light_feature.GetFieldAsInteger("VALNMR"))
    feature.SetField("SECTR1", light_feature.GetFieldAsInteger("SECTR1"))
    feature.SetField("SECTR2", light_feature.GetFieldAsInteger("SECTR2"))
    feature.SetField("HEIGHT", light_feature.GetFieldAsInteger("HEIGHT"))
    feature.SetField("LITCHR", light_feature.GetFieldAsInteger("LITCHR"))
    feature.SetField("SIGGRP", light_feature.GetFieldAsInteger("SIGGRP"))
    feature.SetField("SIGPER", light_feature.GetFieldAsInteger("SIGPER"))
    feature.SetField("COLOUR", light_feature.GetFieldAsInteger("COLOUR"))
    feature.SetField("MEANING", GetMeaning(
        light_feature.GetFieldAsInteger("LITCHR")))

    # create the arc sector here, put lots of point on arc
    lineGeom = ogr.Geometry(ogr.wkbLineString)
    angle = angleFrom
    DegreesToPoint_ = 5
    while (angle <= angleTo):

        x = light_feature_3857.GetX() - math.sin(math.radians(angle)) * radius
        y = light_feature_3857.GetY() - math.cos(math.radians(angle)) * radius
        lineGeom.AddPoint(x, y)

        angle = angle + DegreesToPoint_

    x = light_feature_3857.GetX() - math.sin(math.radians(angleTo)) * radius
    y = light_feature_3857.GetY() - math.cos(math.radians(angleTo)) * radius
    lineGeom.AddPoint(x, y)

    feature.SetGeometry(lineGeom)

    sector_layer.CreateFeature(feature)

print("%d light sectors created" % numOfSector)
sys.exit(1)
