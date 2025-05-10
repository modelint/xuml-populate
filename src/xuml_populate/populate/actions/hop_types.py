"""
hop_types.py – Populate a traverse action instance in PyRAL
"""

# System
from typing import NamedTuple, Callable
from enum import Enum

class AggregationType(Enum):
    FIRST = 1
    LAST = 2
    ALL = 3

class Hop(NamedTuple):
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

class SymmetricHop(Hop):
    aggregation: AggregationType

class AsymmetricCircularHop(Hop):
    side: str
    aggregation: AggregationType

class OrdinalHop(Hop):
    side: str
    ascending: bool
    aggregation: AggregationType

class FromAsymAssocHop(Hop):
    side: str

