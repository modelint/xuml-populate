"""
select_action.py – Populate a selection action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from scrall.parse.visitor import PATH_a
from class_model_dsl.populate.actions.action import Action
from class_model_dsl.populate.flow import Flow
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from collections import namedtuple

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)

class SelectAction:
    """
    Create all relations for a Select Statement
    """

    input_flow = None

    @classmethod
    def process_flow(cls, name:str, input_param:bool):
        print(f"Populating [{name}] as flow")

    @classmethod
    def process_attr(cls, name):
        print(f"Populating [{name}] as attribute")
        cls.attr_set = True

    @classmethod
    def walk_criteria(cls, operator, operands, attr: bool = False):
        attr_set = attr
        # left_op = operands[0]
        # right_op = None if len(operands) < 2 else operands[1]
        for o in operands:
            match type(o).__name__:
                case 'IN_a':
                    cls.process_flow(o, True)
                case 'N_a':
                    if not attr_set:
                        cls.process_attr(o.name)
                        attr_set = True
                    else:
                        cls.process_flow(o.name, False)
                case 'BOOL_a':
                    cls.walk_criteria(o.op, o.operands, attr_set)
                case 'MATH_a':
                    print()
                case 'UNARY_a':
                    print()

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
        cls.walk_criteria(criteria.op, criteria.operands)
        pass


    @classmethod
    def populate(cls, input_flow:str, select_agroup):
        """
        Populate the Select Statement

        :param select_agroup:  The parsed Scrall select action group
        :param input_flow: The name of a Class or an Instance Flow
        """
        cls.input_flow = input_flow
        cls.select_agroup = select_agroup
        cls.process_criteria(criteria=select_agroup.criteria)