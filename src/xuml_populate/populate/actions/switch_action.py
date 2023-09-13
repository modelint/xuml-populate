"""
switch_action.py – Populate a switch action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
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
    def populate(cls, mmdb: 'Tk', sw_parse: Switch_a, activity_data: Activity_ap):
        """
        Populate the Switch Action

        :param mmdb:
        :param sw_parse:  The parsed switch action group
        :param activity_data:
        """
        # For each case, create actions (open/close transaction) and create list of action ids
        cactions = {}
        for c in sw_parse.cases:
            pass
        pass
