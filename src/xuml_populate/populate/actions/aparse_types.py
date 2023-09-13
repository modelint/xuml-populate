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


Activity_ap = namedtuple("Method_Activity_ap", "anum domain cname sname eename xiflow activity_path scrall_text")

Flow_ap = namedtuple("Flow_ap", "fid content tname max_mult")
""" Describes a generated flow with: Flow ID, content(scalar/table/class), type name, Max multiplicity (1,M) """
