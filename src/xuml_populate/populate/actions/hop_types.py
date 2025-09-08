"""
hop_types.py – Populate a traverse action instance in PyRAL
"""

# System
from dataclasses import dataclass
from typing import Callable
from enum import Enum

# xuml Populate
from xuml_populate.populate.actions.aparse_types import MaxMult

class AggregationType(Enum):
    FIRST = 1
    LAST = 2
    ALL = 3

# I tried NamedTuple and ran into type checking issues with inheritance, so let's try
# the dataclass decorator instead

@dataclass
class Hop:
    """
    Here we specify a method and the values it requires to populate the Hop subclasses
    in the metamodel navigation subsystem.
    This class is sufficient for Straight, From Symmetric Association Class, To Association Class and Generaization
    Hop subclasses.

    The subclass hop named tuples supply additional attributes as determined by R931, R936, R932, and R937
    of the metammodel navigation subsystem.
    """
    hoptype: Callable
    to_class: str
    rnum: str

@dataclass
class ToAssocClassHop(Hop):
    input_mult: MaxMult
    # The input_mult_one value helps us resolve multplicity when hopping across a many associative assoc

@dataclass
class SymmetricHop(Hop):
    aggregation: AggregationType

@dataclass
class AsymmetricCircularHop(Hop):
    side: str
    aggregation: AggregationType

@dataclass
class OrdinalHop(Hop):
    side: str
    ascending: bool
    aggregation: AggregationType

@dataclass
class FromAsymAssocHop(Hop):
    side: str

