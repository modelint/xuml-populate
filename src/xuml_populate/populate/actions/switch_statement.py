"""
switch_statement.py – Populate a switch action instance in PyRAL
"""
# System
import logging
from typing import TYPE_CHECKING
from collections import namedtuple, Counter

# Model Integration
from scrall.parse.visitor import Switch_a
from pyral.relvar import Relvar
from pyral.relation import Relation  # Keep here for debugging
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import (Switch_Action_i, Scalar_Switch_Action_i, Case_i, Match_Value_i,
                                               Sequence_Flow_i, Subclass_Switch_Action_i, Gate_Action_i, Gate_Input_i,
                                               Instance_Action_i, Flow_Connector_i)

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)


Case_Control = namedtuple("Case_Control", "match_values target_actions")

# Transactions
tr_Switch = "Switch Action"

class SwitchStatement:
    """
    Create all relations for a Switch Action
    """

    def __init__(self, sw_parse: Switch_a, activity: 'Activity'):
        """
        Args:
            sw_parse: Parsed switch statement
            activity: Enclosing activity object
        """
        self.parse = sw_parse
        self.activity = activity
        self.anum = activity.anum
        self.domain = activity.domain

        self.output_actions = set()

        self.subclass_switch_rnum = None  # Default assumption
        self.superclass_fid = None

    def validate_gen(self):
        """
        Raises exception if the input to a Subclass Switch Action is invalid
        """
        rnum = self.parse.input_flow.rnum
        cases = {enum for c in self.parse.cases for enum in c.enums}
        R = f"Rnum:<{rnum}>, Domain:<{self.domain}>"
        superclass_r = Relation.restrict(db=mmdb, relation="Superclass", restriction=R)
        if not superclass_r.body:
            msg = f"Switch input rnum {self.domain}::{rnum} not defined in at {self.activity.activity_path}"
            _logger.error(msg)
            ActionException(msg)
        subclasses_r = Relation.restrict(db=mmdb, relation="Subclass", restriction=R)
        subclass_names = {s["Class"] for s in subclasses_r.body}
        if subclass_names != cases:
            msg = (f"Switch input cases {cases} do not match subclass names {subclass_names} "
                   f"at {self.activity.activity_path}")
            _logger.error(msg)
            ActionException(msg)


    def populate(self) -> Boundary_Actions:
        """
        Populate a Switch Statement
        """
        # Process the input flow
        scalar_input_flow = None
        match type(self.parse.input_flow).__name__:
            case 'IN_a' | 'N_a':
                # Verify that this is a scalar flow and get its flow id based on the label
                scalar_input_flows = Flow.find_labeled_scalar_flow(name=self.parse.input_flow.name, anum=self.anum,
                                                                   domain=self.domain)
                # Verify only one flow as input
                if len(scalar_input_flows) != 1:
                    msg = f"Switch statement expects a single Scalar Flow input at {self.activity.activity_path}"
                    _logger.error(msg)
                    raise ActionException(msg)
                scalar_input_flow = scalar_input_flows[0] if scalar_input_flows else None
                # TODO: Check for case where multiple are returned
                if not scalar_input_flow:
                    _logger.error(f"Scalar switch on parameter [{self.parse.input_flow.name}] is not a scalar flow")
                    raise BadScalarSwitchInput
            case 'INST_PROJ_a':
                # TODO: Support scalar expression input
                msg = "TODO: Support scalar expression as input into switch statement"
                _logger.error(msg)
                raise IncompleteActionException(msg)
            case 'R_a':
                # This is a subclass switch action
                self.validate_gen()  # Validate the generalization and subclasses
                # Set the rnum used for switching to the subclass cases
                self.subclass_switch_rnum = self.parse.input_flow.rnum
                # Since the R_a was supplied directly, we know that the executing instance must be the superclass
                self.superclass_fid = self.activity.xiflow.fid
            case _:
                # TODO: Any other cases possible?
                msg = "TODO: Support unknown expression input into switch statement"
                _logger.error(msg)
                raise IncompleteActionException(msg)

        # For each case, create actions (open/close transaction) and create list of action ids
        from xuml_populate.populate.xunit import ExecutionUnit
        cactions = {}
        for c in self.parse.cases:
            # Need to create a Control Flow / Case instnace per case_value and label it with the case_value name
            # Combined with the action_id to ensure label is unique within the Activity
            # Need to create all component set statements and obtain a set of initial_pseudo_state action ids
            case_name = f"_{'_'.join(c.enums)}"
            boundary_actions = ExecutionUnit.process_statement_set(activity=self.activity, content=c.comp_statement_set)
            self.output_actions = self.output_actions.union(boundary_actions.aout)
            cactions[case_name] = Case_Control(match_values=c.enums, target_actions=boundary_actions.ain)

        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Switch)
        action_id = Action.populate(tr=tr_Switch, anum=self.anum, domain=self.domain, action_type="scalar switch")
        Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Switch Action', tuples=[
            Switch_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain)
        ])
        if not self.subclass_switch_rnum:
            Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Scalar Switch Action', tuples=[
                Scalar_Switch_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain,
                                       Scalar_input=scalar_input_flow.fid)
            ])
        else:
            Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Subclass Switch Action', tuples=[
                Subclass_Switch_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain,
                                         Superclass_instance=self.superclass_fid, Generalization=self.subclass_switch_rnum)
            ])

        for k, v in cactions.items():
            control_flow_fid = Flow.populate_control_flow(tr=tr_Switch, label=k, enabled_actions=v.target_actions,
                                                          anum=self.anum, domain=self.domain)
            Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Case', tuples=[
                Case_i(Flow=control_flow_fid, Activity=self.anum, Domain=self.domain, Switch_action=action_id)
            ])
            for mv in v.match_values:
                Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Match Value', tuples=[
                    Match_Value_i(Case_flow=control_flow_fid, Activity=self.anum, Domain=self.domain, Value=mv)
                ])

        Transaction.execute(db=mmdb, name=tr_Switch)

        # For a switch statement, the switch action is both the initial state and output action
        # Initial, because the Switch Action is the one Action in the statement that does not
        # depend on any other data input.
        # Also the final output since regardless of what case
        return Boundary_Actions(ain={action_id}, aout=self.output_actions)
