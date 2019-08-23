from enum import Enum
from functools import total_ordering
from operator import attrgetter

from utils.enum import OrderedEnum
from . import templates


class DisplayPriority(OrderedEnum):
    NotSet = -1
    NoData = 0  # no data fill area pattern
    Group1 = 1  # S57 group 1 filled areas
    Area1 = 2  # superimposed areas
    Area2 = 3  # superimposed areas also water features
    PointSymbol = 4  # point symbol also land features
    LineSymbol = 5  # line symbol also restricted areas
    AreaSymbol = 6  # area symbol also traffic areas
    Routing = 7  # routeing lines
    Hazards = 8  # hazards
    Mariners = 9  # VRM, EBL, own ship

    @classmethod
    def get(cls, key):
        key = key.title().replace(' ', '')
        try:
            return cls[key]
        except KeyError:
            return cls.NotSet


class GeomType(str, Enum):
    Polygon = 'POLYGON', 'POLYGON'
    Line = 'LINE', 'LINESTRING'
    Point = 'POINT', 'POINT'

    def __new__(cls, val, filename):
        self = str.__new__(cls)
        self._value_ = val
        self.filename = filename
        return self

    def __hash__(self):
        return hash(self.value)


@total_ordering
class LayerBase:
    priority = DisplayPriority.NotSet

    def __lt__(self, other):
        if isinstance(other, LayerBase):
            return self.priority < other.priority

        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, LayerBase):
            return self.priority == other.priority

        return NotImplemented


class Layer(LayerBase):
    rot_field = None

    def __init__(self, layer_level, feature_name, geom_type, group, msd,
                 fields, lookups, chartsymbols, metadata_name):
        self.layer_level = layer_level
        self.feature_name = feature_name
        self.geom_type = GeomType(geom_type)
        self.group = group
        self.msd = msd
        self.metadata_name = metadata_name
        self.base = "CL{}_{}_{}".format(layer_level, feature_name,
                                        self.geom_type.filename)
        if lookups:
            self.priority = max(
                lookups, key=attrgetter('display_priority')
            ).display_priority

        self.require_ogr = any(rule.require_ogr
                               for lookup in lookups
                               for rule in lookup.rules)
        self.sublayers = self._parse_lookups(lookups, fields, chartsymbols)

    def __bool__(self):
        return bool(self.sublayers)

    def _parse_lookups(self, lookups, fields, chartsymbols):
        classes = {
            GeomType.Line: [],
            GeomType.Point: [],
            GeomType.Polygon: [],
        }

        for lookup in lookups:
            self.rot_field = self.rot_field or lookup.rot_field

            expression = lookup.get_expression(fields)
            styleitems = lookup.get_styleitems(chartsymbols,
                                               self.feature_name,
                                               self.geom_type.value,
                                               fields)
            for geom_type, styleitem in styleitems.items():
                if styleitem:
                    classes[GeomType(geom_type)].append(
                        templates.class_template.format(
                            expression, '\n'.join(styleitem), lookup.id
                        )
                    )

        return [
            SubLayer(self, geom_type, class_)
            for geom_type in GeomType
            for class_ in [classes[geom_type]]
            if class_
        ]

    @property
    def mapfile(self):
        return '\n'.join(sl.mapfile for sl in self.sublayers)

    @property
    def data(self):
        if self.rot_field:
            return templates.dynamic_data_instruction.format(
                self.layer_level, self.base, self.rot_field)

        if self.require_ogr:
            return templates.ogr_data_instruction.format(self.layer_level,
                                                         self.base)

        return 'DATA "{}/{}"'.format(self.layer_level, self.base)


class LightsLayer(LayerBase):
    def __init__(self, main_layer):
        self.priority = main_layer.priority
        self.main_layer = main_layer

    @property
    def mapfile(self):
        return templates.lights_layer_template.format(
            self.main_layer.layer_level,
            self.main_layer.mapfile,
            self.main_layer.group,
            self.main_layer.msd,
        )


class SubLayer:
    def __init__(self, layer_parent, geom_type, classes):
        self.layer_parent = layer_parent
        self.geom_type = geom_type
        self.classes = classes

    @property
    def mapfile(self):
        parent = self.layer_parent
        return templates.mapfile_layer_template.format(
            layer=parent.layer_level,
            feature=parent.feature_name,
            metadata_name=parent.metadata_name,
            group=parent.group,
            type=self.geom_type,
            max_scale_denom=parent.msd,
            data=parent.data,
            classes='\n'.join(self.classes),
        )
