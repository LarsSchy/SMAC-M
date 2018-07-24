import abc
from enum import Enum
from operator import attrgetter
import os


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


class Pattern(metaclass=abc.ABCMeta):

    class FillType(Enum):
        Linear = 'L'
        Staggered = 'S'

    color = 'NODTA'
    gap = 0
    height = 0
    width = 0
    stroke_width = 0

    @classmethod
    def from_element(cls, element):
        if element.find('bitmap'):
            return BitmapPattern(element)
        if element.find('vector'):
            return VectorPattern(element)

    def __init__(self, element):
        self.name = element.find('name').text
        self.fill_type = self.FillType(element.find('filltype').text)

    def generate_bitmap(self, image, output_path):
        # Default implementation noops; BitmapPattern will override
        pass

    @property
    def size(self):
        return max(self.height, self.width)

    def as_style(self, color_table, ttt):
        return '''
    STYLE
        SYMBOL "{symbol}"
        COLOR {color}

        GAP {gap}
        SIZE {size}
        WIDTH {stroke_width}
    END
    '''.format(
        ttt=ttt,
        symbol=self.name,
        color=color_table[self.color].rgb,
        gap=self.size + self.gap,
        size=self.size,
        stroke_width=self.stroke_width,
    )

    @abc.abstractmethod
    def as_symbol(self, subdir):
        pass


class BitmapPattern(Pattern):
    def __init__(self, element):
        super().__init__(element)
        bitmap = element.find('bitmap')
        self.gap = int(bitmap.find('distance').attrib['min'])
        self.width = int(bitmap.attrib['width'])
        self.height = int(bitmap.attrib['height'])

        pivot = bitmap.find('pivot')
        self.pivot_x = int(pivot.attrib['x'])
        self.pivot_y = int(pivot.attrib['y'])

        location = bitmap.find('graphics-location')
        self.bitmap_x = int(location.attrib['x'])
        self.bitmap_y = int(location.attrib['y'])

    def generate_bitmap(self, image, output_path):
        with image[self.bitmap_x:self.bitmap_x + self.width,
                   self.bitmap_y:self.bitmap_y + self.height] as symbol:
            symbol.save(filename=os.path.join(output_path,
                                              self.name + '.png'))

    def as_symbol(self, symboltype):
        return """
    SYMBOL
        NAME "{symname}"
        TYPE PIXMAP
        IMAGE "symbols-{symboltype}/{symname}.png"
    END""".format(symname=self.name, symboltype=symboltype)


class VectorPattern(Pattern):
    def __init__(self, element):
        super().__init__(element)
        self.hpgl = element.find('HPGL').text
        vector = element.find('vector')
        origin = vector.find('origin')
        self.offset_x = int(origin.attrib['x'])
        self.offset_y = int(origin.attrib['y'])
        self.width = int(vector.attrib['width']) * 0.03
        self.height = int(vector.attrib['height']) * 0.03
        color_ref = element.find('color-ref').text
        self.color = color_ref[1:] or 'NODTA'  # Assume only one colour
        distance = vector.find('distance')
        self.gap = int(distance.attrib['min']) * 0.03

        self._parse_vector()

    def _parse_vector(self):
        self.points = []
        for instruction in self.hpgl.split(';'):
            if not instruction:
                continue

            command, args = instruction[:2], instruction[2:]
            if command == 'SP':
                pass  # Assume only one pen
            elif command == 'SW':
                self.stroke_width = int(args) * 0.3
            elif command == 'PU':
                if self.points:
                    self.points += [-99, -99]

                x, y = map(int, args.split(','))
                self.points += [x - self.offset_x, y - self.offset_y]
            elif command == 'PD':
                if not args:
                    continue  # The PU already set our point

                coordinates = map(int, args.split(','))
                for x, y in zip(coordinates, coordinates):
                    self.points += [x - self.offset_x, y - self.offset_y]
            else:
                import warnings
                warnings.warn('Pattern command not implemented: ' + command)


    def as_symbol(self, symboltype):
        return """
    SYMBOL
        NAME "{symname}"
        TYPE VECTOR
        POINTS
        {points}
        END
    END""".format(symname=self.name, points=' '.join(map(str, self.points)))
