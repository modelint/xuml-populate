"""
statement.py – Populate all actions in a Scrall statement
"""

import logging
from xuml_populate.config import mmdb
from pyral.relation import Relation
from xuml_populate.populate.actions.instance_assignment import InstanceAssignment
from xuml_populate.populate.actions.table_assignment import TableAssignment
from xuml_populate.populate.actions.scalar_assignment import ScalarAssignment
from xuml_populate.populate.actions.switch_statement import SwitchStatement
from xuml_populate.populate.actions.aparse_types import Activity_ap, Boundary_Actions, Labeled_Flow
from collections import namedtuple
from typing import Dict, Set, List

_logger = logging.getLogger(__name__)

class Statement:
    """
    Create all relations for a Statement
    """
    next_action_id = {}
    activity_type = None  # enum: state, ee, method
    state = None  # state name
    operation = None  # operation name
    method = None  # method name
    cname = None
    xi_flow_id = None

    @classmethod
    def populate(cls, activity_data: Activity_ap, statement_parse: namedtuple,
                 case_name: str = '', case_outputs: Set[Labeled_Flow] = None) -> Boundary_Actions:
        """
        Populate a Statement

        :param activity_data:
        :param statement_parse:
        :param case_name:  Values matched by case concatenated into a string
        :param case_outputs: Each output labeled data flow in the case
        :return:
        """
        statement_type = type(statement_parse).__name__
        # For now we'll just switch on the action_group name and later wrap all this up
        # into a dictionary of functions of some sort
        match statement_type:
            case 'Inst_Assignment_a':
                boundary_actions = InstanceAssignment.process(activity_data=activity_data,
                                                              inst_assign=statement_parse,
                                                              case_name=case_name,
                                                              case_outputs=case_outputs,
                                                              )
                pass
            case 'Table_Assignment_a':
                boundary_actions = TableAssignment.process(activity_data=activity_data,
                                                           table_assign_parse=statement_parse,
                                                           case_name=case_name,
                                                           case_outputs=case_outputs)
                pass
            case 'Scalar_Assignment_a':
                boundary_actions = ScalarAssignment.process(activity_data=activity_data,
                                                            scalar_assign_parse=statement_parse,
                                                            # case_outputs=case_outputs,
                                                            # case_prefix=case_prefix
                                                            )
                pass
            case 'Switch_a':
                boundary_actions = SwitchStatement.populate(activity_data=activity_data,
                                                            sw_parse=statement_parse)
            case _:
                boundary_actions = None
                # print()

        return boundary_actions
