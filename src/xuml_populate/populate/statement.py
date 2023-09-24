"""
statement.py – Populate all actions in a Scrall statement
"""

import logging
from pyral.relation import Relation
from xuml_populate.populate.actions.instance_assignment import InstanceAssignment
from xuml_populate.populate.actions.table_assignment import TableAssignment
from xuml_populate.populate.actions.scalar_assignment import ScalarAssignment
from xuml_populate.populate.actions.switch_statement import SwitchStatement
from xuml_populate.populate.actions.aparse_types import Activity_ap, Boundary_Actions
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
    def populate(cls, mmdb: 'Tk', activity_data: Activity_ap, statement_parse: namedtuple, case_prefix=''
                 ) -> Boundary_Actions:
        """
        Populate a Statement

        :param mmdb:
        :param activity_data:
        :param statement_parse:
        :param case_prefix:
        :return:
        """
        statement_type = type(statement_parse).__name__
        # For now we'll just switch on the action_group name and later wrap all this up
        # into a dictionary of functions of some sort
        boundary_actions = Boundary_Actions(ain=[], aout=[])
        match statement_type:
            case 'Inst_Assignment_a':
                boundary_actions = InstanceAssignment.process(mmdb, activity_data=activity_data,
                                                              inst_assign=statement_parse, case_prefix=case_prefix)
                pass
            case 'Table_Assignment_a':
                boundary_actions = TableAssignment.process(mmdb, activity_data=activity_data,
                                                           table_assign_parse=statement_parse, case_prefix=case_prefix)
                pass
            case 'Scalar_Assignment_a':
                boundary_actions = ScalarAssignment.process(mmdb, activity_data=activity_data,
                                                            scalar_assign_parse=statement_parse)
                pass
            case 'Switch_a':
                boundary_actions = SwitchStatement.populate(mmdb, activity_data=activity_data,
                                                            sw_parse=statement_parse)
            case _:
                boundary_actions = None
                print()

        return boundary_actions
