"""
switch_statement.py – Populate a switch action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING
from xuml_populate.exceptions.action_exceptions import ActionException, BadScalarSwitchInput
from xuml_populate.populate.actions.aparse_types import Activity_ap, Boundary_Actions
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from scrall.parse.visitor import Switch_a
from xuml_populate.populate.mmclass_nt import (Switch_Action_i, Scalar_Switch_Action_i, Case_i, Match_Value_i,
                                               Control_Dependency_i, Result_i, Sequence_Flow_i,
                                               Decision_Input_i, Decision_Action_i,
                                               Subclass_Switch_Action_i)
from pyral.relvar import Relvar
from pyral.relation import Relation  # Keep here for debugging
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)

from collections import namedtuple
Case_Control = namedtuple("Case_Control", "match_values target_actions")

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
        cls.mmdb = mmdb
        cls.anum = activity_data.anum
        cls.domain = activity_data.domain

        # Process the input flow
        scalar_input_flow = None
        match type(sw_parse.input_flow).__name__:
            case 'IN_a':
                # Verify that this is a scalar flow and get its flow id based on the label
                scalar_input_flow = Flow.find_labeled_scalar_flow(name=sw_parse.input_flow.name, anum=cls.anum,
                                                                  domain=cls.domain)
                if not scalar_input_flow:
                    _logger.error(f"Scalar switch on parameter [{sw_parse.input_flow.name}] is not a scalar flow")
                    raise BadScalarSwitchInput
            case 'INST_PROJ_a':
                pass
            case _:
                # TODO: implement other cases (N_a, ?)
                pass
        # For each case, create actions (open/close transaction) and create list of action ids
        cactions = {}
        for c in sw_parse.cases:
            # Need to create a Control Flow / Case instnace per case_value and label it with the case_value name
            # Combined with the action_id to ensure label is unique within the Activity
            # Need to create all component set statements and obtain a set of initial action ids
            if c.comp_statement_set.statement:
                case_name = f"{'_'.join(c.enums)}"
                from xuml_populate.populate.statement import Statement
                boundary_actions = Statement.populate(mmdb, activity_data=activity_data,
                                                      statement_parse=c.comp_statement_set.statement,
                                                      case_prefix=case_name)
                cactions[case_name] = Case_Control(match_values=c.enums, target_actions=boundary_actions.ain)
            else:
                if not c.component_statement_set.block:
                    raise ActionException
                # process block
                pass
            pass
        # Populate the Action superclass instance and obtain its action_id
        cls.action_id = Action.populate(cls.mmdb, cls.anum, cls.domain)  # Transaction open
        Relvar.insert(relvar='Switch_Action', tuples=[
            Switch_Action_i(ID=cls.action_id, Activity=cls.anum, Domain=cls.domain)
        ])
        Relvar.insert(relvar='Scalar_Switch_Action', tuples=[
            Scalar_Switch_Action_i(ID=cls.action_id, Activity=cls.anum, Domain=cls.domain,
                                   Scalar_input=scalar_input_flow.fid)
        ])
        control_flow_fid = None
        for k, v in cactions.items():
            control_flow_fid = Flow.populate_control_flow(mmdb, label=k, enabled_actions=v.target_actions,
                                                          activity=cls.anum, domain=cls.domain)
            Relvar.insert(relvar='Case', tuples=[
                Case_i(Flow=control_flow_fid, Activity=cls.anum, Domain=cls.domain, Switch_action=cls.action_id)
            ])
            for mv in v.match_values:
                Relvar.insert(relvar='Match_Value', tuples=[
                    Match_Value_i(Case_flow=control_flow_fid, Activity=cls.anum, Domain=cls.domain, Value=mv)
                ])
                pass
            # TODO: Create cases and control dependencies
        Transaction.execute()

        # For a switch statement, the switch action is both the initial and output action
        # Initial, because the Switch Action is the one Action in the statement that does not
        # depend on any other data input.
        # Also the final output since regardless of what case
        return Boundary_Actions(ain={cls.action_id}, aout={cls.action_id})
