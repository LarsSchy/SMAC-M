# -*- coding: utf-8 -*-

import os
import re
import math
from xml.etree import ElementTree as etree

class ChartSymbols():

    color_table = {}

    symbols_def = {}

    point_lookups = {}

    line_lookups = {}

    polygon_lookups = {}

    root = None

    def __init__(self, file, table='Simplified', color_table='DAY_BRIGHT'):
        if not os.path.isfile(file):
            raise Exception('chartsymbol file do not exists')
        tree = etree.parse(file)
        root = tree.getroot()
        self.root = root

        self.color_table = {}
        self.point_lookups = {}
        self.line_lookups = {}
        self.polygon_lookups = {}

        self.load_color_table(root, color_table)
        self.load_symbols(root)
        self.load_lookups(root, table)

    def load_colors(self, color_table):
        self.color_table = {}
        self.load_color_table(self.root, color_table)

    def load_color_table(self, root, color_table):
        for table in root.iter('color-table'):
            name = table.get('name')
            if name != color_table:
                continue
            colors = {}
            for color in table.iter('color'):
                colors[color.get('name')] = [
                    color.get('r'),
                    color.get('g'),
                    color.get('b')
                ]
            self.color_table = colors

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

    def load_lookups(self, root, style):
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
                    #index = int(attr.get('index'))
                    rules.append((attr.text[:6], attr.text[6:]))
            except:
                continue

            # Only load points for now
            if lookup_type == 'Point' and style == table_name:
                if not name in self.point_lookups:
                    self.point_lookups[name] = []
                self.point_lookups[name].append({
                    'id': id,
                    'table': table_name,
                    'display': display,
                    'comment': comment,
                    'instruction': instruction,
                    'rules': rules,
                })

    def get_point_mapfile(self, layer, feature, group, msd):
        mapfile = ''
        base = "CL{}_{}_POINT".format(layer, feature)

        try:
            charts = self.point_lookups[feature]
        except:
            return mapfile

        data = self.get_point_mapfile_data(layer, base, charts)
        classes = self.get_point_mapfile_classes(charts)

        mapfile = """
# LAYER: {1}  LEVEL: {0}

LAYER
    NAME "{1}_{0}"
    GROUP "{2}"
    METADATA
        "ows_title" "{1}"
        "ows_enable_request"   "*"
        "gml_include_items" "all"
        "wms_feature_mime_type" "text/html"
    END
    TEMPLATE blank.html
    TYPE POINT
    STATUS ON
    MAXSCALEDENOM {3}
    {4}
{5}
END

# END of  LAYER: {1}  LEVEL: {0}
        """.format(layer, feature, group, msd, data, classes)

        return mapfile

    def get_point_mapfile_data(self, layer, base, charts):

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

    def get_point_mapfile_classes(self, charts):
        classes = ""

        for chart in charts:
            expression = self.get_expression(chart['rules'])
            style = self.get_point_style(chart['instruction'])
            if not style:
                continue
            classes += """
    CLASS # id: {2}
        {0}
        {1}
    END
            """.format(expression, style, chart['id'])

        return classes

    def get_expression(self, rules):
        expression = ""

        expr = []
        for rule in rules:
            if rule[1] == ' ':
                expr.append('([{}] > 0)'.format(rule[0]))
            elif rule[1].isdigit():
                expr.append('([{}] == {})'.format(rule[0], rule[1]))
            else:
                expr.append('("[{}]" == "{}")'.format(rule[0], rule[1]))

        if expr:
            expression = "EXPRESSION (" + " AND ".join(expr) + ")"

        return expression

    def get_point_style(self, instruction):
        style = ""

        # Split on ;
        try:
            parts = instruction.split(';')
            for part in parts:
                command = part[:2]
                details = part[3:-1]

                # Symbol
                if command == "SY":
                    style += self.get_symbol(details)

                if command in ["TX", "TE"]:
                    style += self.get_label(command, details)

                if command == 'CS':
                    # CS is special logic
                    if details[:-2] == 'SOUNDG':
                        style += self.get_soundg()
                    if details[:-2] == 'LIGHTS':
                        style += self.get_lights_point()

        except:
            return ""

        return style

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
            '1': '', # 1 Is not usde
            '2': '', # Standard spaces
            '3': 'MAXLENGTH 8\n            WRAP " "' # Wrap on spaces
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
                    "' + tostring(["+ s +"], '"+matches.group(1)+"') + '")

        text = re.sub(r'(%[^ ]*[a-z])[^a-z]', get_label_text, format)
        if ' + ' in text:
            text = '({})'.format(text)
        try:
            label_field = re.search('(\[[^\]]+\])', text).group(1)
            label_expr = 'EXPRESSION ("{}" > "0")'.format(label_field)
        except AttributeError:
            # AAA, ZZZ not found in the original string
            label_expr = '' # apply your error handling

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
            ' '.join(self.color_table[colour]),
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
        """
