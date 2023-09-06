"""
switch_action.py – Populate a switch action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mm_class import MMclass
from scrall.parse.visitor import Switch_a
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Read_Action_i, Attribute_Read_Access_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class SwitchAction:
    """
    Create all relations for a Switch Action
    """

    mmdb = None  # The database
    anum = None  # Activity number
    action_id = None
    domain = None
    activity_path = None
    scrall_text = None

    @classmethod
    def populate(cls, mmdb: 'Tk', sw_parse: Switch_a, anum: str,
                 domain: str, activity_path: str, scrall_text: str):
        """
        Populate the Switch Action

        :param mmdb:
        :param sw_parse:  The parsed switch action group
        :param anum:
        :param domain:
        :param scrall_text:
        :param activity_path:
        """
        # For each case, create actions (open/close transaction) and create list of action ids
        cactions = {}
        for c in sw_parse.cases:
            pass
        pass
