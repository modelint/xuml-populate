""" aparse_types.py -- Data types useful for processing parsed action language """

from collections import namedtuple
from enum import Enum


class MaxMult(Enum):
    ONE = 1
    MANY = 2

class Content(Enum):
    SCALAR = 1
    INSTANCE = 2
    TABLE = 3

Flow_ap = namedtuple("Flow_ap", "fid content tname max_mult")
""" Describes a generated flow with: Flow ID, content(scalar/table/class), type name, Max multiplicity (1,M) """

# Deprecated
# InstanceFlow_ap = namedtuple("InstanceFlow_ap", "fid ctype max_mult")
# """ Describes a generated instance flow with: Flow ID, Class Type, Max multiplicity (1,M) in this flow"""
#
# TableFlow_ap = namedtuple("TableFlow_ap", "fid ttype tuple")
# """ Describes a generated table flow with: Flow ID, Table"""
