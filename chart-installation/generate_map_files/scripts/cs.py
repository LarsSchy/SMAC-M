import warnings


class NotImplementedWarning(UserWarning):
    pass


def lookups_from_cs(detail, lookup_type):

    function_name = detail[:6]
    function = globals().get(function_name)

    if function:
        return function(lookup_type)

    warnings.warn('Symproc not implemented: {}'.format(function_name),
                  NotImplementedWarning)

    # Return default lookup
    return [{
        'instruction': '',
        'rules': [],
    }]


def DEPARE(lookup_type):

    # These values are normally passed by the mariner
    # safety_contour = 10
    # shallow_contour = 20
    # deep_contour = 30

    # Basic implementation of DEPARE constructed symbol.
    # We are missing all the line and fill symbology
    return [{
        'instruction': 'AC(DEPIT)',
        'rules': [('DRVAL2', '<0')],
    },{
        'instruction': 'AC(DEPVS)',
        'rules': [('DRVAL2', '<10')],
    },{
        'instruction': 'AC(DEPMS)',
        'rules': [('DRVAL2', '<20')],
    },{
        'instruction': 'AC(DEPMD)',
        'rules': [('DRVAL2', '<30')],
    },{
        'instruction': 'AC(DEPDW)',
        'rules': [],
    }]


def LIGHTS(lookup_type):
    return [{
        'instruction': 'SY(LIGHTS82)',
        'rules': [('__OR__', [('CATLIT', '11'), ('CATLIT', '8')])],
    }, {
        'instruction': 'SY(LIGHTS81)',
        'rules': [('CATLIT', '9')],
    }, {
        'instruction': 'SY(LIGHTS81)',
        'rules': [('__OR__', [('CATLIT', '1'), ('CATLIT', '16')]),
                  ('ORIENT', 'null')],
    }, {
        'instruction': '',
        'rules': [('VALNMR', '>10'),
                  ('__MS__', 'NOT ("[CATLIT]" ~ "5" OR "[CATLIT]" ~ "6")'),
                  ('__MS__', '[LITCHR] != 12')],
    }, {
        'instruction': 'SY(LIGHTS11)',
        'rules': [('__OR__', [('COLOUR', '3,1'), ('COLOUR', '3')])],
    }, {
        'instruction': 'SY(LIGHTS12)',
        'rules': [('__OR__', [('COLOUR', '4,1'), ('COLOUR', '4')])]
    }, {
        'instruction': 'SY(LIGHTS13)',
        'rules': [('__OR__', [
            ('COLOUR', '11'), ('COLOUR', '6'), ('COLOUR', '1')
        ])],
    }]


def SOUNDG(lookup_type):
    return [{
        'instruction':
        '''_MS(
        LABEL
            TEXT (round([DEPTH]+(-0.5),1))
            TYPE TRUETYPE
            FONT sc
            COLOR {color[CHGRD].rgb}
            # COLOR 136 152 139
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
            COLOR {color[CHGRD].rgb}
            # COLOR 136 152 139
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
            COLOR {color[CHGRD].rgb}
            # COLOR 136 152 139
            SIZE 6
            ANTIALIAS TRUE
            FORCE TRUE
        END
    )''',
        'rules': []
    }]
