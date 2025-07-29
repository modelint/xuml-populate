"""
statement.py – Populate all actions in a Scrall statement
"""

# System
import logging
from collections import namedtuple
from typing import Set

# xuml Populate
from xuml_populate.populate.actions.call_statement import CallStatement
from xuml_populate.populate.actions.signal_action import SignalAction
from xuml_populate.populate.actions.instance_assignment import InstanceAssignment
from xuml_populate.populate.actions.table_assignment import TableAssignment
from xuml_populate.populate.actions.scalar_assignment import ScalarAssignment
from xuml_populate.populate.actions.switch_statement import SwitchStatement
from xuml_populate.populate.actions.create_action import CreateAction
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions, Labeled_Flow

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
    def populate(cls, activity_data: ActivityAP, statement_parse: namedtuple,
                 case_name: str = '', case_outputs: Set[Labeled_Flow] = None) -> Boundary_Actions:
        """
        Populate a Statement

        :param activity_data:
        :param statement_parse:  A single parsed statement for us to populate
        :param case_name:  Values matched by case concatenated into a string
        :param case_outputs: Each output labeled data flow in the case, if any
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
                sa = ScalarAssignment(activity_data=activity_data, scalar_assign_parse=statement_parse)
                boundary_actions = sa.process()
                pass
            case 'Switch_a':
                boundary_actions = SwitchStatement.populate(activity_data=activity_data,
                                                            sw_parse=statement_parse)
            case 'Call_a':
                call_s = CallStatement(activity_data=activity_data, call_parse=statement_parse)
                boundary_actions = None  # TODO: Check this
                pass
            case 'Signal_a':
                sig_s = SignalAction(activity_data=activity_data, statement_parse=statement_parse)
                boundary_actions = sig_s.process()
            case 'New_inst_a':
                create_s = CreateAction(activity_data=activity_data, statement_parse=statement_parse)
                boundary_actions = create_s.process()
            case _:
                boundary_actions = None
                # print()

        return boundary_actions
