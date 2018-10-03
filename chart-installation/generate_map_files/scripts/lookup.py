class Lookup:
    def __init__(self, id='', table=None, display=None, comment='',
                 instruction=None, rules=None):
        if rules is None:
            from filters import MSAnd
            rules = MSAnd()

        if instruction is None:
            instruction = []

        self.id = id
        self.table = table
        self.display = display
        self.comment = comment
        self.instruction = instruction
        self.rules = rules

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

    def add_instruction(self, instruction):
        for lookup in self:
            lookup.add_instruction(instruction)

    def __matmul__(self, other):
        return self.__class__(
            Lookup(l.id + r.id,
                   l.table,
                   l.display,
                   l.comment + r.comment,
                   l.instruction + r.instruction,
                   l.rules & r.rules)
            for l in self
            for r in other
            if (r.table is None or r.display == l.display)
            and (r.display is None or r.display == l.display)
        )

    def __add__(self, other):
        return self.__class__(self + other)
