# -*- coding: utf-8 -*-

import os
from symbol import VectorSymbol, Pattern
from xml.etree import ElementTree as etree

from instructions import get_command
from cs import lookups_from_cs


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

    mapfile_layer_template = """
# LAYER: {feature}  LEVEL: {layer}

LAYER
    NAME "{feature}_{layer}"
    GROUP "{group}"
    METADATA
        "ows_title" "{feature}"
        "ows_enable_request"   "*"
        "gml_include_items" "all"
        "wms_feature_mime_type" "text/html"
    END
    TEMPLATE blank.html
    TYPE {type}
    STATUS ON
    MAXSCALEDENOM {max_scale_denom}
    {data}
{classes}
END

# END of  LAYER: {feature}  LEVEL: {layer}
"""

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
        for lookup in root.iter('lookup'):
            try:
                name = lookup.get('name')
                id = lookup.get('id')
                lookup_type = lookup.find('type').text
                table_name = lookup.find('table-name').text
                display = lookup.find('display-cat').text
                comment = lookup.find('comment').text
                instruction = lookup.find('instruction').text or ''
                rules = []
                for attr in lookup.findall('attrib-code'):
                    # Assumption: All attrib-code are in numerical order
                    # index = int(attr.get('index'))
                    rules.append((attr.text[:6], attr.text[6:]))
            except (KeyError, AttributeError):
                continue

            if table_name in (point_style, area_style, 'Lines') and \
                    (displaycategory is None or display in displaycategory):
                if lookup_type == 'Point':
                    lookup = self.point_lookups.setdefault(name, [])
                elif lookup_type == 'Line':
                    lookup = self.line_lookups.setdefault(name, [])
                elif lookup_type == 'Area':
                    lookup = self.polygon_lookups.setdefault(name, [])
                else:
                    lookup = []

                # If we have a CS instruction, explode it in many lookups
                cs_instruction = False
                parts = instruction.split(';')
                for part in parts:
                    command = part[:2]
                    details = part[3:-1]
                    if command == 'CS':
                        cs_instruction = True
                        for cs_lookup in lookups_from_cs(details, lookup_type):
                            # Merge lookup with what was returned
                            cs_lookup.update({
                                'id': '{}-CS({})'.format(id, details),
                                'table': table_name,
                                'display': display,
                                'comment': comment
                            })
                            cs_lookup['rules'].extend(rules)
                            cs_lookup['instruction'] = instruction.replace(
                                part, cs_lookup['instruction'])

                            # Add to lookup list
                            lookup.append(cs_lookup)

                if not cs_instruction:
                    lookup.append({
                        'id': id,
                        'table': table_name,
                        'display': display,
                        'comment': comment,
                        'instruction': instruction,
                        'rules': rules,
                    })

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
            mapfile = """
# LIGHTS features and lines
LAYER
     NAME RAYS_SECTOR
     TYPE LINE
     DATA '{0}/CL{0}_LIGHTS_LINESTRING_SECTOR'
     MAXSCALEDENOM {3}
     GROUP "{2}"
     TOLERANCE 10
     TEMPLATE dummy.html
     PROJECTION
        "init=epsg:3857"
     END
     CLASS
        EXPRESSION ('[TYPE]'='RAYS')
        STYLE
            COLOR  77 77 77
            PATTERN 5 5 5 5 END
            WIDTH 1
        END
     END
     METADATA
        "oms_title" "RAYS_SECTOR"
        "ows_enable_request"   "*"
        "gml_include_items" "all"
        "wms_feature_mime_type" "text/html"
     END
 END
 LAYER
     NAME ARC_LIGHTS_SECTOR
     TYPE LINE
     DATA '{0}/CL{0}_LIGHTS_LINESTRING_SECTOR'
     MAXSCALEDENOM {3}
     GROUP "{2}"
     TOLERANCE 10
     TEMPLATE dummy.html
     PROJECTION
        "init=epsg:3857"
     END
     CLASS
         EXPRESSION ('[TYPE]'='ARC' AND [VALNMR]!=0)
         STYLE
            COLOR [COLOURRGB]
            WIDTH 3
         END
         TEXT ('[MEANING]'+'.'+tostring([SIGGRP],"%.2g")+ '.' + '[COLOURCODE]'+tostring([SIGPER],"%.2g")+ 's' + tostring([HEIGHT],"%.2g") + 'm'+ tostring([VALNMR],"%.2g") + 'M')
         LABEL
             TYPE TRUETYPE
             FONT sc
             COLOR 0 0 0
             OUTLINECOLOR 255 255 255
             SIZE 8
             ANTIALIAS TRUE
             #FORCE TRUE
             POSITION AUTO
             ANGLE FOLLOW
             MINFEATURESIZE AUTO
         END
     END
     CLASS
         EXPRESSION ('[TYPE]'='ARC' AND [SIGPER]!=0)
         TEXT ('[MEANING]'+'.'+'[SIGGRP]'+ '.' + '[COLOURCODE]'+tostring([SIGPER],"%.2g")+ 's')
         STYLE
            COLOR [COLOURRGB]
            WIDTH 3
         END
         LABEL
             TYPE TRUETYPE
             FONT sc
             COLOR 0 0 0
             OUTLINECOLOR 255 255 255
             SIZE 8
             ANTIALIAS TRUE
             #FORCE TRUE
             POSITION AUTO
             ANGLE FOLLOW
             MINFEATURESIZE AUTO
         END
     END
     METADATA
        "oms_title" "ARC_LIGHTS_SECTOR"
        "ows_enable_request"   "*"
        "gml_include_items" "all"
        "wms_feature_mime_type" "text/html"
     END
 END
 LAYER
     NAME LIGHTS_POINT_SIGNATURE
     TYPE POINT
     DATA '{0}/CL{0}_LIGHTS_POINT_SIGNATURE'
     MAXSCALEDENOM {3}
     GROUP "{2}"
     TOLERANCE 10
     TEMPLATE dummy.html
     PROJECTION
        "init=epsg:4326"
     END
     CLASS
         EXPRESSION ([VALNMR]!=0)
         TEXT ('[MEANING]'+'.'+'[SIGGRP]'+ '.' + '[COLOUR_COD]'+tostring([SIGPER],"%.2g")+ 's' + tostring([HEIGHT],"%.2g") + 'm'+ tostring([VALNMR],"%.2g") + 'M')
         LABEL
             TYPE TRUETYPE
             FONT sc
             COLOR 0 0 0
             ##OUTLINECOLOR 255 255 255
             SIZE 8
             ANTIALIAS TRUE
             ##FORCE TRUE
             POSITION cc
             OFFSET 65 12
         END
     END
     CLASS
         EXPRESSION ([SIGPER]!=0)
         TEXT ('[MEANING]'+'.'+tostring([SIGGRP],"%.2g")+ '.' + '[COLOUR_COD]'+tostring([SIGPER],"%.2g")+ 's')
         LABEL
             TYPE TRUETYPE
             FONT sc
             COLOR 0 0 0
             ##OUTLINECOLOR 255 255 255
             SIZE 8
             ANTIALIAS TRUE
             ##FORCE TRUE
             POSITION cc
             OFFSET 65 12
         END
     END
     METADATA
        "oms_title" "LIGHTS_POINT_SIGNATURE"
        "ows_enable_request"   "*"
        "gml_include_items" "all"
        "wms_feature_mime_type" "text/html"
     END
  END
{1}
            """.format(layer, mapfile, group, msd)  # noqa

        return mapfile

    def get_mapfile_data(self, layer, base, charts):

        data = 'DATA "{}"'.format('{}/{}'.format(layer, base))

        for chart in charts:
            if not chart['instruction']:
                continue
            parts = chart['instruction'].split(';')
            for part in parts:
                command = part[:2]
                details = part[3:-1]
                if command == 'SY' and ',' in details:
                    symbol, angle = details.split(',')
                    return """
CONNECTIONTYPE OGR
    CONNECTION "{0}/{1}.shp"
    DATA "SELECT *, 360 - {2} as {2}_CAL FROM {1}"
                    """.format(layer, base, angle)

        return data

    def get_point_mapfile_classes(self, charts, feature, fields):
        classes = ""

        for chart in charts:
            expression = self.get_expression(chart['rules'], fields)
            style = self.get_point_style(chart['instruction'], feature)
            if not style:
                continue
            classes += """
    CLASS # id: {2}
        {0}
        {1}
    END
            """.format(expression, style, chart['id'])

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

                classes[style_geom_type].append("""
    CLASS # id: {2}
        {0}
        {1}
    END""".format(expression, style, lookup['id']))

        classes['POINT'] = '\n'.join(classes['POINT'])
        classes['LINE'] = '\n'.join(classes['LINE'])
        classes['POLYGON'] = '\n'.join(classes['POLYGON'])
        return classes

    def get_expression(self, rules, fields):
        expression = ""

        expr = self.get_subexpression(rules, fields)

        if expr:
            expression = "EXPRESSION (" + " AND ".join(expr) + ")"

        return expression

    def get_subexpression(self, rules, fields):

        expr = []
        for attrib, value in rules:
            if attrib == '__OR__':
                expr.append(' OR '.join(self.get_subexpression(value, fields)))
            elif attrib == '__MS__':
                expr.append('({})'.format(value))
            else:
                if fields and attrib not in fields:
                    expr.append('FALSE')
                elif value == ' ':
                    expr.append('([{}] > 0)'.format(attrib))
                elif value.isdigit():
                    expr.append('([{}] == {})'.format(attrib, value))
                elif len(value) > 1 and value[0] in ['>', '<'] and \
                value[1:].isdigit():
                    operator = value[0]
                    digit = value[1:]
                    expr.append(
                        '([{}] {} {} )'.format(attrib, operator, digit)
                    )
                else:
                    expr.append('("[{}]" == "{}")'.format(attrib, value))

        return expr


    def get_point_style(self, instruction, feature):
        style = []

        if not instruction:
            return ''

        # Split on ;
        try:
            parts = instruction.split(';')
            for part in parts:
                command = get_command(part)
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
            for part in instruction.split(';'):
                command = get_command(part)
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
