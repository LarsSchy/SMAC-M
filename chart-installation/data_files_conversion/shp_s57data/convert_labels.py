"""Convert numeric ids to labels in S57 shapefiles.

A new field will be added to each datasource containing a field to be
converted.  This new label field will contain the label or labels corresponding
to the original value.
"""
from argparse import ArgumentParser
from collections import namedtuple
import csv
import functools
from pathlib import Path

from osgeo import ogr


HERE = Path(__file__).absolute().parent


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('data_directory',
                        help='Directory of the S57 shapefiles',
                        type=Path)
    parser.add_argument('fields', nargs='+',
                        help='Name of field to convert to labels')
    args = parser.parse_args()

    attr_values = get_field_value_mapping()
    for acronym, fields in datasets(args.fields):
        convert_dataset(args.data_directory, acronym, fields, attr_values)


def convert_dataset(base_dir, acronym, fields, values):
    filename_acronym = acronym
    if acronym.upper() != acronym:
        filename_acronym += '_lcase'

    for level in '123456':
        for shape in ('POLYGON', 'LINESTRING', 'POINT'):
            filename = 'CL{level}_{acronym}_{shape}.shp'.format(
                level=level,
                acronym=filename_acronym,
                shape=shape
            )
            path = base_dir / level / filename
            if path.exists():
                convert_file(path, acronym, fields, values)


def convert_file(path, acronym, fields, values):
    file = ogr.Open(str(path), True)
    try:
        layer = file.GetLayer()
        defn = layer.GetLayerDefn()
        existing_fields = []
        missing_fields = []
        for field in fields:
            if defn.GetFieldIndex(field) >= 0:
                existing_fields.append(field)
                if defn.GetFieldIndex(field + '_txt') < 0:
                    missing_fields.append(ogr.FieldDefn(field + '_txt'))
        layer.CreateFields(missing_fields)

        feat = layer.GetNextFeature()
        while feat:
            for field in existing_fields:
                value = feat.GetFieldAsString(field)
                if value:
                    value = ','.join(
                        values[field].get(v, v)
                        for v in value.split(',')
                    )
                feat.SetField(field + '_txt', value)

            layer.SetFeature(feat)
            feat = layer.GetNextFeature()
    finally:
        file.Destroy()


def get_field_value_mapping():
    with open(HERE / 's57attributes.csv', newline='') as attributes:
        attributes = csv.reader(attributes, delimiter=',')
        Attribute = namedtuple('Attributes', next(attributes))

        att_codes = {}
        for attribute in attributes:
            if not attribute:
                continue
            attribute = Attribute(*attribute)
            att_codes[attribute.Code] = attribute.Acronym

    with open(HERE / 's57expectedinput.csv', newline='') as inputs:
        inputs = csv.reader(inputs, delimiter=',')
        Input = namedtuple('Input', next(inputs))

        attrvalues = {}
        for input in inputs:
            if not input:
                continue
            input = Input(*input)
            acronym = att_codes[input.Code]
            attrvalues.setdefault(acronym, {})[input.ID] = input.Meaning

    return attrvalues


def datasets(fields):
    with open(HERE / 's57objectclasses.csv', newline='') as classes:
        classes = csv.reader(classes, delimiter=',')
        ObjectClass = namedtuple('ObjectClass', next(classes))

        for object_class in classes:
            if not object_class:
                continue
            object_class = ObjectClass(*object_class)
            attributes = {
                attribute for attribute in ';'.join([
                    object_class.Attribute_A,
                    object_class.Attribute_B,
                    object_class.Attribute_C
                ]).split(';')
                if attribute
            }

            matching_fields = attributes.intersection(fields)
            if matching_fields:
                yield object_class.Acronym, matching_fields


_open = open


@functools.wraps(_open)
def open(file, *args, **kwargs):
    """Helper function that accepts Path to open"""
    file = str(file)
    return _open(file, *args, **kwargs)


if __name__ == '__main__':
    main()
