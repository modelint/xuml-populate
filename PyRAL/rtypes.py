"""
rtypes.py -- Relational database types such as header, attribute, tuple, etc
"""

from collections import namedtuple

Attribute = namedtuple('_Attribute', 'name type')