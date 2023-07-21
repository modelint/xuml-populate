"""
pop_types.py - Named tuples corresponding to each MM type
"""

# TODO Generate these from the metamodel parse

from collections import namedtuple
from pyral.rtypes import Mult as DBMult

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
Spanning_Element_i = namedtuple('Spanning_Element_i', 'Label Domain')

# Class and Attribute subsystem
Class_i = namedtuple('Class_i', 'Name Cnum Domain')
Alias_i = namedtuple('Alias_i', 'Name Class Domain')
Attribute_i = namedtuple('Attribute_i', 'Name Class Domain Type')
Identifier_i = namedtuple('Identifier_i', 'Number Class Domain')
Identifer_Attribute_i = namedtuple('Identifier_Attribute_i', 'Identifier Attribute Class Domain')
Irreducible_Identifier_i = namedtuple('Irreducible_Identifier_i', 'Number Class Domain')
Super_Identifier_i = namedtuple('Super_Identifier_i', 'Number Class Domain')
Identifier_Attribute_i = namedtuple('Identifier_Attribute_i', 'Identifier Attribute Class Domain')
Non_Derived_Attribute_i = namedtuple('Non_Derived_Attribute_i', 'Name Class Domain')
Attribute_Reference_i = namedtuple('Attribute_Reference_i', 'From_attribute From_class To_attribute To_class '
                                                            'Domain To_identifier Ref Rnum')

# Relationship subsystem
Rel_i = namedtuple('Rel_i', 'Rnum Domain')
Reference_i = namedtuple('Reference_i', 'Ref From_class To_class Rnum Domain')
Formalizing_Class_Role_i = namedtuple('Formalizing_Class_Role_i', 'Rnum Class Domain')

# Association
Association_i = namedtuple('Association_i', 'Rnum Domain')
Binary_Association_i = namedtuple('Binary_Association_i', 'Rnum Domain')
Association_Class_i = namedtuple('Association_Class_i', 'Rnum Class Domain Multiplicity')
Perspective_i = namedtuple('Perspective_i', 'Side Rnum Domain Viewed_class Phrase Conditional Multiplicity')
Asymmetric_Perspective_i = namedtuple('Asymmetric_Perspective_i', 'Side Rnum Domain')
T_Perspective_i = namedtuple('T_Perspective_i', 'Side Rnum Domain')
P_Perspective_i = namedtuple('P_Perspective_i', 'Side Rnum Domain')
Association_Reference_i = namedtuple('Association_Reference_i', 'Ref_type From_class To_class Rnum Domain Perspective')
Simple_Association_Reference_i = namedtuple('Simple_Association_Reference_i',
                                            'Ref_type From_class To_class Rnum Domain')
Referring_Class_i = namedtuple('Referring_Class_i', 'Rnum Class Domain')
Association_Class_Reference_i = namedtuple('Association_Class_Reference_i',
                                           'Ref_type Association_class Participating_class '
                                           'Rnum Domain')
T_Reference_i = namedtuple('T_Reference_i', 'Ref_type Association_class Participating_class Rnum Domain')
P_Reference_i = namedtuple('P_Reference_i', 'Ref_type Association_class Participating_class Rnum Domain')

# Generalization
Generalization_i = namedtuple('Generalization_i', 'Rnum Domain Superclass')
Facet_i = namedtuple('Facet_i', 'Rnum Domain Class')
Superclass_i = namedtuple('Superclass_i', 'Rnum Domain Class')
Subclass_i = namedtuple('Subclass_i', 'Rnum Domain Class')
Minimal_Partition_i = namedtuple('Minimal_Partition_i', 'Rnum Domain A_subclass B_subclass')
Generalization_Reference_i = namedtuple('Generalization_i', 'Ref_type Subclass Superclass Rnum Domain')

# Ordinal
Ordinal_Relationship = namedtuple('Ordinal_Relationship_i',
                                  'Rnum Domain Ranked_class Ranking_attribute Ranking_identifier '
                                  'Ascending_perspective Descending_perspective')

# Lineage
Lineage_i = namedtuple('Lineage_i', 'Lnum Domain')
Class_In_Lineage_i = namedtuple('Class_In_Lineage_i', 'Class Lnum Domain')

# State Model
Lifecycle_i = namedtuple('Lifecycle_i', 'Class Domain')
State_Model_i = namedtuple('State_Model_i', 'Name Domain')

# States
Non_Deletion_State_i = namedtuple('Non_Deletion_State_i', 'Name State_model Domain')
Real_State_i = namedtuple('Real_State_i', 'Name State_model Domain Signature Activity')
State_i = namedtuple('State_i', 'Name State_model Domain')
Deletion_State_i = namedtuple('Deletion_State_i', 'Name Class Domain')
Initial_Pseudo_State_i = namedtuple('Initial_Pseudo_State_i', 'Name Class Domain')
State_Signature_i = namedtuple('State_Signature_i', 'SIGnum State_model Domain')
Initial_Transition_i = namedtuple('Initial_Transition_i', 'From_state Class Domain Event')

# Events
Event_Specification_i = namedtuple('Event_Specification_i', 'Name State_model Domain, State_signature')
Monomorphic_Event_Specification_i = namedtuple('Monomorphic_Event_Specification_i', 'Name State_model Domain')
Monomorphic_Event_i = namedtuple('Monomorphic_Event_i', 'Name State_model Domain')
Effective_Event_i = namedtuple('Effective_Event_i', 'Name State_model Domain')
Event_i = namedtuple('Event_i', 'Name State_model Domain')

# Transitions
Event_Response_i = namedtuple('Event_Response_i', 'State Event State_model Domain')
Transition_i = namedtuple('Transition_i', 'From_state Event State_model Domain To_state')
Non_Transition_i = namedtuple('Non_Transition_i', 'State Event State_model Domain Behavior Reason')

# Activity
Activity_i = namedtuple('Activity_i', 'Anum Domain')
Asynchronous_Activity_i = namedtuple('Asynchronous_Activity_i', 'Anum Domain')
State_Activity_i = namedtuple('State_Activity_i', 'Anum State State_model Domain')
Signature_i = namedtuple('Signature_i', 'SIGnum Domain')
Parameter_i = namedtuple('Parameter_i', 'Name Signature Domain Input_flow Activity Type')
Method_Signature_i = namedtuple('Method_Signature_i', 'SIGnum Method Class Domain')
Method_i = namedtuple('Method_i', 'Anum Name Class Domain Executing_instance_flow')
Synchronous_Activity_i = namedtuple('Synchronous_Activity_i', 'Anum Domain')
Synchronous_Output_i = namedtuple('Synchronous_Output_i', 'Anum Domain Output_flow Type')

# Flow
Data_Flow_i = namedtuple('Data_Flow_i', 'ID Activity Domain')
Flow_i = namedtuple('Flow_i', 'ID Activity Domain')
Control_Flow_i = namedtuple('Control_Flow_i', 'ID Activity Domain')
Instance_Flow_i = namedtuple('Instance_Flow_i', 'ID Activity Domain Class')
Label_i = namedtuple('Label_Flow_i', 'Name Flow Activity Domain')
Multiple_Instance_Flow_i = namedtuple('Multiple_Instance_Flow_i', 'ID Activity Domain')
Single_Instance_Flow_i = namedtuple('Single_Instance_Flow_i', 'ID Activity Domain')
Non_Scalar_Flow_i = namedtuple('Non_Scalar_Flow_i', 'ID Activity Domain')
Scalar_Flow_i = namedtuple('Scalar_Flow_i', 'ID Activity Domain Type')
Table_Flow_i = namedtuple('Table_Flow_i', 'ID Activity Domain Tuple')

# External Entity
EE_i = namedtuple('EE_i', 'EEnum Name Class Domain')
Op_i = namedtuple('Op_i', 'Name EE Domain Direction')
Op_Signature_i = namedtuple('Op_Signature_i', 'SIGnum Operation EE Domain')
Asynchronous_Operation_i = namedtuple('Asynchronous_Operation_i', 'Name EE Domain Anum')
Synchronous_Operation_i = namedtuple('Synchronous_Operation_i', 'Name EE Domain Anum')

# Type
Type_i = namedtuple('Type_i', 'Name Tnum Domain')
Class_Type_i = namedtuple('Class_Type_i', 'Name Domain')
Scalar_Type_i = namedtuple('Scalar_Type_i', 'Name Domain')
Table_Type_i = namedtuple('Table_Type_i', 'Name Domain')
Table_Attribute_i = namedtuple('Table_Attribute_i', 'Name Table_type Domain Attribute_type')

## Actions

# Traverse action
Action_i = namedtuple('Action_i', 'ID Activity Domain')
Traverse_Action_i = namedtuple('Traverse_Action_i', 'ID Activity Domain Path Source_flow Destination_flow')
Path_i = namedtuple('Path_i', 'Name Domain Dest_class')
Hop_i = namedtuple('Hop_i', 'Number Path Domain Rnum Class_step')
Perspective_Hop_i = namedtuple('Perspective_Hop_i', 'Number Path Domain Side Rnum')
Association_Hop_i = namedtuple('Association_Hop_i', 'Number Path Domain')
Circular_Hop_i = namedtuple('Circular_Hop_i', 'Number Path Domain Aggregation')
Symmetric_Hop_i = namedtuple('Symmetric_Hop_i', 'Number Path Domain')
Asymmetric_Circular_Hop_i = namedtuple('Symmetric_Hop_i', 'Number Path Domain')
Ordinal_Hop_i = namedtuple('Ordinal_Hop_i', 'Number Path Domain Ascending')
Straight_Hop_i = namedtuple('Straight_Hop_i', 'Number Path Domain')
Association_Class_Hop_i = namedtuple('Association_Class_Hop_i', 'Number Path Domain')
From_Asymmetric_Assocation_Class_Hop_i = namedtuple('From_Asymmetric_Association_Class_Hop_i', 'Number Path Domain')
From_Symmetric_Assocation_Class_Hop_i = namedtuple('From_Symmetric_Association_Class_Hop_i', 'Number Path Domain')
To_Assocation_Class_Hop_i = namedtuple('To_Association_Class_Hop_i', 'Number Path Domain')
Generalization_Hop_i = namedtuple('Generalization_Hop_i', 'Number Path Domain')
To_Superclass_Hop_i = namedtuple('To_Superclass_Hop_i', 'Number Path Domain')
To_Subclass_Hop_i = namedtuple('To_Subclass_Hop_i', 'Number Path Domain')

# Select action
Comparison_Criterion_i = namedtuple('Comparison_Criterion_i', 'ID Select_action Activity Attribute Class Domain'
                                                              'Compared_input Comparison')
Equivalence_Criterion_i = namedtuple('Equivalence_Criterion_i', 'ID Select_action Activity Attribute Class Domain'
                                                                ' Equal Value Scalar_type')
Restriction_Criterion_i = namedtuple('Restriction_Criterion_i', 'ID Select_action Activity Attribute Class Domain')
Ranking_Criterion_i = namedtuple('Ranking_Criterion_i', 'ID Select_action Activity Attribute Class Domain Order')
Identifer_Select_i = namedtuple('Identifer_Select_i', 'ID Activity Domain Identifier Class')
Many_Select_i = namedtuple('Many_Select_i', 'ID Activity Domain Output_flow')
Single_Select_i = namedtuple('Single_Select_i', 'ID Activity Domain Output_flow')
Zero_One_Cardinality_Select_i = namedtuple('Zero_One_Cardinality_Select_i', 'ID Activity Domain')
Projected_Attribute_i = namedtuple('Projected_Attribute_i', 'Attribute Class Select_action Activity Domain')
Restriction_i = namedtuple('Restriction_i', 'Select_action Activity Class Domain Expression')
Select_Action_i = namedtuple('Select_Action_i', 'ID Activity Class Domain Input_flow Selection_cardinality')
