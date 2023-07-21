"""
select_action.py – Populate a selection action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from class_model_dsl.exceptions.action_exceptions import ComparingNonAttributeInSelection, NoInputInstanceFlow
from class_model_dsl.populate.actions.action import Action
from class_model_dsl.populate.pop_types import Select_Action_i
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
    expression = None
    comparison_criteria = []
    select_on_id = False
    restriction_text = ""
    cardinality = None
    action_id = None
    domain = None  # in this domain
    mmdb = None  # The database

    @classmethod
    def identifier_selection(cls) -> bool:
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
                return True
            i += 1  # Increment to the next I num (I1, I2, etc)
        return False

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

        These components are:
        * Restriction Criterian (Comparison or Ranking)
        * Scalar Flow inputs to any Comparison Criterion

        These components
        Sift through criteria to ensure that each terminal is either an attribute, input flow, or value.


        :param criteria:
        :return:
        """
        # Criteria is a scalar expression
        # Consider case where there is a single boolean value critieria
        if type(criteria).__name__ == 'N_a':
            criteria = BOOL_a(op='==', operands=[criteria, N_a(name='true')])
        op = criteria.op
        operands = criteria.operands
        cls.expression = cls.walk_criteria(op, operands)
        cls.select_on_id = cls.identifier_selection()
        pass

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
        cls.mmdb = mmdb
        cls.domain = domain
        cls.input_instance_flow = input_instance_flow
        cls.action_id = Action.populate(mmdb, anum, domain)  # Transaction open
        cls.cardinality = '1' if select_agroup.card == '1' else 'M'
        # Determine this flow's Class Type
        R = f"ID:<{input_instance_flow}>, Activity:<{anum}>, Domain:<{cls.domain}>"
        result = Relation.restrict3(cls.mmdb, relation='Instance_Flow', restriction=R)
        if not result.body:
            raise NoInputInstanceFlow(f"select action input flow [{input_instance_flow}:{anum}:{domain}]"
                                      f" is not an instance flow")
        cls.cname = result.body[0]['Class']
        Relvar.insert(relvar='Select_Action', tuples=[
            Select_Action_i(Action=cls.action_id, Activity=anum, Class=cls.cname, Domain=domain,
                            Input_flow=cls.input_instance_flow, Selection_cardinality=cls.cardinality)
        ])

        cls.select_agroup = select_agroup
        cls.process_criteria(criteria=select_agroup.criteria)
        Transaction.execute()  # Select Action
