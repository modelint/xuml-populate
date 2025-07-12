""" aparse_types.py -- Data types useful for processing parsed action language """

from collections import namedtuple
from typing import NamedTuple, TypedDict
from dataclasses import dataclass
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

""" Activity identification and diagnostic data """

@dataclass(frozen=True, kw_only=True)
class ActivityAP:
    anum: str  # activity number
    domain: str  # domainname
    xiflow: str  # executing instance flow (none for assigner state activities)
    activity_path: str  # descriptive name of activity for logging (e.g. domain, class, method name)
    scrall_text: str  # Full unparsed text of the activity for logging and diagnostic reference

@dataclass(frozen=True, kw_only=True)
class MethodActivityAP(ActivityAP):
    cname: str  # Method is defined on this class name
    opname: str  # Name of the method

@dataclass(frozen=True, kw_only=True)
class StateActivityAP(ActivityAP):
    sname: str  # state name
    state_model: str  # state model name (class or rnum)
    smtype: str  # lifecycle, sa assigner, ma assigner
    piflow: str  # parititioning instance flow, set to None unless sm type is ma assigner
    pclass: str  # name of the partitioning class

@dataclass(frozen=True, kw_only=True)
class OpActivityAP(ActivityAP):
    eename: str
    opname: str

class Flow_ap(NamedTuple):
    """
    Describes a generated flow
    """
    fid: str  # Flow ID
    content: Content
    tname: str
    max_mult: MaxMult