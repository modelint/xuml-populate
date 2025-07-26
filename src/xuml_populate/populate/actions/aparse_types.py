""" aparse_types.py -- Data types useful for processing parsed action language """

# System
from collections import namedtuple
from typing import NamedTuple
from dataclasses import dataclass
from enum import Enum

# Model Integration
from scrall.parse.visitor import Execution_Unit_a

class MaxMult(Enum):
    ONE = 1
    MANY = 2


class Content(Enum):
    SCALAR = 1
    INSTANCE = 2
    RELATION = 3

class SMType(Enum):
    LIFECYCLE = 1
    SA = 2
    MA = 3

class ActivityType(Enum):
    METHOD = 1
    STATE = 2
    OP = 3


Attribute_ap = namedtuple('Attribute_ap', 'name scalar')
""" An Attribute/Scalar pair """
Labeled_Flow = namedtuple('Labeled_Flow', 'label flow')
""" A label, Flow_ap pair """
Attribute_Comparison = namedtuple('Attribute_Comparison', 'attr op')
""" An attribute compared in a selection phrase """
Boundary_Actions = namedtuple("Boundary_Actions", "ain aout")
""" Initial actions not dependent on any data flow input and output actions that do not flow to any other action"""

""" Activity identification and diagnostic data """

class Flow_ap(NamedTuple):
    """
    Describes a generated flow
    """
    fid: str  # Flow ID
    content: Content
    tname: str
    max_mult: MaxMult

@dataclass(frozen=True, kw_only=True)
class ActivityAP:
    anum: str  # activity number
    domain: str  # domainname
    signum: str  # signature number
    xiflow: Flow_ap  # executing instance flow (none for assigner state activities)
    activity_path: str  # descriptive name of activity for logging (e.g. domain, class, method name)
    parse: Execution_Unit_a  # The Scrall parse of the actions
    scrall_text: str  # Full unparsed text of the activity for logging and diagnostic reference

@dataclass(frozen=True, kw_only=True)
class MethodActivityAP(ActivityAP):
    cname: str  # Method is defined on this class name
    opname: str  # Name of the method

@dataclass(frozen=True, kw_only=True)
class StateActivityAP(ActivityAP):
    sname: str  # state name
    state_model: str  # state model name (class or rnum)
    smtype: SMType  # lifecycle, sa assigner, ma assigner
    piflow: Flow_ap  # parititioning instance flow, set to None unless sm type is ma assigner

@dataclass(frozen=True, kw_only=True)
class OpActivityAP(ActivityAP):
    eename: str
    opname: str
