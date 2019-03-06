from .filters import MSAnd
from .instructions import SY
from .layer import DisplayPriority


class Lookup:
    def __init__(self, id='', table=None, display=None, comment='',
                 instruction=None, rules=None,
                 display_priority=DisplayPriority.NotSet):
        if rules is None:
            rules = MSAnd()

        if instruction is None:
            instruction = []

        self.id = id
        self.table = table
        self.display = display
        self.comment = comment
        self.instruction = instruction
        self.rules = rules
        self.display_priority = display_priority

    @property
    def rot_field(self):
        for command in self.instruction:
            if isinstance(command, SY) and command.rot_field:
                return command.rot_field

    def get_expression(self, fields):
        if self.rules:
            return 'EXPRESSION ({})'.format(self.rules.to_expression(fields))

        return ''

    def get_styleitems(self, chartsymbols, feature_name, geom_type, fields):
        style = {
            'POINT': [],
            'LINE': [],
            'POLYGON': [],
        }
        for command in self.instruction:
            styleitem = command(chartsymbols, feature_name, geom_type, fields)
            if isinstance(styleitem, str):
                style[geom_type].append(styleitem)
            else:
                for style_type, style_str in styleitem.items():
                    style[style_type].append(style_str)

        return style

    def add_instruction(self, instruction):
        self.instruction.append(instruction)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError as e:
            raise KeyError(e)

    def __add__(self, other):
        return LookupCollection([self]) + other

    def __matmul__(self, other):
        return LookupCollection([self]) @ other

    def __iter__(self):
        return iter(LookupCollection([self]))


class LookupCollection(list):
    __slots__ = ()

    def __init__(self, seq, *, id=''):
        super().__init__(Lookup(id=id, **lookup)
                         if isinstance(lookup, dict)
                         else lookup
                         for lookup in seq)

        if not all(isinstance(item, Lookup) for item in self):
            raise TypeError('LookupCollection can only contain Lookups')

    def add_instruction(self, instruction):
        for lookup in self:
            lookup.add_instruction(instruction)

    def __matmul__(self, other):
        return self.__class__(
            Lookup(l.id + r.id,
                   l.table or r.table,
                   l.display or r.display,
                   l.comment + r.comment,
                   l.instruction + r.instruction,
                   l.rules & r.rules,
                   max(l.display_priority, r.display_priority),
                   )
            for l in self
            for r in other
            if (r.table is None or l.table is None or r.table == l.table)
            and (r.display is None or l.display is None
                 or r.display == l.display)
        )

    def __add__(self, other):
        return self.__class__(list.__add__(self, other))
