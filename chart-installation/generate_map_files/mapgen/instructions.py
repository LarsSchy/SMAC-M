import re
import warnings


class NotImplementedWarning(UserWarning):
    pass


pattern = re.compile(r'^([^(]+)\((.+?)\)?$', re.DOTALL)


def get_command(instruction):
    match = pattern.match(instruction)
    if match is None:
        command = Command()
        command.set_command_name(instruction)
        return command

    Command_ = globals().get(match.group(1), Command)
    command = Command_(*match.group(2).split(','))
    command.set_command_name(match.group(1))
    return command


class Command:
    def __init__(self, *args):
        self.command = ''

    def set_command_name(self, command):
        self.command = command

    def __call__(self, chartsymbols, layer, geom_type, fields):
        warnings.warn('Command not implemented: {}'.format(self.command),
                      NotImplementedWarning)
        return ''

    def __iter__(self):
        return iter([self])

    def __add__(self, other):
        if isinstance(other, Command):
            return [self, other]

        if isinstance(other, list):
            return [self] + other

        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, list):
            return other + [self]

        return NotImplemented

    @staticmethod
    def units(value):
        return float(value)


class LS(Command):
    """ShowLine: 9.3"""

    patterns = {
        'SOLD': '',
        'DASH': 'PATTERN 12 6 END',
        'DOTT': 'PATTERN 2 4 END',
    }

    def __init__(self, pattern, width, color):
        self.pattern = pattern
        self.width = width
        self.color = color

    def __call__(self, chartsymbols, layer, geom_type, fields):
        style = '''
        STYLE
            COLOR {color}
            WIDTH {width}
            LINECAP ROUND
            LINEJOIN ROUND
            {pattern}
        END
            '''.format(
                color=chartsymbols.color_table[self.color].rgb,
                width=self.units(self.width),
                pattern=self.patterns.get(self.pattern, ''),
            )
        if geom_type == 'POLYGON':
            return {'LINE': style}
        else:
            return style


class TE(Command):
    """ShowText 9.1"""

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

    def __init__(self, format, attributes, hjust, vjust, space, chars,
                 xoffs, yoffs, colour, display):
        self.format = format
        self.attributes = attributes.strip("'")
        self.hjust = str(hjust)
        self.vjust = str(vjust)
        self.space = str(space)
        self.chars = chars
        self.xoffs = xoffs
        self.yoffs = yoffs
        self.colour = colour
        self.display = display
        super().__init__()

    def __call__(self, chartsymbols, layer, geom_type, fields):
        text = re.sub(r'(%[^ ]*[a-z])[^a-z]', self.get_label_text, self.format)
        if ' + ' in text:
            text = '({})'.format(text)

        def force_labels(match):
            field = match.group(1)
            if field + '_txt' in fields:
                return '[{}_txt]'.format(field)

            return match.group(0)

        text = re.sub(r'\[([^\]]+)\]', force_labels, text)
        
        try:
            label_field = re.search(r'(\[[^\]]+\])', text).group(1)
            label_expr = 'EXPRESSION ("{}" > "0")'.format(label_field)
        except AttributeError:
            # AAA, ZZZ not found in the original string
            label_expr = ''  # apply your error handling

        return """
        LABEL  # {command}
            {label}
            TYPE TRUETYPE
            FONT SC
            PARTIALS TRUE
            MINDISTANCE 0
            POSITION {vjust}{hjust}
            {space}
            SIZE {size}
            OFFSET {xoff} {yoff}
            COLOR {color}
            TEXT {text}
        END
        """.format(
            command=self.command,
            label=label_expr,
            vjust=self.vjustHash[self.vjust],
            hjust=self.hjustHash[self.hjust],
            space=self.spaceHash[self.space],
            size=self.chars[-4:-2],
            xoff=self.xoffs,
            yoff=self.yoffs,
            color=chartsymbols.color_table[self.colour].rgb,
            text=text
        )

    def get_label_text(self, matches):
        # TODO: Support multi attributes
        s = self.attributes

        if matches.group(1) == '%s':
            return matches.group(0).replace('%s', '[{}]'.format(s))
        else:
            return matches.group(0).replace(
                matches.group(1),
                "' + tostring([" + s + "], '" + matches.group(1) + "') + '")


class TX(TE):
    """ShowText 9.1"""

    def __init__(self, attributes, hjust, vjust, space, chars,
                 xoffs, yoffs, colour, display):
        format = "'%s'"
        super().__init__(format,  attributes, hjust, vjust, space, chars,
                         xoffs, yoffs, colour, display)


class SY(Command):
    """ShowPoint 9.2"""

    def __init__(self, symbol, rot=0):
        self.symbol = symbol
        self.rot_field = None
        try:
            self.rot = int(rot)
        except ValueError:
            self.rot_field = rot
            self.rot = '[{}_CAL]'.format(rot)

    def __call__(self, chartsymbols, layer, geom_type, fields):
        # OFFSET
        x = 0
        y = 0

        # Hardcoded value to skip typo in official XML
        # TODO: Validate that the symbol exists
        if self.symbol == 'BCNCON81':
            return ''
        if self.symbol == 'FOGSIG01':
            x = -15

        if self.symbol in chartsymbols.symbols_def:
            symbol_name = self.symbol
        else:
            symbol_name = 'QUESMRK1'

        symbol = chartsymbols.symbols_def[symbol_name]
        x += -(symbol['size'][0] // 2)
        x += symbol['pivot'][0]
        y += symbol['size'][1] // 2
        y -= symbol['pivot'][1]

        geomtransform = ''
        if geom_type == 'POLYGON':
            geomtransform = 'GEOMTRANSFORM centroid'

        return """
        STYLE
            {geomtransform}
            SYMBOL "{symbol}"
            OFFSET {x} {y}
            ANGLE {angle}
            GAP 2000
        END
        """.format(symbol=symbol_name, x=x, y=y, angle=self.rot,
                   geomtransform=geomtransform)


class LC(Command):
    """ShowLine 9.3"""
    def __init__(self, style):
        self.symbol = style

    def __call__(self, chartsymbols, layer, geom_type, fields):
        style = chartsymbols.line_symbols[self.symbol].as_style(
            chartsymbols.color_table)
        if geom_type == 'POLYGON':
            return {'LINE': style}
        else:
            return style


class AC(Command):
    """ShowArea 9.4"""
    def __init__(self, color, transparency='0'):
        self.color = color
        # MapServer uses Opacity, OpenCPN uses trnasparency
        self.opacity = (4 - int(transparency)) * 25

    def __call__(self, chartsymbols, layer, geom_type, fields):
        return """
        STYLE
            COLOR {}
            OPACITY {}
        END
        """.format(chartsymbols.color_table[self.color].rgb, self.opacity)


class AP(Command):
    """ShowArea 9.4"""
    def __init__(self, pattern):
        self.pattern = pattern

    def __call__(self, chartsymbols, layer, geom_type, fields):
        return chartsymbols.area_symbols[self.pattern].as_style(
            chartsymbols.color_table)


class CS(Command):
    """ CallSymproc 9.5"""
    def __init__(self, proc):
        self.proc = proc

    def __call__(self, chartsymbols, layer, geom_type, fields):
        warnings.warn(
            'Symproc left in lookup: {}'.format((self.proc, layer)),
            NotImplementedWarning)

        return ''


class _MS(Command):
    """Command that emits hardcoded mapserver code.

    To be used with CS procedures that are too complex to be represented by S52
    instructions.
    """

    def __init__(self, *style):
        # get_command splits on comma. we need to readd the commas if there
        # were any
        self.style = ','.join(style)

    def __call__(self, chartsymbols, layer, geom_type, fields):
        return self.style.format(color=chartsymbols.color_table)
