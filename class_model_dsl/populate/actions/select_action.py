"""
select_action.py – Populate a selection action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from class_model_dsl.parse.scrall_visitor import PATH_a
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

    source_flow = None


    @classmethod
    def populate(cls, input_name:str):
        """
        Populate the Select Statement

        :param input_name: The name of a Class or an Instance Flow
        """
        pass
