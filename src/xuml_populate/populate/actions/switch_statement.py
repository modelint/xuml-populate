"""
switch_statement.py – Populate a switch action instance in PyRAL
"""

import logging
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import ActionException, BadScalarSwitchInput
from xuml_populate.populate.actions.aparse_types import Activity_ap, Boundary_Actions
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from scrall.parse.visitor import Switch_a
from xuml_populate.populate.mmclass_nt import (Switch_Action_i, Scalar_Switch_Action_i, Case_i, Match_Value_i,
                                               Control_Dependency_i, Result_i, Sequence_Flow_i,
                                               Decision_Input_i, Decision_Action_i,
                                               Subclass_Switch_Action_i, Switched_Data_Flow_i, Data_Flow_Switch_i)
from pyral.relvar import Relvar
from pyral.relation import Relation  # Keep here for debugging
from pyral.transaction import Transaction

_logger = logging.getLogger(__name__)

from collections import namedtuple, Counter

Case_Control = namedtuple("Case_Control", "match_values target_actions")

# Transactions
tr_Switch = "Switch Action"

class SwitchStatement:
    """
    Create all relations for a Switch Action
    """

    output_actions = None
    labeled_outputs = None

    @classmethod
    def populate(cls, sw_parse: Switch_a, activity_data: Activity_ap) -> Boundary_Actions:
        """
        Populate the Switch Action and its Cases

        :param sw_parse:  The parsed switch action group
        :param activity_data:
        """
        anum = activity_data.anum
        domain = activity_data.domain
        cls.output_actions = set()
        cls.labeled_outputs = {}  # { <case>: [output_flow, ...], }  labeled output flows keyed by case

        # Process the input flow
        scalar_input_flow = None
        match type(sw_parse.input_flow).__name__:
            case 'IN_a':
                # Verify that this is a scalar flow and get its flow id based on the label
                scalar_input_flow = Flow.find_labeled_scalar_flow(name=sw_parse.input_flow.name, anum=anum,
                                                                  domain=domain)
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
                cls.labeled_outputs[case_name] = set()
                from xuml_populate.populate.statement import Statement
                boundary_actions = Statement.populate(activity_data=activity_data,
                                                      statement_parse=c.comp_statement_set.statement,
                                                      case_name=case_name,
                                                      case_outputs=cls.labeled_outputs[case_name])
                cls.output_actions = cls.output_actions.union(boundary_actions.aout)
                cactions[case_name] = Case_Control(match_values=c.enums, target_actions=boundary_actions.ain)
            else:
                if not c.component_statement_set.block:
                    raise ActionException
                # process block
                pass
            pass
        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Switch)
        action_id = Action.populate(tr=tr_Switch, anum=anum, domain=domain, action_type="switch")  # Transaction open
        Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Switch_Action', tuples=[
            Switch_Action_i(ID=action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Scalar_Switch_Action', tuples=[
            Scalar_Switch_Action_i(ID=action_id, Activity=anum, Domain=domain,
                                   Scalar_input=scalar_input_flow.fid)
        ])
        for k, v in cactions.items():
            control_flow_fid = Flow.populate_control_flow(tr=tr_Switch, label=k, enabled_actions=v.target_actions,
                                                          anum=anum, domain=domain)
            Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Case', tuples=[
                Case_i(Flow=control_flow_fid, Activity=anum, Domain=domain, Switch_action=action_id)
            ])
            for mv in v.match_values:
                Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Match_Value', tuples=[
                    Match_Value_i(Case_flow=control_flow_fid, Activity=anum, Domain=domain, Value=mv)
                ])
                pass
            # TODO: Create cases and control dependencies

        # Get all labels that appear in more than one case
        # (The same label cannot appear more than once in the same case since label names are unique within a case)
        # First create a bag of labels (list with possible duplicates) ranging over all cases
        all_labels = [lf.label for v in cls.labeled_outputs.values() for lf in v]
        # all_labels_ = [{k:lf.label} for k, v in cls.labeled_outputs.items() for lf in v]
        all_flows = [lf for v in cls.labeled_outputs.values() for lf in v]
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
        # Data Flow Switch
        # Create an output Data Flow for each multi case label
        output_flows = {}
        for mcl in multi_case_labels:
            output_flows[mcl] = Flow.populate_switch_output(label=mcl, ref_flow=mcl_flows[mcl][0],
                                                            anum=anum, domain=domain)
            Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Data_Flow_Switch', tuples=[
                Data_Flow_Switch_i(Output_flow=output_flows[mcl].fid, Activity=anum, Domain=domain)
            ])
        for label, flows in mcl_flows.items():
            for f in flows:
                Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Switched_Data_Flow', tuples=[
                    Switched_Data_Flow_i(Input_flow=f.fid, Activity=anum, Domain=domain,
                                         Output_flow=output_flows[label].fid)
                ])

        # for sc, lfset in cls.labeled_outputs.items():
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

        # x = {i.label for f in cls.labeled_outputs.items() for i in f}
        # TODO: Create data flow switches
        Transaction.execute(db=mmdb, name=tr_Switch)

        # For a switch statement, the switch action is both the initial and output action
        # Initial, because the Switch Action is the one Action in the statement that does not
        # depend on any other data input.
        # Also the final output since regardless of what case
        return Boundary_Actions(ain={action_id}, aout=cls.output_actions)
