"""
statement.py – Populate all actions in a Scrall statement
"""

import logging
from pyral.relation import Relation
from xuml_populate.populate.actions.instance_assignment import InstanceAssignment
from xuml_populate.populate.actions.table_assignment import TableAssignment
from xuml_populate.populate.actions.scalar_assignment import ScalarAssignment
from xuml_populate.populate.actions.switch_action import SwitchAction
from xuml_populate.populate.actions.aparse_types import Activity_ap
from collections import namedtuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tkinter import Tk


class Statement:
    """
    Create all relations for a Statement
    """
    _logger = logging.getLogger(__name__)
    next_action_id = {}
    activity_type = None  # enum: state, ee, method
    state = None  # state name
    operation = None  # operation name
    method = None  # method name
    cname = None
    xi_flow_id = None

    @classmethod
    def populate(cls, mmdb: 'Tk', activity_data: Activity_ap, statement_parse: namedtuple):
        """
        Populate a Statement
        """
        statement_type = type(statement_parse).__name__
        # For now we'll just switch on the action_group name and later wrap all this up
        # into a dictionary of functions of some sort
        match statement_type:
            case 'Inst_Assignment_a':
                InstanceAssignment.process(mmdb, activity_data=activity_data, inst_assign=statement_parse)
            case 'Table_Assignment_a':
                TableAssignment.process(mmdb, anum=anum, cname=cls.cname, domain=domain,
                                        table_assign_parse=aparse.action_group, xi_flow_id=cls.xi_flow_id,
                                        activity_path=activity_path, scrall_text=scrall_text)
            case 'Scalar_Assignment_a':
                ScalarAssignment.process(mmdb, anum=anum, cname=cls.cname, domain=domain,
                                         scalar_assign_parse=aparse.action_group, xi_flow_id=cls.xi_flow_id,
                                         activity_path=activity_path, scrall_text=scrall_text)
            case 'Switch_a':
                SwitchAction.populate(mmdb,  sw_parse=aparse.action_group, anum=anum, domain=domain,
                                      activity_path=activity_path, scrall_text=scrall_text)
            case _:
                print()
