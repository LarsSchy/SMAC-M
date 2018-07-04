from operator import attrgetter


class VectorSymbol:

    def __new__(cls, element):
        if element.find('HPGL') is not None:
            return super().__new__(cls)

        return None

    def __init__(self, element):
        self.element = element
        self.name = element.find('name').text
        self.hpgl = element.find('HPGL').text
        vector = element.find('vector')
        origin = vector.find('origin')
        self.offset_x = int(origin.attrib['x'])
        self.offset_y = int(origin.attrib['y'])
        self.width = int(vector.attrib['width'])
        self.height = int(vector.attrib['height'])

        self.subsymbols = []
        self._parse_colors()
        self._parse_vector_symbol()

    def as_style(self, color_table):
        return '\n\n'.join(s.as_style(color_table) for s in self.subsymbols)

    @property
    def as_symbol(self):
        return '\n\n'.join(s.as_symbol for s in self.subsymbols)

    def _parse_vector_symbol(self):
        pen = '-'
        width = 1
        points = []
        polygon_buffer = []
        position = (None, None)
        opacity = 100
        subsymbols = []
        for instruction in self.hpgl.split(';'):
            if not instruction:
                continue

            command, args = instruction[:2], instruction[2:]
            if command == 'SP':
                if pen != args and len(points) > 2:
                    subsymbols.append(SubSymbol(self, pen, width,
                                                opacity, points))

                pen = args
            elif command == 'SW':
                width = int(args)
            elif command == 'ST':
                opacity = 100 - (int(args) * 25)
            elif command == 'PM':
                if len(points) > 2:
                    subsymbols.append(SubSymbol(self, pen, width,
                                                opacity, points))

                if args == '2':
                    # Exit polygon mode
                    polygon_buffer = list(points)
                elif args == '0':
                    # Enter polygon mode
                    points = list(position)
                else:
                    raise Exception('Subpolygons are not implemented')
            elif command == 'PU':
                if len(points) > 2:
                    subsymbols.append(SubSymbol(self, pen, width,
                                                opacity, points))

                coordinates = map(int, args.split(','))
                for x, y in zip(coordinates, coordinates):
                    position = (x - self.offset_x, y - self.offset_y)

                points = list(position)
            elif command == 'PD':
                coordinates = map(int, args.split(','))
                for x, y in zip(coordinates, coordinates):
                    position = (x - self.offset_x, y - self.offset_y)
                    points.extend(position)
            elif command == 'FP':
                subsymbols.append(SubSymbol(self, pen, width, opacity,
                                            polygon_buffer, filled=True))
            elif command == 'EP':
                subsymbols.append(SubSymbol(self, pen, width, opacity,
                                            polygon_buffer))
            elif command == 'CI':
                pass
            else:
                import warnings
                warnings.warn('Not implemented: ' + command)

        if len(points) > 2:
            subsymbols.append(SubSymbol(self, pen, width,
                                        opacity, points))

        self.subsymbols = self._merge_symbols(subsymbols)

    def _parse_colors(self):
        color_ref = self.element.find('color-ref').text
        self.colors = {}
        while color_ref:
            color, color_ref = color_ref[:6], color_ref[6:]
            self.colors[color[0]] = color[1:]

    def _merge_symbols(self, subsymbols):
        subsymbols.sort(key=attrgetter('center'))
        merged_symbols = []
        while subsymbols:
            symbol = subsymbols.pop()
            for i, other in reversed(list(enumerate(subsymbols))):
                if other & symbol:
                    subsymbols.pop(i)
                    symbol.merge(other)

            merged_symbols.append(symbol)

        for i, symbol in enumerate(merged_symbols):
            symbol.set_name('{}_{}'.format(self.name, i))

        return merged_symbols


class SubSymbol:
    vector_template = """
    SYMBOL
        NAME "{symname}"
        TYPE VECTOR
        FILLED {filled}
        POINTS
        {points}
        END
    END"""

    style_template = """
    STYLE
        SYMBOL "{symbol}"
        COLOR {color}

        INITIALGAP {initialgap}
        GAP -{gap}
        SIZE {size}
        WIDTH {stroke_width}
        OPACITY {opacity}
        ANGLE AUTO
    END
    """

    def __init__(self, parent, pen, width, opacity, points, filled=False):
        self.parent = parent
        self.pen = pen
        self.stroke_width = width
        self.opacity = opacity
        self.points = points
        self.filled = filled
        self.name = parent.name
        self._calc_extremes()

    def _calc_extremes(self):
        self.left = min(p for p in self.points[::2] if p != -99)
        self.right = max(self.points[::2])
        self.top = min(p for p in self.points[1::2] if p != -99)
        self.bottom = max(self.points[1::2])

    def set_name(self, name):
        self.name = name

    @property
    def center(self):
        return (self.left + self.right) / 2

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def normalised_points(self):
        for i in range(0, len(self.points), 2):
            if self.points[i] == -99:
                yield -99
                yield -99
            else:
                yield self.points[i] - self.left
                yield self.points[i + 1] - self.top

    def __and__(self, other):
        if not isinstance(other, SubSymbol):
            return NotImplemented

        # Symbols only overlap if each contain the other's center
        if not (other.left <= self.center <= other.right) and (
                self.left <= other.center <= other.right):
            return False

        return (
            self.pen == other.pen
            and self.stroke_width == other.stroke_width
            and self.opacity == other.opacity
            and self.filled == other.filled
        )

    def merge(self, other):
        self.points += [-99, -99] + other.points
        self._calc_extremes()

    @property
    def as_symbol(self):
        return self.vector_template.format(
            symname=self.name,
            filled=self.filled,
            points=' '.join(map(str, self.normalised_points)),
        )

    def as_style(self, color_table):
        color_key = self.parent.colors.get(self.pen, 'NODTA')
        return self.style_template.format(
            symbol=self.name,
            color=color_table[color_key].rgb,
            opacity=self.opacity,
            size=self.height * 0.03,
            stroke_width=0.3 * self.stroke_width,
            # We use a slightly larger ratio for the gap to prevent
            # overcrowding
            initialgap=self.center * 0.04,
            gap=self.parent.width * 0.04,
        )
