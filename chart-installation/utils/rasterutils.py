#!/usr/bin/python2

import os
import sys
from osgeo import gdal
from osgeo import osr
from subprocess import check_output

gdal.UseExceptions()

default_output_srs = "4326"

def calculate_source_projection(raster_file_path):
    source = gdal.Open(raster_file_path)
    from_sys = osr.SpatialReference()
    from_sys.ImportFromWkt(source.GetProjection())
    source_srs = from_sys.GetAuthorityCode("PROJCS")
    # If no PROJCS tag can be found we assume default projection, WGS84
    return source_srs or default_output_srs

def calculate_total_extent(data_path, list_of_files, to_srs):
    total_extent = [sys.maxint, sys.maxint, -sys.maxint - 1, -sys.maxint - 1]
    for f in list_of_files:
        name = f[1]
        sub_dir = f[0] or ""
        source = gdal.Open(os.path.join(data_path, sub_dir, name))
        from_sys = osr.SpatialReference()
        from_sys.ImportFromWkt(source.GetProjection())
        gt = source.GetGeoTransform()
        width = source.RasterXSize
        height = source.RasterYSize

        thisMinX = gt[0]
        thisMinY = gt[3] + width*gt[4] + height*gt[5]
        thisMaxX = gt[0] + width*gt[1] + height*gt[2]
        thisMaxY = gt[3]

        to_sys = osr.SpatialReference()
        to_sys.ImportFromEPSG(to_srs)
        transformation = osr.CoordinateTransformation(from_sys,to_sys)
        minXY = transformation.TransformPoint(thisMinX, thisMinY)
        maxXY = transformation.TransformPoint(thisMaxX, thisMaxY)

        if minXY[0] < total_extent[0]:
            total_extent[0] = minXY[0]
        if minXY[1] < total_extent[1]:
            total_extent[1] = minXY[1]
        if maxXY[0] > total_extent[2]:
            total_extent[2] = maxXY[0]
        if maxXY[1] > total_extent[3]:
            total_extent[3] = maxXY[1]
    return total_extent

# This method is to be used by clients of this class
def find_all_raster_files(data_path, suffixes):
    return find_all_raster_files_internal(data_path, None, suffixes, True)

# This is an internal method that recurse through the directory tree
def find_all_raster_files_internal(data_path, sub_dir, suffixes, traverse_subdir):
    files = []
    for item in os.listdir(data_path):
        if os.path.isdir(os.path.join(data_path,item)) and traverse_subdir:
            # Recurse and extend the layers list with the list from the subdir
            files.extend(find_all_raster_files_internal(os.path.join(data_path,item), item, suffixes, False))
        _, filesuffix = os.path.splitext(item)
        if filesuffix in suffixes:
            files.append((sub_dir, item))
    return files

# This mehod returns the proper azimuth angle for hillshading for the file given
def get_proper_azimuth_for_file(tif_file):
    bashCmd = ' '.join(["gdalinfo",  "-mm", tif_file, "| grep Min/Max | cut -d'=' -f 2"])
    minmax = check_output(bashCmd, shell=True)
#   If the values are below zero, treat the data as Depth
    if min(map(float, minmax.split(',', 1))) < 0:
        return 135
    else:
        return 315

