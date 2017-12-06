#!/usr/bin/python2

# TODO 
# - Dont assume WGS84, instead read from input layer.
# - Find a better way to separate different same object type with multiple
# geometry types.

import subprocess
import multiprocessing as mp
import osr
import ogr
import sys
import fnmatch
import os
import time
import math
import socket
import itertools

rundir="/opt/data/chart-installation/data_files_conversion/"

def send_progress(socket, min, max, current):
    if socket:
        s = "p:min={},max={},current={}\n".format(min, max, current)
        try:
            r = socket.sendall(s)
        except:
            print ("Error sending progress information")

def process(level, source_path, output_path, progress_address=None, debug=None):
    s = None
    if progress_address:
        try:
            host, port = progress_address.split(":")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, int(port)))
        except:
            print "Error Creating socket"
    print "CL{} | Starting processing".format(level)
    # setup OGR environment options
    os.environ["OGR_S57_OPTIONS"] = "SPLIT_MULTIPOINT=ON,ADD_SOUNDG_DEPTH=ON,RECODE_BY_DSSI=ON"

    input_driver = "S57"
    output_driver = "ESRI Shapefile"
    output_path = os.path.join(output_path,str(level))

    result = {}
    os.makedirs(output_path)

    files = glob(source_path, level)

    driver = ogr.GetDriverByName(input_driver)

    send_progress(s,0,5,0)
    print "CL{} | Merging S57 features".format(level)
    for f in files:
        # print f[:-4]
        datasource = driver.Open(f, 0)
        for layer in datasource:
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326) # dont assume WGS84!

            objtype = layer.GetName()
            for feature in layer:
                # need to find a better way to separate different geometry
                # types(Point,polygon,line etc.) with same objectcode(eg.
                # SOUNDG)
                dtype = feature_datatype_name(feature)
                if not dtype:
                    continue
                key = objtype + "-" + dtype

                if key not in result:
                    result[key] = []
                
                result[key].append(feature)
    send_progress(s,0,5,2)
    
    out_driver = ogr.GetDriverByName(output_driver)
    # dont assume WGS84
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    print "CL{} | Creating output shape files".format(level)
    out_files = []
    for key in result:
        objtype, geom_type = key.split("-")
        out_filename = get_name(geom_type, level, objtype)
        out_files.append(out_filename)
        filepath = os.path.join(output_path, out_filename)
        featuresToFile(result[key], output_driver, filepath, srs, key)

    send_progress(s,0,5,3)
    # PROCESS SOME OF THE LAYERS (SOUNDG, WRECKS and UWTROC)
    print "CL{} | Preprocessing".format(level)

    # SOUNDG 
    print "CL{} | Preprocessing soundg".format(level)

    # get the soundg file path
    try:
        soundgs = [os.path.join(output_path,f) for f in out_files if "SOUNDG" in f][0]
        dsrc = ogr.Open(soundgs, 1)
        layer = dsrc.GetLayer()

        # add WHOLE NUM and FRACNUM fields
        add_fields(layer, [("WHOLE_NUM",ogr.OFTInteger), ("FRAC_NUM", ogr.OFTInteger)])

        # fill the WHOLE_NUM and FRAC_NUM fields
        fill_fields(layer,[("WHOLE_NUM", fill_preproc_value_whole, ("DEPTH",)),
                           ("FRAC_NUM" , fill_preproc_value_frac , ("DEPTH",))])
    except IndexError:
        print "CL{} | WARNING {} is not available in data sources file".format(level,dataset)

    # WRECKS
    print "CL{} | Preprocessing wrecks".format(level)

    # get the wrecks file path
    try:
        wrecks = [os.path.join(output_path,f) for f in out_files if "WRECKS" in f][0]
        dsrc = ogr.Open(wrecks, 1)
        layer = dsrc.GetLayer()

        # add WHOLE NUM and FRACNUM fields
        add_fields(layer, [("WHOLE_NUM",ogr.OFTInteger), ("FRAC_NUM", ogr.OFTInteger)])

        # fill the WHOLE_NUM and FRAC_NUM fields
        fill_fields(layer,[("WHOLE_NUM", fill_preproc_value_whole, ("VALSOU",)),
                           ("FRAC_NUM", fill_preproc_value_frac, ("VALSOU",))])
    except IndexError:
        print "CL{} | WARNING {} is not available in data sources file".format(level,dataset)

    # UWTROC
    print "CL{} | Preprocessing uwtroc".format(level)

    # get the uwtroc file path
    try:
        uwtroc = [os.path.join(output_path,f) for f in out_files if "UWTROC" in f][0]
        dsrc = ogr.Open(uwtroc, 1)
        layer = dsrc.GetLayer()

        # add WHOLE NUM and FRACNUM fields
        add_fields(layer, [("WHOLE_NUM",ogr.OFTInteger), ("FRAC_NUM", ogr.OFTInteger)])

        # fill the WHOLE_NUM and FRAC_NUM fields
        fill_fields(layer,[("WHOLE_NUM", fill_preproc_value_whole, ("VALSOU",)),
                           ("FRAC_NUM", fill_preproc_value_frac, ("VALSOU",))])
    except IndexError:
        print "CL{} | WARNING {} is not available in data sources file".format(level,dataset)

    # SBDARE
    print "CL{} | Preprocessing sbdare".format(level)
    sbdares = [os.path.join(output_path,f) for f in out_files if "SBDARE" in f]
    for sbdare in sbdares:
        dsrc = ogr.Open(sbdare, 1)
        layer = dsrc.GetLayer()

        # Add SEABED field for seabed material
        add_fields(layer, [("SEABED",ogr.OFTString)])

        # Fill the seabed material column with text
        fill_fields(layer,[("SEABED", fill_seabed, ())])
                      

    # MIPARE
    print "CL{} | Preprocessing mipare".format(level)
    # get the file
    mipare = [os.path.join(output_path,f) for f in out_files if ("MIPARE" in f) and ("poly" in f)]
    for m in mipare:
        subprocess.call(os.path.join(os.getcwd(), "preproc_MIPARE.sh {}").format(m[:-4]), shell=True)
    

    # RESARE
    print "CL{} | Preprocessing resare".format(level)
    mipare = [os.path.join(output_path,f) for f in out_files if ("RESARE" in f) and ("poly" in f)]
    for m in mipare:
        subprocess.call(os.path.join(os.getcwd(), "preproc_RESARE.sh {}").format(m[:-4]), shell=True)

    # run shptree on the created shapefiles
    print "CL{} | Indexing files".format(level)
    send_progress(s,0,5,4)
    processes = []
    for f in out_files:
        processes.append(mp.Process(target=shptree, args=(output_path + "/" + f,)))

    #start
    for p in processes:
        p.start()

    #join
    for p in processes:
        p.join()

    send_progress(s,0,5,5)
    print "CL{} | Done".format(level)

    if s:
        s.close()
    return 

def glob(source_path, CL):
    # Get all S57 basefiles (ending with .000) for a specific zoom level and
    # return a list with the full path to all those files.
    matches = []
    for root, dirnames, filenames in os.walk(source_path):
        for filename in fnmatch.filter(filenames, '??{CL}*.000'.format(CL=CL)):
            matches.append(root + "/" + filename)
    return matches

def shptree(f):
    subprocess.call("shptree {} 1>/dev/null".format(f),shell=True)


def add_fields(layer,fielddefs):
    # fielddefs = [(new_field_name, data_type),...]
    # 
    for fielddef in fielddefs:
        layer.CreateField(ogr.FieldDefn(fielddef[0],fielddef[1]))

def fill_preproc_value_whole(feature, depth_field):
    depth = feature.GetField(depth_field)
    if depth == None:
        return None
    return abs(int(depth))


def fill_preproc_value_frac(feature, depth_field):
    depth = feature.GetField(depth_field)
    if depth == None:
        return None
    whole = feature.GetField("WHOLE_NUM")
    frac = int(round(10 * (depth - math.floor(depth))))
    if depth < 0:
        return 10 - frac
    else:
        return frac
    
def fill_seabed(feature):
    natsur_dic = {
            4:"S",
            1:"M",
            2:"Cy",
            3:"Si",
            5:"St",
            6:"G",
            7:"P",
            8:"Cb",
            9:"R",
            18:"Bo",
            14:"Co",
            17:"Sh"
        }
    natqua_dic = {
            1:"f",
            2:"m",
            3:"c",
            4:"bk",
            5:"sy",
            6:"so",
            7:"sf",
            8:"v",
            9:"ca",
            10:"h"
        }
    # natsur = seabed material
    natsur = feature.GetField("NATSUR")
    if natsur is not None:
        try:
            natsur = [int(n) for n in natsur.split(",")]
        except:
            print "ERROR: while processing natsur (%s)" % natsur
    else:
        natsur = []
    
    # natqua = seabed structure
    natqua = feature.GetField("NATQUA")
    if natqua is not None:
        try:
            natqua = [int(n) for n in natqua.split(",")]
        except:
            print "ERROR: while processing natqua (%s)" % natqua
    else:
        natqua = []

    
    # Merge the two seabed type columns
    if natqua is not None:
        data = itertools.izip_longest(natsur,natqua)

    res = []
    # build up the res list with strings to be merged to create the final text
    for d in data:
        natqua = d[1]
        natsur = d[0]
        if natsur is None:
            natsur = ""
        if natqua is None:
            natqua = ""

        if natsur in natsur_dic:
            natsur_str = natsur_dic[natsur]
        else:
            natsur_str = ""

        if natqua in natqua_dic:
            natqua_str = natqua_dic[natqua]
        else:
            natqua_str = ""

        a = natqua_str + natsur_str
        res.append(a)
    return ".".join(res)

def fill_fields(layer,fieldinfos):
    # Fills the fields of all features in layer. Fieldinfo says which fields to
    # change and to what.

    # fieldinfo = [("Field_name_to_fill", function that takes a feature as first
    # argument and returns the value to fill, optional extra args), ...]

    for feature in layer:
        for fieldinfo in fieldinfos:
            field_name = fieldinfo[0]
            func = fieldinfo[1]
            args = fieldinfo[2]

            data = func(feature,*args)
            if data == None:
                feature.UnsetField(field_name)
            else:
                feature.SetField(field_name, data)
        layer.SetFeature(feature)


def feature_datatype(feature):
    # returns the geometry datatype (point, line, polygon) of the feature 
    geomref = feature.GetGeometryRef()
    if geomref:
        return geomref.GetGeometryType()
    else:
        return None
    

def feature_datatype_name(feature):
    # returns the name of the geometry datatype of the feature
    geomref = feature.GetGeometryRef()
    if geomref:
        return geomref.GetGeometryName()
    else:
        return None


def get_name(geom_type, level, objtype):
    # returns the final filename of the a feature
    if geom_type == "POLYGON":
        geom_type = "poly"
    elif geom_type == "LINESTRING":
        geom_type = "line"
    else:
        geom_type = geom_type.lower()

    return "CL{}-{}-{}.shp".format(level,geom_type, objtype)


def featuresToFile(features, dst_drv, dst_name, dst_srs, layer_name=None,
        geomtype=None,overwrite=True):
    if not features: # features is empty list
        print "No Features Created"
        return

    drv = ogr.GetDriverByName(dst_drv)
    if drv is None:
        print "Driver not available ({})".format(dst_drv)
        return 

    dsrc = drv.CreateDataSource(dst_name)
    if dsrc is None:
        print "DataSource creation failed"
        return

    if not geomtype:
        f0 = features[0]
        geomref = features[0].GetGeometryRef()
        if geomref is not None:
            geomtype = geomref.GetGeometryType()
        else:
            return

    layer = dsrc.CreateLayer(layer_name, srs=dst_srs, geom_type=geomtype)

    # Create the fields for the new file
    for i in range(features[0].GetFieldCount()):
        fieldDef = features[0].GetFieldDefnRef(i)
        if "List" in ogr.GetFieldTypeName(fieldDef.GetType()):
            t = ogr.GetFieldTypeName(fieldDef.GetType())[:-4]
            if t == "String":
                fieldDef = ogr.FieldDefn(fieldDef.GetName(), ogr.OFTString)
            elif t == "Integer":
                fieldDef = ogr.FieldDefn(fieldDef.GetName(), ogr.OFTInteger)

        layer.CreateField(fieldDef)

    # print layer_name
    for feature in features:
        layer.CreateFeature(feature)
    
