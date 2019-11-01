# -*- coding: utf-8 -*-

import os
from xml.etree import ElementTree as etree

from .cs import lookups_from_cs
from .filters import MSAnd, MSFilter
from .instructions import get_command, CS
from .layer import DisplayPriority, Layer, LightsLayer
from .lookup import Lookup
from .symbol import VectorSymbol, Pattern

# Imported for easier debugging
from utils import ExclusiveSet  # noqa


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


class ChartSymbols:

    color_table = {}  # type: dict

    symbols_def = {}

    point_lookups = {}

    line_lookups = {}

    polygon_lookups = {}

    excluded_lookups = ['M_QUAL']
    # excluded_lookups = ExclusiveSet('LIGHTS BCNLAT'.split())

    symbol_size_overwrite = {} 

    root = None

    def __init__(self, file, point_table='Simplified', area_table='Plain',
                 displaycategory=None, color_table='DAY_BRIGHT',
                 excluded_lookups=None, symbol_size_overwrite=None):
        if not os.path.isfile(file):
            raise Exception('chartsymbol file do not exists')

        if excluded_lookups is not None:
            self.excluded_lookups = excluded_lookups

        if symbol_size_overwrite is not None:
            self.symbol_size_overwrite = symbol_size_overwrite

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
            except Exception:
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
                display_priority = lookup.find('disp-prio').text
            except (KeyError, AttributeError):
                continue

            if name in self.excluded_lookups:
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
                    display_priority=DisplayPriority.get(display_priority)
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

            # Add virtual lookup for X-SNDG
            self.point_lookups['X-SNDG'] = list(
                Lookup(
                    id='X-SNDG',
                    comment='non-SOUNDG features with sounding',
                    display_priority=DisplayPriority.AreaSymbol,
                )
                @ [Lookup(table='Paper'), Lookup(table='Simplified')]
                @ lookups_from_cs('SOUNDG', 'Point', 'X-SNDG')
            )

    def get_maxscale_shift_layer(self, maxscale_shift, layer, msd):
       # maxscale shift are stored into config file based on array of 
       # tuple ["SOUNDG:0.1", ...].  
       # NOTE: layers are case senssitive
       for mxs in maxscale_shift:
           ly = mxs.split(":")
           if ly[0] == layer:
               return str(round(int(msd) * float(ly[1])))
       
       # Layer not funded, simply return original max scale
       return msd

    def get_point_mapfile(self, layer, feature, group, msd, fields,
                          metadata_name, maxscale_shift):

        # ajusting max scale for layer pointed in config file by user.
        msd_verified = self.get_maxscale_shift_layer(maxscale_shift, feature, msd) 

        layer = Layer(layer, feature, 'POINT', group, msd_verified, fields,
                      self.point_lookups.get(feature, []), self,
                      metadata_name)

        if feature == 'LIGHTS':
            layer = LightsLayer(layer)

        return layer

    def get_line_mapfile(self, layer, feature, group, max_scale_denom,
                         fields, metadata_name, maxscale_shift):
        # ajusting max scale for layer pointed in config file by user.
        msd_verified = self.get_maxscale_shift_layer(maxscale_shift, feature, max_scale_denom) 

        return Layer(layer, feature, 'LINE', group, msd_verified,
                     fields, self.line_lookups.get(feature, []), self,
                     metadata_name)

    def get_poly_mapfile(self, layer, feature, group, max_scale_denom,
                         fields, metadata_name, maxscale_shift):

        # ajusting max scale for layer pointed in config file by user.
        msd_verified = self.get_maxscale_shift_layer(maxscale_shift, feature, max_scale_denom)

        return Layer(layer, feature, 'POLYGON', group, msd_verified,
                     fields, self.polygon_lookups.get(feature, []), self,
                     metadata_name)


class AllInclusive:
    def __contains__(self, val):
        return True
