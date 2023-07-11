"""
select_action.py – Populate a selection action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from scrall.parse.visitor import PATH_a
from class_model_dsl.populate.actions.action import Action
from class_model_dsl.populate.flow import Flow
from PyRAL.relvar import Relvar
from PyRAL.relation import Relation
from PyRAL.transaction import Transaction
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
    def process_criteria(cls, criteria):
        for c in criteria:
            match type(c).__name__:
                case 'N_a':
                    # We have an attribute
                    print()
                case _:
                    _logger.error("No match case for criteria in select populate")

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