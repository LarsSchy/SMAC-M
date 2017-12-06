#!/usr/bin/python2

import gdal
import osr
import ogr
import argparse
from subprocess import call

gdal.UseExceptions()

to_srs = 3857

source = osr.SpatialReference()
source.ImportFromEPSG(4326)
target = osr.SpatialReference()
target.ImportFromEPSG(3857)
transform = osr.CoordinateTransformation(source, target)

def parse_arguments():
    parser = argparse.ArgumentParser(prog="georeference_tif", description="This program geo references a TIFF image to make a GeoTIFF")
    parser.add_argument("src_file", nargs=1, help="Your input TIFF image")
    parser.add_argument("out_file", nargs=1, help="The output GeoTIFF image")
    parser.add_argument("position", nargs=2, help="The upper left geographic position (Latitude Longitude)")
    parser.add_argument("pixelsize", nargs=2, help="The pixel size in meters (Latitude Longitude)")
    return parser.parse_args()

def main():
    args = parse_arguments()
    src_ds = gdal.Open(args.src_file[0])

    driver = gdal.GetDriverByName("GTiff")

    dst_ds = driver.CreateCopy(args.out_file[0], src_ds, 0)

    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(float(args.position[0]), float(args.position[1]))
    point.Transform(transform)

    gt = [ point.GetX(), float(args.pixelsize[0]), 0, point.GetY(), 0, -float(args.pixelsize[1])]

    dst_ds.SetGeoTransform(gt)

    to_sys = osr.SpatialReference()
    to_sys.ImportFromEPSG(to_srs)

    dest_wkt = to_sys.ExportToWkt()

    dst_ds.SetProjection(dest_wkt)

if __name__ == "__main__":
    main()
