from operator import itemgetter
import os
import warnings


class NotImplementedWarning(UserWarning):
    pass


def lookups_from_cs(detail, lookup_type, name):

    function_name = detail[:6]
    function = globals().get(function_name)

    if function:
        return function(lookup_type, name)

    warnings.warn('Symproc not implemented: {}'.format(function_name),
                  NotImplementedWarning)

    # Return default lookup; leave CS as is, maybe CS in instruction.py can
    # make something useful
    return [{
        'instruction': 'CS({})'.format(detail),
        'rules': [],
    }]


def DATCVR(lookup_type, name):
    return [{
        'instruction': 'LC(HODATA01)',
        'rules': [],
    }]


def DEPARE(lookup_type, name):

    # These values are normally passed by the mariner
    # safety_contour = 10
    # shallow_contour = 20
    # deep_contour = 30

    # Basic implementation of DEPARE constructed symbol.
    # We are missing all the line and fill symbology
    return [{
        'instruction': 'AC(DEPIT)',
        'rules': [('DRVAL2', '<0')],
    }, {
        'instruction': 'AC(DEPVS)',
        'rules': [('DRVAL2', '<10')],
    }, {
        'instruction': 'AC(DEPMS)',
        'rules': [('DRVAL2', '<20')],
    }, {
        'instruction': 'AC(DEPMD)',
        'rules': [('DRVAL2', '<30')],
    }, {
        'instruction': 'AC(DEPDW)',
        'rules': [],
    }]


def DEPCNT(lookup_type, name):
    return [{
        'rules': [
            ('QUAPOS', '>1'),
            ('QUAPOS', '<10')
        ],
        'instruction': 'LS(DASH,1,DEPCN)',
    }, {
        'rules': [],
        'instruction': 'LS(SOLD,1,DEPCN)',
    }]


def LEGLIN(lookup_type, name):
    plnspd = "TE('%d kt',plnspd,3,2,2,’15110’,0,0,CHBLK,50)"

    return [{
        'rules': [('select', '1'), ('plnspd', ' ')],
        'instruction': ';'.join([
            'LC(PLNRTE03)',
            'SY(PLNSPD03)',
            plnspd
        ]),
    }, {
        'rules': [('select', '1')],
        'instruction': ';'.join([
            'LC(PLNRTE03)',
        ]),
    }, {
        'rules': [('plnspd', ' ')],
        'instruction': ';'.join([
            'LS(DOTT,2,APLRT)',
            'SY(PLNSPD04)',
            plnspd
        ]),
    }, {
        'rules': [],
        'instruction': ';'.join([
            'LS(DOTT,2,APLRT)',
        ]),
    }]


def LIGHTS(lookup_type, name):
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
        'instruction': 'SY(LIGHTS81)',
        'rules': [('__OR__', [('CATLIT', '1'), ('CATLIT', '16')])],
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


def OBSTRN(lookup_type, name):
    if lookup_type == 'Point':
        return OBSTRN_point(name)

    if lookup_type == 'Line':
        return OBSTRN_line(name)

    return OBSTRN_area(name)


def OBSTRN_area(name):
    return [{
        'rules': [('VALSOU', '>30')],
        'instruction': 'LS(DASH,2,CHGRD)'
    }, {
        'rules': [('VALSOU', ' ')],
        'instruction': 'LS(DOTT,2,CHBLK)'
    }, {
        'rules': [('CATOBS', '6')],
        'instruction': 'AP(FOULAR01);LS(DOTT,2,CHBLK)'
    }, {
        'rules': [('__OR__', [('WATLEV', '1'), ('WATLEV', '2')])],
        'instruction': 'AC(CHBRN);LS(SOLD,2,CSTLN)'
    }, {
        'rules': [('WATLEV', '4')],
        'instruction': 'AC(DEPIT);LS(DASH,2,CSTLN)'
    }, {
        'rules': [],
        'instruction': 'AC(DEPVS);LS(DOTT,2,CHBLK)'
    }]


def OBSTRN_line(name):
    return [{
        'rules': [('VALSOU', '>30')],
        'instruction': 'LS(DASH,2,CHBLK)'
    }, {
        # VALSOU missing and <= SAFETY_DEPTH both lead here
        'rules': [],
        'instruction': 'LS(DOTT,2,CHBLK)'
    }]


def OBSTRN_point(name):
    common_rule = [{
        'rules': [('VALSOU', '>30')],
        'instruction': 'SY(DANGER02)'
    }]

    if name =='UWTROC':
        return common_rule + [{
            'rules': [('VALSOU', ' '), ('__OR__', [
                ('WATLEV', '4'),
                ('WATLEV', '5'),
            ])],
            'instruction': 'SY(UWTROC04)'
        }, {
            'rules': [('VALSOU', ' ')],
            'instruction': 'SY(DANGER01)'
        }, {
            'rules': [('WATLEV', '3')],
            'instruction': 'SY(UWTROC03)'
        }, {
            'rules': [],
            'instruction': 'SY(UWTROC04)'
        }]

    else:
        return common_rule + [{
            'rules': [('VALSOU', ' '), ('CATOBS', '6')],
            'instruction': 'SY(DANGER01)'
        }, {
            'rules': [('VALSOU', ' '), ('__OR__', [
                ('WATLEV', '1'),
                ('WATLEV', '2'),
            ])],
            'instruction': 'SY(OBSTRN11)'
        }, {
            'rules': [('VALSOU', ' '), ('__OR__', [
                ('WATLEV', '4'),
                ('WATLEV', '5'),
            ])],
            'instruction': 'SY(DANGER03)'
        }, {
            'rules': [('VALSOU', ' ')],
            'instruction': 'SY(DANGER01)'
        }, {
            'rules': [('CATOBS', '6')],
            'instruction': 'SY(OBSTRN01)'
        }, {
            'rules': [('__OR__', [
                ('WATLEV', '1'),
                ('WATLEV', '2'),
            ])],
            'instruction': 'SY(OBSTRN11)'
        }, {
            'rules': [('__OR__', [
                ('WATLEV', '4'),
                ('WATLEV', '5'),
            ])],
            'instruction': 'SY(OBSTRN03)'
        }, {
            'rules': [],
            'instruction': 'SY(OBSTRN01)'
        }]


def OWNSHP(lookuptype, name):
    return [{
        'rules': [],
        'instruction': 'SY(OWNSHP01)',
    }]


def QUALIN(lookuptype, name):
    common_rule = [{
        'instruction': 'LC(LOWACC21)',
        'rules': [
            # QUAPOS only has values 1 to 11. QUAPOS not in 1, 10, 11 is
            # equivalent to the below rules
            ('QUAPOS', '>1'),
            ('QUAPOS', '<10')
        ]
    }]

    if name == 'COALNE':
        return common_rule + [{
            'instruction': 'LS(SOLD,1,CSTLN)',
            'rules': []
        }]
    else:
        return common_rule + [{
            'instruction': 'LS(SOLD,3,CHMGF);LS(SOLD,1,CSTLN)',
            'rules': [('CONRAD', '1')]
        }, {
            # CONRAD missing and CONRAD != 1 both lead here
            'instruction': 'LS(SOLD,1,CSTLN)',
            'rules': []
        }]


def QUAPNT(lookup_type, name):
    return [{
        'instruction': 'SY(LOWACC01)',
        'rules': [('__OR__', [
            ('QUAPOS', '2'),
            ('QUAPOS', '3'),
            ('QUAPOS', '4'),
            ('QUAPOS', '5'),
            ('QUAPOS', '6'),
            ('QUAPOS', '7'),
            ('QUAPOS', '8'),
            ('QUAPOS', '9'),
        ])]
    }]


def QUAPOS(lookup_type, name):
    if lookup_type == 'Point':
        return QUAPNT(lookup_type, name)
    else:
        return QUALIN(lookup_type, name)


def SLCONS(lookup_type, name):
    return [{
        'instruction': 'SY(LOWACC01)',
        'rules': [
            # QUAPOS only has values 1 to 11. QUAPOS not in 1, 10, 11 is
            # equivalent to the below rules
            ('QUAPOS', '>1'),
            ('QUAPOS', '<10')
        ]
    }, {
        'instruction': 'LC(LOWACC21)',
        'rules': [
            # QUAPOS only has values 1 to 11. QUAPOS not in 1, 10, 11 is
            # equivalent to the below rules
            ('QUAPOS', '>1'),
            ('QUAPOS', '<10')
        ]
    }, {
        'instruction': 'LS(DASH,1,CSTLN)',
        'rules': [('__OR__', [('CONDTN', '1'), ('CONDTN', '2')])]
    }, {
        'instruction': 'LS(SOLD,4,CSTLN)',
        'rules': [(
            '__OR__', [('CATSLC', '6'), ('CATSLC', '15'), ('CATSLC', '16')]
        )]
    }, {
        'instruction': 'LS(DASH,2,CSTLN)',
        'rules': [(
            '__OR__', [('WATLEV', '3'), ('WATLEV', '4')]
        )]
    }, {
        'instruction': 'LS(SOLD,2,CSTLN)',
        'rules': []
    }]


def SOUNDG(lookup_type, name):
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


def SYMINS(lookup_type, name):
    instructions = {
        'Point': 'SY(NEWOBJ01)',
        'Line': 'LC(NEWOBJ01)',
        'Area': 'SY(NEWOBJ01);LS(DASH,2,CHMGD)',
    }

    return [{
        'rules': [],
        'instruction': instructions[lookup_type],
    }]


topshp_to_sy = [
    # (topshp, floating, rigid),
    ('1', 'TOPMAR02', 'TOPMAR22'),
    ('2', 'TOPMAR04', 'TOPMAR24'),
    ('3', 'TOPMAR10', 'TOPMAR30'),
    ('4', 'TOPMAR12', 'TOPMAR32'),
    ('5', 'TOPMAR13', 'TOPMAR33'),
    ('6', 'TOPMAR14', 'TOPMAR34'),
    ('7', 'TOPMAR65', 'TOPMAR85'),
    ('8', 'TOPMAR17', 'TOPMAR86'),
    ('9', 'TOPMAR16', 'TOPMAR36'),
    ('10', 'TOPMAR08', 'TOPMAR28'),
    ('11', 'TOPMAR07', 'TOPMAR27'),
    ('12', 'TOPMAR14', 'TOPMAR14'),
    ('13', 'TOPMAR05', 'TOPMAR25'),
    ('14', 'TOPMAR06', 'TOPMAR26'),
    ('15', 'TMARDEF2', 'TOPMAR88'),
    ('16', 'TMARDEF2', 'TOPMAR87'),
    ('17', 'TMARDEF2', 'TMARDEF1'),
    ('18', 'TOPMAR10', 'TOPMAR30'),
    ('19', 'TOPMAR13', 'TOPMAR33'),
    ('20', 'TOPMAR14', 'TOPMAR34'),
    ('21', 'TOPMAR13', 'TOPMAR33'),
    ('22', 'TOPMAR14', 'TOPMAR34'),
    ('23', 'TOPMAR14', 'TOPMAR34'),
    ('24', 'TOPMAR02', 'TOPMAR22'),
    ('25', 'TOPMAR04', 'TOPMAR24'),
    ('26', 'TOPMAR10', 'TOPMAR30'),
    ('27', 'TOPMAR17', 'TOPMAR86'),
    ('28', 'TOPMAR18', 'TOPMAR89'),
    ('29', 'TOPMAR02', 'TOPMAR22'),
    ('30', 'TOPMAR17', 'TOPMAR86'),
    ('31', 'TOPMAR14', 'TOPMAR14'),
    ('32', 'TOPMAR10', 'TOPMAR30'),
    ('33', 'TMARDEF2', 'TMARDEF1'),
    (' ', 'TMARDEF2', 'TMARDEF1'),
]


def TOPMAR(lookup_type, name):
    if os.environ.get('TOPMAR_FLOAT'):
        sy_getter = itemgetter(0)
    else:
        sy_getter = itemgetter(1)

    return [{
        'instruction': 'SY({})'.format(sy),
        'rules': [('TOPSHP', shp)]
    }
        for shp, floating, rigid in topshp_to_sy
        for sy in [sy_getter([floating, rigid])]
    ] + [{
        'instruction': 'SY(QUESMRK1)',
        'rules': [],
    }]

def WRECKS(lookup_type, name):
    if lookup_type == 'Point':
        return WRECKS_Point(lookup_type, name)
    else:
        return WRECKS_other(lookup_type, name)


def WRECKS_other(lookup_type, name):
    # TODO: add rules for background
    return [{
        'rules': [
            ('QUAPOS', '>1'),
            ('QUAPOS', '<10')
        ],
        'instruction': 'LC(LOWACC41)'
    }, {
        'rules': [('VALSOU', '>30')],
        'instruction': 'LS(DASH,2,CHBLK)'
    }, {
        'rules': [('VALSOU', ' ')],
        'instruction': 'LS(DOTT,2,CHBLK)'
    }, {
        'rules': [('__OR__', [
            ('WATLEV', '1'),
            ('WATLEV', '2')
        ])],
        'instruction': 'LS(SOLD,2,CSTLN);AC(CHBRN)'
    }, {
        'rules': [('WATLEV', '4')],
        'instruction': 'LS(DASH,2,CSTLN);AC(DEPIT)'
    }, {
        'rules': [('__OR__', [
            ('WATLEV', '3'),
            ('WATLEV', '5')
        ])],
        'instruction': 'LS(DOTT,2,CSTLN);AC(DEPVS)'
    }, {
        'rules': [],
        'instruction': 'LS(DOTT,2,CSTLN);AC(DEPVS)'
    }]


def WRECKS_Point(lookup_type, name):
    return [{
        'rules': [('VALSOU', '>30')],
        'instruction': 'SY(DANGER02)'
    }, {
        'rules': [('VALSOU', ' ')],
        'instruction': 'SY(DANGER01)'
    }, {
        'rules': [('CATWRK', '1'), ('WATLEV', '3')],
        'instruction': 'SY(WRECKS04)'
    }, {
        'rules': [('CATWRK', '2'), ('WATLEV', '3')],
        'instruction': 'SY(WRECKS05)'
    }, {
        'rules': [('__OR__', [
            ('CATWRK', '4'),
            ('CATWRK', '5'),
            ('WATLEV', '1'),
            ('WATLEV', '2'),
            ('WATLEV', '3'),
            ('WATLEV', '4'),
        ])],
        'instruction': 'SY(WRECKS01)'
    }, {
        'rules': [],
        'instruction': 'SY(WRECKS05)'
    }]
