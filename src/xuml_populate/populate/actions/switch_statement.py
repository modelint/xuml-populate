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
from xuml_populate.exceptions.action_exceptions import ActionException, BadScalarSwitchInput
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

    output_actions = None
    labeled_outputs = None

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
        self.labeled_outputs = {}  # { <case>: [output_flow, ...], }  labeled output flows keyed by case

    def populate(self) -> Boundary_Actions:
        """
        """
        # Process the input flow
        scalar_input_flow = None
        match type(self.parse.input_flow).__name__:
            case 'IN_a':
                # Verify that this is a scalar flow and get its flow id based on the label
                scalar_input_flows = Flow.find_labeled_scalar_flow(name=self.parse.input_flow.name, anum=self.anum,
                                                                  domain=self.domain)
                scalar_input_flow = scalar_input_flows[0] if scalar_input_flows else None
                # TODO: Check for case where multiple are returned
                if not scalar_input_flow:
                    _logger.error(f"Scalar switch on parameter [{self.parse.input_flow.name}] is not a scalar flow")
                    raise BadScalarSwitchInput
            case 'INST_PROJ_a':
                pass
            case 'R_a':
                # This is a subclass switch action
                pass
            case _:
                # TODO: implement other cases (N_a, ?)
                pass
        # For each case, create actions (open/close transaction) and create list of action ids
        cactions = {}
        for c in self.parse.cases:
            # Need to create a Control Flow / Case instnace per case_value and label it with the case_value name
            # Combined with the action_id to ensure label is unique within the Activity
            # Need to create all component set statements and obtain a set of initial_pseudo_state action ids
            if c.comp_statement_set.statement:
                case_name = f"{'_'.join(c.enums)}"
                self.labeled_outputs[case_name] = set()
                from xuml_populate.populate.statement import Statement
                boundary_actions = Statement.populate(activity=self.activity,
                                                      statement_parse=c.comp_statement_set.statement,
                                                      case_name=case_name,
                                                      case_outputs=self.labeled_outputs[case_name])
                self.output_actions = self.output_actions.union(boundary_actions.aout)
                cactions[case_name] = Case_Control(match_values=c.enums, target_actions=boundary_actions.ain)
            else:
                if not c.component_statement_set.block:
                    raise ActionException
                # process block
                pass
            pass
        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Switch)
        action_id = Action.populate(tr=tr_Switch, anum=self.anum, domain=self.domain, action_type="scalar switch")  # Transaction open
        # TODO: It appears that the Subclass Switch Action has is not yet populated/implemented
        Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Switch_Action', tuples=[
            Switch_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Scalar_Switch_Action', tuples=[
            Scalar_Switch_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain,
                                   Scalar_input=scalar_input_flow.fid)
        ])
        for k, v in cactions.items():
            control_flow_fid = Flow.populate_control_flow(tr=tr_Switch, label=k, enabled_actions=v.target_actions,
                                                          anum=self.anum, domain=self.domain)
            Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Case', tuples=[
                Case_i(Flow=control_flow_fid, Activity=self.anum, Domain=self.domain, Switch_action=action_id)
            ])
            for mv in v.match_values:
                Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Match_Value', tuples=[
                    Match_Value_i(Case_flow=control_flow_fid, Activity=self.anum, Domain=self.domain, Value=mv)
                ])
                pass
            # TODO: Create cases and control dependencies

        # Get all labels that appear in more than one case
        # (The same label cannot appear more than once in the same case since label names are unique within a case)
        # First create a bag of labels (list with possible duplicates) ranging over all cases
        all_labels = [lf.label for v in self.labeled_outputs.values() for lf in v]
        # all_labels_ = [{k:lf.label} for k, v in self.labeled_outputs.items() for lf in v]
        all_flows = [lf for v in self.labeled_outputs.values() for lf in v]
        # Now filter out only those labels that appear more than once
        label_count = Counter(all_labels)
        multi_case_labels = {label for label, count in label_count.items() if count > 1}
        # For each multi_case_label, verify type/content/multipicity compatibility
        # We create a dict keyed by multi_case_label wiht a list of flows per key
        mcl_flows = {mcl: [f.flow for f in all_flows if f.label == mcl] for mcl in multi_case_labels}
        for flows in mcl_flows.values():
            # Create list of flows from flow component of each Labeled_Flow and verify that they are all compatible
            if not Flow.compatible(flows):
                raise ActionException
            pass
        pass
        # Gate Action
        # Create an output Data Flow for each multi case label
        output_flows = {}

        # Populate the Gate Action and get an action id
        gate_aid = Action.populate(tr=tr_Switch, anum=self.anum, domain=self.domain, action_type="gate")
        for mcl in multi_case_labels:
            output_flows[mcl] = Flow.populate_switch_output(label=mcl, ref_flow=mcl_flows[mcl][0],
                                                            anum=self.anum, domain=self.domain)
            Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Instance Action', tuples=[
                Instance_Action_i(ID=gate_aid, Activity=self.anum, Domain=self.domain)
            ])
            Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Flow Connector', tuples=[
                Instance_Action_i(ID=gate_aid, Activity=self.anum, Domain=self.domain)
            ])
            Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Gate Action', tuples=[
                Gate_Action_i(ID=gate_aid, Output_flow=output_flows[mcl].fid, Activity=self.anum, Domain=self.domain)
            ])

        for label, flows in mcl_flows.items():
            for f in flows:
                Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Gate Input', tuples=[
                    Gate_Input_i(Input_flow=f.fid, Activity=self.anum, Domain=self.domain,
                                 Gate_action=gate_aid)
                ])

        # for sc, lfset in self.labeled_outputs.items():
        #     for lf in lfset:
        #         if lf.label in multi_case_labels:
        #             # Create the output flow
        #             Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Data_Flow', tuples=[
        #                 Table_i()
        #             ])
        #             pass

        # Create the output dataflow
        # Create a switch for each such multi_case_label
        # Create an input to the switch for each case where the label appears that connects to
        # and connect the corresponding flow

        # x = {i.label for f in self.labeled_outputs.items() for i in f}
        # TODO: Create data flow switches
        Transaction.execute(db=mmdb, name=tr_Switch)

        # For a switch statement, the switch action is both the initial_pseudo_state and output action
        # Initial, because the Switch Action is the one Action in the statement that does not
        # depend on any other data input.
        # Also the final output since regardless of what case
        return Boundary_Actions(ain={action_id}, aout=self.output_actions)
