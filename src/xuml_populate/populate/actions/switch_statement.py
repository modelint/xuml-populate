"""
switch_statement.py – Populate a switch action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING
from xuml_populate.exceptions.action_exceptions import ActionException
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap, Boundary_Actions
# from xuml_populate.populate.actions.action import Action
# from xuml_populate.populate.mm_class import MMclass
from scrall.parse.visitor import Switch_a
# from xuml_populate.populate.flow import Flow
# from xuml_populate.populate.mmclass_nt import Read_Action_i, Attribute_Read_Access_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class SwitchStatement:
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
    def populate(cls, mmdb: 'Tk', sw_parse: Switch_a, activity_data: Activity_ap) -> Boundary_Actions:
        """
        Populate the Switch Action and its Cases

        :param mmdb:
        :param sw_parse:  The parsed switch action group
        :param activity_data:
        """
        # For each case, create actions (open/close transaction) and create list of action ids
        cactions = {}
        for c in sw_parse.cases:
            # Need to create a Control Flow / Case instnace per case_value and label it with the case_value name
            # Combined with the action_id to ensure label is unique within the Activity
            # Need to create all component set statements and obtain a set of initial action ids
            if c.comp_statement_set.statement:
                case_prefix = f"<{','.join(c.enums)}>_"
                from xuml_populate.populate.statement import Statement
                boundary_actions = Statement.populate(mmdb, activity_data=activity_data,
                                                      statement_parse=c.comp_statement_set.statement,
                                                      case_prefix=case_prefix)
                cactions[case_prefix] = boundary_actions
                pass
            else:
                if not c.component_statement_set.block:
                    raise ActionException
                # process block
                pass
            pass
        # TODO: resolve boundary actions
        # TODO: create the switch action
        pass
        return Boundary_Actions(ain={}, aout={})
