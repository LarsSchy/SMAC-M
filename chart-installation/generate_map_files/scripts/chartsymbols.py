# -*- coding: utf-8 -*-

import os
import re
from xml.etree import ElementTree as etree

class ChartSymbols():

    color_table = {}

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
            if lookup_type == 'Point' and style == table_name and id != '1794':
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
        base = "CL{}-point-{}".format(layer, feature)

        try:
            charts = self.point_lookups[feature]
        except:
            return mapfile

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
    DATA "{4}"
{5}
END

# END of  LAYER: {1}  LEVEL: {0}
        """.format(layer, feature, group, msd, '{}/{}'.format(layer, base), classes)

        return mapfile

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
            if rule[1].isdigit():
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
        except:
            raise
            return ""

        return style

    def get_symbol(self, details):
        # Hardcoded value to skip typo in official XML
        # TODO: Validate that the symbol exists
        if details == 'BCNCON81':
            return ''
        return """
        STYLE
            SYMBOL "{}"
        END
        """.format(details)

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
                return format.replace('%s', '[{}]'.format(s))
            else:
                return format.replace(
                    matches.group(1),
                    "' + tostring(["+ s +"], '"+matches.group(1)+"') + '")

        text = re.sub(r'(%[^ ]*[a-z])[^a-z]', get_label_text, format)

        return """
        LABEL  # {}
            TYPE TRUETYPE
            FONT SC
            PARTIALS TRUE
            MINDISTANCE 0
            POSITION {}
            {}
            SIZE {}
            OFFSET {} {}
            COLOR {}
            TEXT ({})
        END
        """.format(
            command,
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
        END
        """
