"""
rtypes.py -- Relational database types such as header, attribute, tuple, etc
"""

from collections import namedtuple
from enum import Enum

Attribute = namedtuple('_Attribute', 'name type')

class Mult(Enum):
    AT_LEAST_ONE = '+'
    EXACTLY_ONE = '1'
    ZERO_ONE_OR_MANY = '*'
    ZERO_OR_ONE = '?'

