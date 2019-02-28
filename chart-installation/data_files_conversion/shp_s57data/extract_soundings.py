'''Convert numeric ids to labels in S57 shapefiles.

A new field will be added to each datasource containing a field to be
converted.  This new label field will contain the label or labels corresponding
to the original value.
'''
from argparse import ArgumentParser
from collections import namedtuple
import csv
from functools import lru_cache
from pathlib import Path

from typing import Iterator, List, Tuple

from osgeo import ogr, osr  # type: ignore


HERE = Path(__file__).absolute().parent


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('data_directory',
                        help='Directory of the S57 shapefiles',
                        type=Path)
    args = parser.parse_args()

    for level in '123456':
        extract_soundings(args.data_directory, level)


def extract_soundings(base_dir: Path, level: str) -> None:
    directory = base_dir / level
    destination = directory / 'CL{level}_X-SNDG_POINT.shp'.format(level=level)
    if destination.exists():
        # Destroy any old X-SNDG
        glob = destination.with_suffix('.*').name
        for f in directory.glob(glob):
            f.unlink()

    x_sndg, layer = create_datasource(destination)

    for dataset in datasets():
        for shape in ('POLYGON', 'LINESTRING', 'POINT'):
            filename = 'CL{level}_{acronym}_{shape}.shp'.format(
                level=level,
                acronym=dataset,
                shape=shape
            )
            path = directory / filename
            if path.exists():
                convert_dataset(path, layer)


def convert_dataset(
    path: Path,
    sndg_layer: ogr.Layer,
) -> None:
    file = ogr.Open(str(path))
    layer = file.GetLayer()
    defn = sndg_layer.GetLayerDefn()
    for feature in layer:
        if not feature.GetFieldAsString('VALSOU'):
            # VALSOU is not set; feature has no sounding
            continue

        new = ogr.Feature(defn)
        new.SetField('RCID', feature.GetField('RCID'))
        new.SetField('DEPTH', feature.GetField('VALSOU'))
        new.SetGeometry(feature.GetGeometryRef().Centroid())
        sndg_layer.CreateFeature(new)


def create_datasource(destination: Path) -> Tuple[ogr.DataSource, ogr.Layer]:
    driver = ogr.GetDriverByName('ESRI Shapefile')
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(3857)
    ds = driver.CreateDataSource(str(destination))
    layer_name = destination.with_suffix('').name
    layer = ds.CreateLayer(layer_name, target_srs, ogr.wkbPoint)
    layer.CreateField(ogr.FieldDefn('RCID', ogr.OFTInteger64))
    layer.CreateField(ogr.FieldDefn('DEPTH', ogr.OFTReal))

    return ds, layer


@lru_cache(maxsize=1)
def datasets() -> List[str]:
    def _inner() -> Iterator[str]:
        with open(str(HERE / 's57objectclasses.csv'), newline='') as f_classes:
            classes = csv.reader(f_classes, delimiter=',')

            ObjectClass = namedtuple('ObjectClass', [
                'Code', 'ObjectClass', 'Acronym', 'Attribute_A', 'Attribute_B',
                'Attribute_C', 'Class', 'Primitives'
            ])
            assert tuple(next(classes)) == ObjectClass._fields

            for line in classes:
                object_class = ObjectClass(*line)
                attributes = {
                    attribute for attribute in ';'.join([
                        object_class.Attribute_A,
                        object_class.Attribute_B,
                        object_class.Attribute_C
                    ]).split(';')
                    if attribute
                }

                if 'VALSOU' in attributes:
                    yield object_class.Acronym

    return list(_inner())


if __name__ == '__main__':
    main()
