""" aparse_types.py -- Data types useful for processing parsed action language """

from collections import namedtuple
from enum import Enum


class MaxMult(Enum):
    ONE = 1
    MANY = 2


class Content(Enum):
    SCALAR = 1
    INSTANCE = 2
    RELATION = 3

Attribute_ap = namedtuple('Attribute_ap', 'name scalar')
""" An Attribute/Scalar pair """
Labeled_Flow = namedtuple('Labeled_Flow', 'label flow')
""" A label, Flow_ap pair """
Attribute_Comparison = namedtuple('Attribute_Comparison', 'attr op')
""" An attribute compared in a selection phrase """
Boundary_Actions = namedtuple("Boundary_Actions", "ain aout")
""" Initial actions not dependent on any data flow input and output actions that do not flow to any other action"""
Activity_ap = namedtuple("Activity_ap", "anum domain cname sname eename opname xiflow activity_path scrall_text")
""" Activity identification and diagnostic data """
Flow_ap = namedtuple("Flow_ap", "fid content tname max_mult")
""" Describes a generated flow with: Flow ID, content(scalar/table/class), type name, Max multiplicity (1,M) """
