"""
select_action.py – Populate a selection action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from class_model_dsl.exceptions.action_exceptions import ComparingNonAttributeInSelection, NoInputInstanceFlow
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
    comparison_criteria = []
    restriction_text = ""
    cardinality = None
    domain = None  # in this domain
    mmdb = None  # The database

    @classmethod
    def determine_cardinality(cls):
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
    def walk_criteria(cls, operator, operands, attr: bool = False) -> str:
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
                case 'N_a':
                    if not attr_set:
                        cls.process_attr(name=o.name, op=operator)
                        text = f"{o.name} {text}"
                        attr_set = True
                    else:
                        cls.process_flow(o.name, False)
                case 'BOOL_a':
                    cls.walk_criteria(o.op, o.operands, attr_set)
                case 'MATH_a':
                    print()
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
        cls.walk_criteria(op, operands)
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
        # Determine this flow's Class Type
        R = f"ID:<{input_instance_flow}>, Activity:<{anum}>, Domain:<{cls.domain}>"
        result = Relation.restrict3(cls.mmdb, relation='Instance_Flow', restriction=R)
        if not result.body:
            raise NoInputInstanceFlow(f"select action input flow [{input_instance_flow}:{anum}:{domain}]"
                                      f" is not an instance flow")
        cls.cname = result.body[0]['Class']

        cls.select_agroup = select_agroup
        cls.process_criteria(criteria=select_agroup.criteria)
        pass
