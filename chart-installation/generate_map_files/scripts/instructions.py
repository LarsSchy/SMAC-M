import re
import warnings


class NotImplementedWarning(UserWarning):
    pass


pattern = re.compile(r'^([^(]+)\(([^)]+)\)$')


def get_command(instruction):
    match = pattern.match(instruction)

    Command_ = globals().get(match.group(1), Command)
    command = Command_(*match.group(2).split(','))
    command.set_command_name(match.group(1))
    return command


class Command:
    def __init__(self, *args):
        self.command = ''

    def set_command_name(self, command):
        self.command = command

    def __call__(self, chartsymbols, layer, geom_type):
        warnings.warn('Command not implemented: {}'.format(self.command),
                      NotImplementedWarning)
        return ''

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

    def __call__(self, chartsymbols, layer, geom_type):
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
        self.attributes = attributes.replace("'", '')
        self.hjust = hjust
        self.vjust = vjust
        self.space = space
        self.chars = chars
        self.xoffs = xoffs
        self.yoffs = yoffs
        self.colour = colour
        self.display = display
        super().__init__()

    def __call__(self, chartsymbols, layer, geom_type):

        text = re.sub(r'(%[^ ]*[a-z])[^a-z]', self.get_label_text, self.format)
        if ' + ' in text:
            text = '({})'.format(text)

        try:
            label_field = re.search(r'(\[[^\]]+\])', text).group(1)
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
            self.command,
            label_expr,
            self.vjustHash[self.vjust] + self.hjustHash[self.hjust],
            self.spaceHash[self.space],
            self.chars[-3:-1],
            self.xoffs, self.yoffs,
            chartsymbols.color_table[self.colour].rgb,
            text
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
        try:
            self.rot = int(rot)
        except ValueError:
            self.rot = '[{}_CAL]'.format(rot)

    def __call__(self, chartsymbols, layer, geom_type):
        # Hardcoded value to skip typo in official XML
        # TODO: Validate that the symbol exists
        if self.symbol == 'BCNCON81':
            return ''

        # OFFSET
        x = 0
        y = 0
        if self.symbol in chartsymbols.symbols_def:
            symbol = chartsymbols.symbols_def[self.symbol]
            x = -(symbol['size'][0] // 2)
            x += symbol['pivot'][0]
            y = symbol['size'][1] // 2
            y -= symbol['pivot'][1]

        return """
        STYLE
            SYMBOL "{}"
            OFFSET {} {}
            ANGLE {}
            GAP 2000
        END
        """.format(self.symbol, x, y, self.rot)


class LC(Command):
    """ShowLine 9.3"""
    def __init__(self, style):
        self.symbol = style

    def __call__(self, chartsymbols, layer, geom_type):
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

    def __call__(self, chartsymbols, layer, geom_type):
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

    def __call__(self, chartsymbols, layer, geom_type):
        return chartsymbols.area_symbols[self.pattern].as_style(
            chartsymbols.color_table, layer)


class CS(Command):
    """ CallSymproc 9.5"""
    # Dict of proc references to simpler styles.
    # Entries are searched in this order:
    #   1. Exact procname and layer name
    #   2. Exact procname
    #   3. Class code (First 6 characters of the procname)
    procs = {
        ('SLCONS03', 'SLCONS'): LS('SOLD', 2, 'CSTLN'),
        ('QUAPOS03', 'COALNE'): LS('SOLD', 1, 'CSTLN'),

        'QUAPOS01': LS('SOLD', 1, 'CSTLN'),
        'DEPCNT02': LS('SOLD', 1, 'DEPCN'),

        'OBSTRN': SY('ISODGR01'),
        'DEPARE': AC('DEPMS'),
    }

    def __init__(self, proc):
        self.proc = proc

    def __call__(self, chartsymbols, layer, geom_type):
        #   1. Exact procname and layer name
        subcmd = self.procs.get((self.proc, layer))

        if subcmd is None:
            #   2. Exact procname
            subcmd = self.procs.get(self.proc)

        if subcmd is None:
            #   3. Class code (First 6 characters of the procname)
            subcmd = self.procs.get(self.proc[:6])

        if subcmd:
            return subcmd(chartsymbols, layer, geom_type)
        else:
            warnings.warn(
                'Symproc not implemented: {}'.format((self.proc, layer)),
                NotImplementedWarning)
        return ''
