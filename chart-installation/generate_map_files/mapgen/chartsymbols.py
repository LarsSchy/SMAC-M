# -*- coding: utf-8 -*-

import os
from xml.etree import ElementTree as etree

from .cs import lookups_from_cs
from .filters import MSAnd, MSFilter
from .instructions import get_command, CS, SY
from .lookup import Lookup
from .symbol import VectorSymbol, Pattern

from . import templates


class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    @property
    def hex(self):
        return '"#{:02x}{:02x}{:02x}"'.format(self.r, self.g, self.b).upper()

    @property
    def rgb(self):
        return ' '.join([self.r, self.g, self.b])

    def __str__(self):
        return self.hex


class ChartSymbols():

    color_table = {}  # type: dict

    symbols_def = {}

    point_lookups = {}

    line_lookups = {}

    polygon_lookups = {}

    root = None

    mapfile_layer_template = templates.mapfile_layer_template

    def __init__(self, file, point_table='Simplified', area_table='Plain',
                 displaycategory=None, color_table='DAY_BRIGHT'):

        if not os.path.isfile(file):
            raise Exception('chartsymbol file do not exists')

        tree = etree.parse(file)
        root = tree.getroot()
        self.root = root

        self._color_tables = self.load_color_table(root)

        self.load_colors(color_table)

        self.point_lookups = {}
        self.line_lookups = {}
        self.polygon_lookups = {}

        self.symbols_def = {}
        self.line_symbols = {}
        self.area_symbols = {}

        self.load_symbols(root)
        self.load_lookups(root, point_table, area_table, displaycategory)

    def load_colors(self, color_table):
        self.color_table = self._color_tables.get(color_table, {})

    def load_color_table(self, root):
        tables = {}
        for table in root.iter('color-table'):
            name = table.get('name')
            colors = {}
            for color in table.iter('color'):
                colors[color.get('name')] = Color(
                    color.get('r'),
                    color.get('g'),
                    color.get('b')
                )
            tables[name] = colors

        return tables

    def load_symbols(self, root):
        for symbol in root.iter('symbol'):
            try:
                name = symbol.find('name').text
                bitmap = symbol.find('bitmap')
                pivot = bitmap.find('pivot')
                width = int(bitmap.get('width'))
                height = int(bitmap.get('height'))
                self.symbols_def[name] = {
                    'pivot': [int(pivot.get('x')), int(pivot.get('y'))],
                    'size': [width, height],
                }
            except:
                continue

        for linestyle in root.iter('line-style'):
            symbol = VectorSymbol(linestyle)
            if symbol:
                self.line_symbols[symbol.name] = symbol

        for pattern in root.iter('pattern'):
            symbol = Pattern.from_element(pattern)
            if symbol:
                self.area_symbols[symbol.name] = symbol

    def load_lookups(self, root, point_style, area_style,
                     displaycategory=None):
        if displaycategory is None:
            displaycategory = AllInclusive()

        for lookup in root.iter('lookup'):
            try:
                name = lookup.get('name')
                id = lookup.get('id')
                lookup_type = lookup.find('type').text
                table_name = lookup.find('table-name').text
                display = lookup.find('display-cat').text
                comment = lookup.find('comment').text
                str_instruction = lookup.find('instruction').text or ''
                rules = MSAnd(
                    *(MSFilter.from_attrcode(attr.text)
                      for attr in lookup.findall('attrib-code'))
                )
            except (KeyError, AttributeError):
                continue

            if table_name in (point_style, area_style, 'Lines') and \
                    display in displaycategory:
                if lookup_type == 'Point':
                    lookup_table = self.point_lookups.setdefault(name, [])
                elif lookup_type == 'Line':
                    lookup_table = self.line_lookups.setdefault(name, [])
                elif lookup_type == 'Area':
                    lookup_table = self.polygon_lookups.setdefault(name, [])
                else:
                    lookup_table = []

                lookups = Lookup(
                    id=id,
                    table=table_name,
                    display=display,
                    comment=comment,
                    instruction=[],
                    rules=rules,
                )

                # If we have a CS instruction, explode it in many lookups
                parts = str_instruction.split(';')
                for part in parts:
                    if not part:
                        continue

                    command = get_command(part)
                    if isinstance(command, CS):
                        details = command.proc
                        lookups @= lookups_from_cs(details, lookup_type, name)

                    else:
                        lookups.add_instruction(command)

                for lookup in lookups:
                    lookup_table.append(lookup)

    def get_point_mapfile(self, layer, feature, group, msd, fields):
        base = "CL{}_{}_POINT".format(layer, feature)

        try:
            charts = self.point_lookups[feature]
        except KeyError:
            return ''

        data = self.get_mapfile_data(layer, base, charts)
        classes = self.get_point_mapfile_classes(charts, feature, fields)

        mapfile = self.mapfile_layer_template.format(
            layer=layer, feature=feature, group=group, max_scale_denom=msd,
            type='POINT', data=data, classes=classes)

        # Hack to add special layers for Light Sector.
        # TODO: this should be refactor in future phases
        if feature == 'LIGHTS':
            mapfile = templates.lights_layer_template.format(layer, mapfile,
                                                             group, msd)

        return mapfile

    def get_mapfile_data(self, layer, base, charts):
        data = 'DATA "{}"'.format('{}/{}'.format(layer, base))

        for chart in charts:
            if not chart['instruction']:
                continue
            parts = chart['instruction']
            for command in parts:
                if isinstance(command, SY) and command.rot_field:
                    return templates.dynamic_data_instruction.format(
                        layer, base, command.rot_field)

        return data

    def get_point_mapfile_classes(self, charts, feature, fields):
        classes = ""

        for chart in charts:
            expression = self.get_expression(chart['rules'], fields)
            style = self.get_point_style(chart['instruction'], feature)
            if not style:
                continue
            classes += templates.class_template.format(expression, style,
                                                       chart['id'])

        return classes

    def get_line_mapfile(self, layer, feature_type, group, max_scale_denom,
                         fields):
        base = "CL{}_{}_LINESTRING".format(layer, feature_type)

        try:
            lookups = self.line_lookups[feature_type]
        except KeyError:
            return ''

        return self._get_mapfile(layer, feature_type, group, max_scale_denom,
                                 base, lookups, 'LINE', fields)

    def get_poly_mapfile(self, layer, feature_type, group, max_scale_denom,
                         fields):
        base = "CL{}_{}_POLYGON".format(layer, feature_type)

        try:
            lookups = self.polygon_lookups[feature_type]
        except KeyError:
            return ''

        return self._get_mapfile(layer, feature_type, group, max_scale_denom,
                                 base, lookups, 'POLYGON', fields)

    def _get_mapfile(self, layer, feature_type, group, max_scale_denom,
                     base, lookups, type, fields):
        data = self.get_mapfile_data(layer, base, lookups)
        typed_classes = self.get_mapfile_classes(lookups, feature_type, type,
                                                 fields)

        mapfile = ''
        for geom_type in ['POLYGON', 'LINE', 'POINT']:
            classes = typed_classes[geom_type]
            if(classes):
                mapfile += self.mapfile_layer_template.format(
                    layer=layer, feature=feature_type, group=group,
                    type=geom_type, max_scale_denom=max_scale_denom,
                    data=data, classes=classes)

        return mapfile

    def get_mapfile_classes(self, lookups, feature, geom_type, fields):
        classes = {
            'POINT': [],
            'LINE': [],
            'POLYGON': [],
        }

        for lookup in lookups:
            expression = self.get_expression(lookup['rules'], fields)
            styles = self.get_styleitems(lookup['instruction'], feature,
                                        geom_type)
            for style_geom_type, style in styles.items():
                if not style:
                    continue

                classes[style_geom_type].append(
                    templates.class_template.format(
                        expression, style, lookup['id']
                    )
                )

        classes['POINT'] = '\n'.join(classes['POINT'])
        classes['LINE'] = '\n'.join(classes['LINE'])
        classes['POLYGON'] = '\n'.join(classes['POLYGON'])
        return classes

    def get_expression(self, rules, fields):
        expression = ""

        if rules:
            expression = "EXPRESSION (" + rules.to_expression(fields) + ")"

        return expression

    def get_point_style(self, instruction, feature):
        style = []

        if not instruction:
            return ''

        # Split on ;
        try:
            for command in instruction:
                style.append(command(self, feature, 'POINT'))

        except:
            return ""

        return '\n'.join(style)

    def get_styleitems(self, instruction, feature, geom_type):
        style = {
            'POINT': [],
            'LINE': [],
            'POLYGON': [],
        }
        try:
            for command in instruction:
                styles = command(self, feature, geom_type)
                if isinstance(styles, str):
                    style[geom_type].append(styles)
                elif styles:
                    for style_type, style_str in styles.items():
                        style[style_type].append(style_str)

            style['POINT'] = '\n'.join(filter(None, style['POINT']))
            style['LINE'] = '\n'.join(filter(None, style['LINE']))
            style['POLYGON'] = '\n'.join(filter(None, style['POLYGON']))
            return style
        except:
            return {
                'POINT': [],
                'LINE': [],
                'POLYGON': [],
            }


class AllInclusive:
    def __contains__(self, val):
        return True
