"""
select_action.py – Populate a selection action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from class_model_dsl.exceptions.action_exceptions import ComparingNonAttributeInSelection, NoInputInstanceFlow
from class_model_dsl.populate.actions.action import Action
from class_model_dsl.populate.flow import Flow
from class_model_dsl.populate.pop_types import Select_Action_i, Single_Select_i, Identifer_Select_i,\
    Zero_One_Cardinality_Select_i, Many_Select_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from collections import namedtuple
from scrall.parse.visitor import N_a, BOOL_a, Op_a

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class SelectAction:
    """
    Create all relations for a Select Statement
    """

    input_instance_flow = None  # We are selecting instances from this instance flow
    cname = None  # We are performing a selection on this class
    anum = None
    expression = None
    comparison_criteria = []
    restriction_text = ""
    cardinality = None
    action_id = None
    domain = None  # in this domain
    mmdb = None  # The database

    @classmethod
    def identifier_selection(cls) -> int:
        """
        | Determine whether we are selecting based on an identifier match.
        An identifier match supplies one value per identifier attribute for some identifier defined on
        the class.
         | Each comparison must be == (equivalence)
         |
         | **For example:**
         |
         | Assume Floor, Shaft is an identifier defined on the Accessible Shaft Level class
         | This means that if you supply a value for each attribute like so
         |
         | Accessible Shaft Level( Floor == x, Shaft == y )
         |
         | you will select at most one instance. But if you select based on:
         |
         | Accessible Shaft Level( Shaft == y )
         |
         | you may select multiple instances since a Shaft intersects multiple Floors
         :returns: An identifier number 1,2, ... or 0 if none found
        """
        idcheck = {c['attr'] for c in cls.comparison_criteria if c['op'] == '=='}
        R = f"Class:<{cls.cname}>, Domain:<{cls.domain}>"
        Relation.restrict3(cls.mmdb, relation='Identifier_Attribute', restriction=R)
        Relation.project2(cls.mmdb, attributes=('Identifier', 'Attribute',), svar_name='all_id_attrs')
        # We have created a named relation with a projection of each id_attr and its id_num
        # Now we must step through each id_num to see if we are selecting on any of them
        i = 1  # Start with inum 1 {I}, (identifier 1). Every class has at least this identifier
        while True:
            # Step through every identifier of the class and see if there is a set of equivalence
            # comparisons that forms a superset of this identifier. If we are selecting at most one instance
            R = f"Identifier:<{str(i)}>"
            t_id_n_attrs = Relation.restrict3(cls.mmdb, relation='all_id_attrs', restriction=R)
            if not t_id_n_attrs.body:
                # This i num is not defined on the class, no more i nums to check
                break
            t_id_n_attr_names = Relation.project2(cls.mmdb, attributes=('Attribute',))
            id_n_attr_names = {t['Attribute'] for t in t_id_n_attr_names.body}
            if not id_n_attr_names - idcheck:
                # The set of identifier attributes for the current id number
                # is present in the set of attribute equivalence matches
                # So we are selecting on an identifier and at most one instance can flow out of the selection
                return i
            i += 1  # Increment to the next I num (I1, I2, etc)
        return 0

    @classmethod
    def process_bool_value(cls, attr: str, setting: bool):
        R = f"Name:<{attr}>, Class:<{cls.cname}>, Domain:<{cls.domain}>"
        result = Relation.restrict3(cls.mmdb, relation='Attribute', restriction=R)
        type = result.body[0]['Type']

    @classmethod
    def process_enum_value(cls, attr: str, enum: str):
        pass

    @classmethod
    def process_flow(cls, name: str, input_param: bool):
        print(f"Populating [{name}] as flow")

    @classmethod
    def process_attr(cls, name: str, op: str):
        """
        Validate that attribute is a member of the input flow class

        :param op:
        :param name:
        :return:
        """
        R = f"Name:<{name}>, Class:<{cls.cname}>, Domain:<{cls.domain}>"
        result = Relation.restrict3(cls.mmdb, relation='Attribute', restriction=R)
        if not result.body:
            raise ComparingNonAttributeInSelection(f"select action restriction on class [{cls.cname}] is "
                                                   f"comparing on name [{name}] that is not an attribute of that class")
        cls.comparison_criteria.append({'attr': name, 'op': op})
        cls.attr_set = True

    @classmethod
    def walk_criteria(cls, operator, operands, attr: Optional[str] = None) -> str:
        """
        Recursively walk down the selection criteria parse tree validating attributes and input flows found in
        the leaf nodes. Also flatten the parse back into a language independent text representation for reference
        in the metamodel.

        :param operator:  A boolean, math or unary operator
        :param operands:  One or two operands (depending on the operator)
        :param attr:  If true, an attribute is in the process of being compared to an expression
        :return: Flattened selection expression as a string
        """
        attr_set = attr  # Has an attribute been set for this invocation?
        text = f" {operator} "  # Flatten operator into temporary string
        for o in operands:
            match type(o).__name__:
                case 'IN_a':
                    cls.process_flow(o, True)
                    text += f" {o.name}"
                case 'N_a':
                    if not attr_set:
                        # It must be the name of some attribute of the class selected upon
                        cls.process_attr(name=o.name, op=operator)
                        text = f"{o.name} {text}"
                        attr_set = o.name
                        # Otherwise, not an attribute, process as a constant value or scalar input flow
                    else:
                        text += f" {o.name}"
                        if o.name.startswith('_'):
                            # It's an enum value
                            cls.process_enum_value(attr=attr_set, enum=o.name)
                        elif (n := o.name.lower()) in {'true', 'false'}:
                            # It's a boolean value
                            cls.process_bool_value(attr=attr_set, setting=(n == 'true'))
                        else:
                            # It must be the name of a scalar flow that should have been set with some value
                            cls.process_flow(o.name, False)
                case 'BOOL_a':
                    text += cls.walk_criteria(o.op, o.operands, attr_set)
                case 'MATH_a':
                    text += cls.walk_criteria(o.op, o.operands, attr_set)
                case 'UNARY_a':
                    print()

        return text

    @classmethod
    def process_criteria(cls, criteria):
        """
        Break down criteria into a set of attribute comparisons and validate the components of a Select Action that
        must be populated into the metamodel.
         | These components are:
        * Restriction Criterian (Comparison or Ranking)
        * Scalar Flow inputs to any Comparison Criterion

        Sift through criteria to ensure that each terminal is either an attribute, input flow, or value.
        :param criteria:
        """
        # Consider case where there is a single boolean value critieria such as:
        #   shaft aslevs( Stop requested )
        # The implication is that we are selecting on: Stop requested == true
        # So elaborate the parse elminating our shorhand
        if type(criteria).__name__ == 'N_a':
            # Name only (no explicit operator or operand)
            criteria = BOOL_a(op='==', operands=[criteria, N_a(name='true')])
        # Walk the parse tree and save all attributes, ops, values, and input scalar flows
        cls.expression = cls.walk_criteria(criteria.op, criteria.operands)
        # Determine if this should be an Identifier Select subclass that yields at most one instance
        selection_idnum = cls.identifier_selection()
        if selection_idnum or cls.cardinality == 'ONE':
            # Populate a single instance flow for the selection output
            output_flow_id = Flow.populate_instance_flow(cls.mmdb, cname=cls.cname, activity=cls.anum, domain=cls.domain,
                                                         label=None, single=True)
            # Populate the Single Select subclass
            Relvar.insert(relvar='Single_Select', tuples=[
                Single_Select_i(Action=cls.action_id, Activity=cls.anum, Domain=cls.domain, Output_flow=output_flow_id)
            ])
            if selection_idnum:
                # Populate an Identifier Select subclass
                Relvar.insert(relvar='Identifier_Select', tuples=[
                    Identifer_Select_i(Action=cls.action_id, Activity=cls.anum, Domain=cls.domain,
                                       Identifier=selection_idnum, Class=cls.cname)
                ])
            else:
                # Populate an Identifier Select subclass
                # Note that if both ONE cardinality specified and identifier select, identifier select takes precedence
                Relvar.insert(relvar='Zero_One_Cardinality_Select', tuples=[
                    Zero_One_Cardinality_Select_i(Action=cls.action_id, Activity=cls.anum, Domain=cls.domain)
                ])
        else:
            # Many select with Multiple Instance Flow output
            output_flow_id = Flow.populate_instance_flow(cls.mmdb, cname=cls.cname, activity=cls.anum,
                                                         domain=cls.domain, label=None, single=False)
            # Populate the Many Select subclass
            Relvar.insert(relvar='Many_Select', tuples=[
                Many_Select_i(Action=cls.action_id, Activity=cls.anum, Domain=cls.domain, Output_flow=output_flow_id)
            ])


    @classmethod
    def populate(cls, mmdb: 'Tk', input_instance_flow: str, anum: str, select_agroup, domain: str):
        """
        Populate the Select Statement

        :param mmdb:
        :param input_instance_flow: The id of the executing instance flow
        :param anum:
        :param domain:
        :param select_agroup:  The parsed Scrall select action group
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        cls.mmdb = mmdb
        cls.domain = domain
        cls.anum = anum
        # Cardinality is specified as 1 or M on the selection
        # If 1, user wants at most one arbitrary instance, even if many are selected
        # If M, get them all.
        cls.cardinality = 'ONE' if select_agroup.card == '1' else 'ALL'

        # Ensure that the input flow is, in fact, an instance flow and determine its Class Type
        R = f"ID:<{input_instance_flow}>, Activity:<{anum}>, Domain:<{cls.domain}>"
        result = Relation.restrict3(cls.mmdb, relation='Instance_Flow', restriction=R)
        if not result.body:
            raise NoInputInstanceFlow(f"select action input flow [{input_instance_flow}:{anum}:{domain}]"
                                      f" is not an instance flow")
        cls.input_instance_flow = input_instance_flow
        cls.cname = result.body[0]['Class']

        # Populate the Action superclass instance and obtain its action_id
        cls.action_id = Action.populate(mmdb, anum, domain)  # Transaction open
        Relvar.insert(relvar='Select_Action', tuples=[
            Select_Action_i(Action=cls.action_id, Activity=anum, Class=cls.cname, Domain=domain,
                            Input_flow=cls.input_instance_flow, Selection_cardinality=cls.cardinality)
        ])
        cls.select_agroup = select_agroup
        # Walk through the critieria parse tree storing any attributes or input flows
        # Also check to see if we are selecting on an identifier
        cls.process_criteria(criteria=select_agroup.criteria)

        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute()  # Select Action
