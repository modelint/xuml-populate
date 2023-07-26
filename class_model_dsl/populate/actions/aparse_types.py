""" aparse_types.py -- Data types useful for processing parsed action language """

from collections import namedtuple
from enum import Enum

class MaxMult(Enum):
    ONE = 1
    MANY = 2

InstanceFlow_ap = namedtuple("InstanceFlow_ap", "fid ctype max_mult")
""" Describes a generated instance flow with: Flow ID, Class Type, Max multiplicity (1,M) in this flow"""

TableFlow_ap = namedtuple("TableFlow_ap", "fid ttype")
""" Describes a generated table flow with: Flow ID, Table Type"""
