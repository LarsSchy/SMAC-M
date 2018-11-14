from abc import ABC, abstractmethod
from enum import Enum

class _MSFilterBase(ABC):
    __slots__ = ()
    def __and__(self, other):
        if isinstance(other, MSAnd):
            return NotImplemented

        return MSAnd(self, other)

    def __rand__(self, other):
        if isinstance(other, MSAnd):
            return NotImplemented

        return MSAnd(other, self)

    def __or__(self, other):
        if isinstance(other, MSOr):
            return NotImplemented

        return MSOr(self, other)

    def __ror__(self, other):
        if isinstance(other, MSOr):
            return NotImplemented

        return MSOr(other, self)


class MSFilter(_MSFilterBase):
    __slots__ = ('field',)
    def __init__(self, field):
        self.field = field

    def to_expression(self, fields):
        if fields and self.field not in fields:
            return 'FALSE'

        return '({})'.format(self.render_expression())

    @abstractmethod
    def render_expression(self):
        pass

    @staticmethod
    def from_attrcode(attrcode):
        attrib, value = attrcode[:6], attrcode[6:]
        if value == ' ':
            return MSHasValue(attrib)
        if value.isdigit():
            return MSCompare(attrib, value)

        return MSStrCompare(attrib, value)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.render_expression())


class MSRawFilter(_MSFilterBase):
    __slots__ = ('expression',)
    def __init__(self, expression):
        self.expression = expression

    def to_expression(self, fields):
        return '({})'.format(self.expression)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.render_expression())


class MSHasValue(MSFilter):
    __slots__ = ()
    def render_expression(self):
        return '"[{0}]" != ""'.format(self.field)


class MSCompare(MSFilter):
    __slots__ = ('op', 'value')
    class OP(str, Enum):
        LT = '<'
        LE = '<='
        GT = '>'
        GE = '>='
        EQ = '='
        NE = '!='

        # Operators for strings
        RE = '~'
        IRE = '~*'

    def __init__(self, field, value, op=OP.EQ):
        super().__init__(field)
        self.op = op
        self.value = value

    def render_expression(self):
        return '[{}] {} {}'.format(self.field, self.op, self.value)


class MSStrCompare(MSCompare):
    __slots__ = ()
    def render_expression(self):
        return '"[{}]" {} "{}"'.format(self.field, self.op, self.value)

    @classmethod
    def includes(cls, field, *values):
        return cls(
            field,
            r'\b({})\b'.format('|'.join(str(v) for v in values)),
            cls.OP.RE
        )


class _MSCombiner(list, _MSFilterBase):
    __slots__ = ()
    def __init__(self, *filters):
        super().__init__(filters)

    def to_expression(self, fields):
        return '({})'.format(self.separator.join(f.to_expression(fields)
                                                 for f in self))

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, [repr(f) for f in self])

    def extend(self, other):
        if type(self) is type(other):
            super().extend(other)
        else:
            self.append(other)


class MSAnd(_MSCombiner):
    __slots__ = ()
    separator = ' AND '

    def __and__(self, other):
        if type(self) is type(other):
            return MSAnd(*self, *other)

        return MSAnd(*self, other)

    def __rand__(self, other):
        if type(self) is type(other):
            return MSAnd(*other, *self)

        return MSAnd(other, *self)


# Alias for symbols with no rules
MSNoRules = MSAnd


class MSOr(_MSCombiner):
    __slots__ = ()
    separator = ' OR '

    def __or__(self, other):
        if type(self) is type(other):
            return MSOr(*self, *other)

        return MSOr(*self, other)

    def __ror__(self, other):
        if type(self) is type(other):
            return MSOr(*other, *self)

        return MSOr(other, *self)
