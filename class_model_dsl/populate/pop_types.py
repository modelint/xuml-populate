"""
pop_types.py - Named tuples corresponding to each MM type
"""

# TODO Generate these from the metamodel parse

from collections import namedtuple
from PyRAL.rtypes import Mult as DBMult

mult_tclral = {
    'M': DBMult.AT_LEAST_ONE,
    '1': DBMult.EXACTLY_ONE,
    'Mc': DBMult.ZERO_ONE_OR_MANY,
    '1c': DBMult.ZERO_OR_ONE
}

# Domain subsystem
Domain_i = namedtuple('Domain_i', 'Name Alias')
Modeled_Domain_i = namedtuple('Modeled_Domain_i', 'Name')
Domain_Partition_i = namedtuple('Domain_Partition_i', 'Number Domain')
Subsystem_i = namedtuple('Domain_Partition_i', 'Name First_element_number Domain Alias')
Element_i = namedtuple('Element_i', 'Label Domain')
Subsystem_Element_i = namedtuple('Element_i', 'Label Domain Subsystem')

# Class and Attribute subsystem
Class_i = namedtuple('Class_i', 'Name Cnum Domain')
Alias_i = namedtuple('Alias_i', 'Name Class Domain')
Attribute_i = namedtuple('Attribute_i', 'Name Class Domain Type')
Identiifer_i = namedtuple('Identifier_i', 'Number Class Domain')
Identifer_Attribute_i = namedtuple('Identifier_Attribute_i', 'Identifier Attribute Class Domain')
Identifier_i = namedtuple('Identifier_i', 'Number Class Domain')
Irreducible_Identifier_i = namedtuple('Irreducible_Identifier_i', 'Number Class Domain')
Super_Identifier_i = namedtuple('Super_Identifier_i', 'Number Class Domain')
Identifier_Attribute_i = namedtuple('Identifier_Attribute_i', 'Identifier Attribute Class Domain')
Non_Derived_Attribute_i = namedtuple('Non_Derived_Attribute_i', 'Name Class Domain')

# Relationship subsystem
Rel_i = namedtuple('Rel_i', 'Rnum Domain')
Association_i = namedtuple('Association_i', 'Rnum Domain')
Binary_Association_i = namedtuple('Binary_Association_i', 'Rnum Domain')
Association_Class_i = namedtuple('Association_Class_i', 'Rnum Class Domain')
Perspective_i = namedtuple('Perspective_i', 'Side Rnum Domain Viewed_class Phrase Conditional Multiplicity')
Asymmetric_Perspective_i = namedtuple('Asymmetric_Perspective_i', 'Side Rnum Domain')
T_Perspective_i = namedtuple('T_Perspective_i', 'Side Rnum Domain')
P_Perspective_i = namedtuple('P_Perspective_i', 'Side Rnum Domain')

