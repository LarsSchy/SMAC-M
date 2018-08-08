import re
import warnings

from instructions import get_command


class NotImplementedWarning(UserWarning):
    pass


def lookups_from_cs(detail):

    if detail[0:6] == 'DEPARE':
        return DEPARE()

    # Return default lookup
    return [{
        'instruction': '',
        'rules': [],
    }]


def DEPARE():

    # These values are normally passed by the mariner
    safety_contour = 10
    shallow_contour = 20
    deep_contour = 30

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
