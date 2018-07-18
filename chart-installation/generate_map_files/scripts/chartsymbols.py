# -*- coding: utf-8 -*-

import os
import re
from symbol import VectorSymbol
import math
from xml.etree import ElementTree as etree

from instructions import get_command


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
                instruction = lookup.find('instruction').text
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

                lookup.append({
                    'id': id,
                    'table': table_name,
                    'display': display,
                    'comment': comment,
                    'instruction': instruction,
                    'rules': rules,
                })

    def get_point_mapfile(self, layer, feature, group, msd):
        base = "CL{}_{}_POINT".format(layer, feature)

        try:
            charts = self.point_lookups[feature]
        except KeyError:
            return ''

        data = self.get_mapfile_data(layer, base, charts)
        classes = self.get_point_mapfile_classes(charts, feature)

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

    def get_point_mapfile_classes(self, charts, feature):
        classes = ""

        for chart in charts:
            expression = self.get_expression(chart['rules'])
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

    def get_line_mapfile(self, layer, feature_type, group, max_scale_denom):
        base = "CL{}_{}_LINESTRING".format(layer, feature_type)

        try:
            lookups = self.line_lookups[feature_type]
        except KeyError:
            return ''

        return self._get_mapfile(layer, feature_type, group, max_scale_denom,
                                 base, lookups, 'LINE')

    def get_poly_mapfile(self, layer, feature_type, group, max_scale_denom):
        base = "CL{}_{}_POLYGON".format(layer, feature_type)

        try:
            lookups = self.polygon_lookups[feature_type]
        except KeyError:
            return ''

        return self._get_mapfile(layer, feature_type, group, max_scale_denom,
                                 base, lookups, 'POLYGON')

    def _get_mapfile(self, layer, feature_type, group, max_scale_denom,
                     base, lookups, type):
        data = self.get_mapfile_data(layer, base, lookups)
        classes = self.get_mapfile_classes(lookups, feature_type, type)

        mapfile = self.mapfile_layer_template.format(
            layer=layer, feature=feature_type, group=group, type=type,
            max_scale_denom=max_scale_denom, data=data, classes=classes)

        return mapfile

    def get_mapfile_classes(self, lookups, feature, geom_type):
        classes = []

        for lookup in lookups:
            expression = self.get_expression(lookup['rules'])
            style = self.get_styleitems(lookup['instruction'], feature,
                                        geom_type)
            if not style:
                continue

            classes.append("""
    CLASS # id: {2}
        {0}
        {1}
    END""".format(expression, style, lookup['id']))

        return '\n'.join(classes)

    def get_expression(self, rules):
        expression = ""

        expr = []
        for attrib, value in rules:
            if value == ' ':
                expr.append('([{}] > 0)'.format(attrib))
            elif value.isdigit():
                expr.append('([{}] == {})'.format(attrib, value))
            else:
                expr.append('("[{}]" == "{}")'.format(attrib, value))

        if expr:
            expression = "EXPRESSION (" + " AND ".join(expr) + ")"

        return expression

    def get_point_style(self, instruction, feature):
        style = []

        if not instruction:
            return ''

        # Split on ;
        try:
            parts = instruction.split(';')
            for part in parts:
                command = part[:2]
                details = part[3:-1]

                # Symbol
                # if command == "SY":
                #    style.append(self.get_symbol(details))

                if command in ["TX", "TE", "SY"]:
                    command = get_command(part)
                    style.append(command(self, feature, 'POINT'))

                if command == 'CS':
                    # CS is special logic
                    if details[:-2] == 'SOUNDG':
                        style.append(self.get_soundg())
                    if details[:-2] == 'LIGHTS':
                        style.append(self.get_lights_point())

        except:
            return ""

        return '\n'.join(style)

    def get_styleitems(self, instruction, feature, geom_type):
        style = []
        try:
            for part in instruction.split(';'):
                command = get_command(part)
                style.append(command(self, feature, geom_type))

            return '\n'.join(filter(None, style))
        except:
            return ''

    def get_symbol(self, details):
        # Hardcoded value to skip typo in official XML
        # TODO: Validate that the symbol exists
        if details == 'BCNCON81':
            return ''

        # OFFSET
        x = 0
        y = 0
        if details in self.symbols_def:
            symbol = self.symbols_def[details]
            x = math.floor(symbol['size'][0] / 2) * -1
            x += symbol['pivot'][0]
            y = math.floor(symbol['size'][1] / 2)
            y -= symbol['pivot'][1]

        # ANGLE
        angle = 0
        if ',' in details:
            details, angle = details.split(',')
            angle = '[{}_CAL]'.format(angle)

        return """
        STYLE
            SYMBOL "{}"
            OFFSET {} {}
            ANGLE {}
        END
        """.format(details, x, y, angle)

    def get_label(self, command, details):
        hjustHash = {
            '1': 'C',
            '2': 'R',
            '3': 'L'
        }
        vjustHash = {
            '1': 'L',
            '2': 'C',
            '3': 'T'
        }
        spaceHash = {
            '1': '',  # 1 Is not usde
            '2': '',  # Standard spaces
            '3': 'MAXLENGTH 8\n            WRAP " "'  # Wrap on spaces
        }
        details = details.split(',')

        # label TX
        # FORMAT:
        #   (STRING, HJUST, VJUST, SPACE, "CHARS", XOFFS, YOFFS,
        #    COLOUR, DISPLAY);
        if command == "TX":
            format = "'%s'"
            details.insert(0, format)

        # label TE
        # FORMAT:
        #   ("FORMAT", "ATTRIB1,ATTRIB2,...", HJUST, VJUST, SPACE,
        #    CHARS, XOFFS, YOFFS, COLOUR, DISPLAY);

        format, attributes, hjust, vjust, space, chars, \
            xoffs, yoffs, colour, display = details

        # TODO: Support multi attributes
        def get_label_text(matches):
            s = attributes
            if "'" in attributes:
                s = attributes[1:-1]
            if matches.group(1) == '%s':
                return matches.group(0).replace('%s', '[{}]'.format(s))
            else:
                return matches.group(0).replace(
                    matches.group(1),
                    "' + tostring([" + s + "], '"+matches.group(1)+"') + '")

        text = re.sub(r'(%[^ ]*[a-z])[^a-z]', get_label_text, format)
        if ' + ' in text:
            text = '({})'.format(text)
        try:
            label_field = re.search('(\[[^\]]+\])', text).group(1)
            label_expr = 'EXPRESSION ("{}" > "0")'.format(label_field)
        except AttributeError:
            # AAA, ZZZ not found in the original string
            label_expr = ''  # apply your error handling

        return """
        LABEL  # {}
            {}
            TYPE TRUETYPE
            FONT SC
            PARTIALS TRUE
            MINDISTANCE 0
            POSITION {}
            {}
            SIZE {}
            OFFSET {} {}
            COLOR {}
            TEXT {}
        END
        """.format(
            command,
            label_expr,
            vjustHash[vjust] + hjustHash[hjust],
            spaceHash[space],
            chars[-3:-1],
            xoffs, yoffs,
            self.color_table[colour].rgb,
            text
        )

    def get_soundg(self):
        return """
        LABEL
            TEXT (round([DEPTH]+(-0.5),1))
            TYPE TRUETYPE
            FONT sc
            COLOR 136 152 139
            SIZE 8
            ANTIALIAS TRUE
            FORCE TRUE
        END

        LABEL
            EXPRESSION ([DEPTH] > 10 AND [DEPTH] < 31)
            TEXT ( [DEPTH] * 10 % 10)
            OFFSET 8 4
            TYPE TRUETYPE
            FONT sc
            COLOR 136 152 139
            SIZE 7
            ANTIALIAS TRUE
            FORCE TRUE
        END

        LABEL
            EXPRESSION ([DEPTH] < 10)
            TEXT ( [DEPTH] * 10 % 10)
            OFFSET 5 4
            TYPE TRUETYPE
            FONT sc
            COLOR 136 152 139
            SIZE 6
            ANTIALIAS TRUE
            FORCE TRUE
        END
        """

    def get_lights_point(self):
        # See 13.2.4 Conditional Symbology Procedure LIGHTS06
        return """
         EXPRESSION ([CATLIT] == 11 OR [CATLIT] == 8)
         STYLE
             SYMBOL 'LIGHTS82'
         END
     END
     CLASS
        EXPRESSION ([CATLIT] == 9)
        STYLE
            SYMBOL 'LIGHTS81'
        END
     END
     CLASS
        EXPRESSION (([CATLIT] == 1 OR [CATLIT] == 16) AND "[ORIENT]" == "null")
        STYLE
            SYMBOL 'LIGHTS81'
        END
     END
     # No symbol
     CLASS
        EXPRESSION ([VALNMR] >= 10 AND NOT ("[CATLIT]" ~ "5" OR "[CATLIT]" ~ "6") AND [LITCHR] != 12)
     END
     CLASS
        EXPRESSION ("[COLOUR]" == "3,1" OR "[COLOUR]" == "3")
        STYLE
            SYMBOL 'LIGHTS11'
            OFFSET 9 9
        END
     END
     CLASS
        EXPRESSION ("[COLOUR]" == "4,1" OR "[COLOUR]" == "4")
        STYLE
            SYMBOL 'LIGHTS12'
            OFFSET 9 9
        END
     END
     CLASS
        EXPRESSION ("[COLOUR]" == "11" OR "[COLOUR]" == "6" OR "[COLOUR]" == "1")
        STYLE
            SYMBOL 'LIGHTS13'
            OFFSET 9 9
        END
        """  # noqa
