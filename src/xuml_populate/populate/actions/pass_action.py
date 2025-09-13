"""
pass_action.py – Populate a pass action instance in PyRAL
"""

# System
import logging
from typing import Sequence, TYPE_CHECKING, Optional
from collections import namedtuple
import re

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.utility import print_mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.gate_action import GateAction
from xuml_populate.populate.mmclass_nt import Pass_Action_i, Instance_Action_i, Flow_Connector_i

_logger = logging.getLogger(__name__)

# Transactions
tr_Pass = "Pass Action"

PassOutput = namedtuple('PassOutput', 'aid fid')


class PassAction:
    """
    Populate a Pass Action
    """

    def __init__(self, input_fid: str, output_flow_label: str, activity: 'Activity'):
        """
        Collect the data necessary to populate a Pass Action

        Args:
            input_fid: The id of an existing Data Flow
            output_flow_label: The name of the passed output flow to be created
            activity: The enclosing Activity
        """
        self.input_fid = input_fid
        self.output_flow_label = output_flow_label

        self.anum = activity.anum
        self.domain = activity.domain
        self.activity = activity

        self.action_id = None
        self.flow_to_new_gate: Optional[PassOutput] = None
        self.flow_to_existing_gate = None

    def populate(self) -> tuple[str, Flow_ap]:
        """
        Populate the Pass Action

        Returns:
            A tuple with the action id and output Data Flow
        """
        # pass_actions_sv = 'pass_actions_sv'
        labeled_flows_sv = 'labeled_flows_sv'
        # First check to see if there is one other Pass with the same output flow label, in this Activity

        # Get all the Pass Actions in this Activity
        R = f"Activity:<{self.anum}>, Domain:<{self.domain}>"
        pa_r = Relation.restrict(db=mmdb, relation="Pass Action", restriction=R)
        # Find all related Labeled Flows output from those Pass Actions
        lf_r = Relation.join(db=mmdb, rname2="Labeled Flow", attrs={
            "Activity": "Activity", "Domain": "Domain", "Output_flow": "ID"
        }, svar_name=labeled_flows_sv)
        # Find any label names that match our output flow label
        R = f"Name:<{self.output_flow_label}>"
        duplicate_labeled_flow_r = Relation.restrict(db=mmdb, restriction=R)
        if duplicate_labeled_flow_r.body:
            # There is another Pass Action outputting a flow with the same label
            # We will create a gate and flow that Pass Action's output Flow ID
            # Along with the output of the new Pass Action to a newly created Gate
            self.flow_to_new_gate = PassOutput(aid=duplicate_labeled_flow_r.body[0]['ID'],
                                               fid=duplicate_labeled_flow_r.body[0]['Output_flow'])
            pass

        if not self.flow_to_new_gate and pa_r.body:
            # There may be an existing gate
            # If so, the Pass Action outputs to that Gate Action will match a pattern with
            # an underscore prefix followed by the action number and another underscore
            # in front of the output label name.
            pass_name_pattern = re.compile(rf'_([1-9]\d*)_{re.escape(self.output_flow_label)}$')
            gate_input_labels = [n['Name'] for n in lf_r.body if pass_name_pattern.search(n)]
            # TODO: Look up flows for each name and add to self.flow_to_existing_gate
            pass

        Transaction.open(db=mmdb, name=tr_Pass)
        pass_aid = Action.populate(tr=tr_Pass, anum=self.anum, domain=self.domain, action_type="pass")

        # Use supplied output flow label unless we are feeding into a gate
        # in which case, prefix with the action id
        if self.flow_to_new_gate:
            # Use prefix
            output_label = f"_{pass_aid[4:]}_{self.output_flow_label}"
        else:
            output_label = self.output_flow_label

        pass_output_flow = Flow.copy_data_flow(tr=tr_Pass, ref_fid=self.input_fid,
                                               ref_anum=self.anum, new_anum=self.anum, domain=self.domain,
                                               label=output_label)
        Relvar.insert(db=mmdb, tr=tr_Pass, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=pass_aid, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Pass, relvar='Flow Connector', tuples=[
            Flow_Connector_i(ID=pass_aid, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Pass, relvar='Pass Action', tuples=[
            Pass_Action_i(ID=pass_aid, Activity=self.anum, Domain=self.domain, Input_flow=self.input_fid,
                          Output_flow=pass_output_flow.fid)
        ])
        Transaction.execute(db=mmdb, name=tr_Pass)

        # Rename the other matching pass flow and feed both into the new gate
        if self.flow_to_new_gate:
            # Relabel the other Pass Action output to match it's action
            gate_input_label = f"_{self.flow_to_new_gate.aid[4:]}_{self.output_flow_label}"
            Flow.relabel_flow(new_label=gate_input_label, fid=self.flow_to_new_gate.fid, anum=self.anum,
                              domain=self.domain)

            # Populate the Gate Action
            ga = GateAction(input_flows=[pass_output_flow.fid, self.flow_to_new_gate.fid],
                            output_flow_label=self.output_flow_label, activity=self.activity)
            gate_aid, gate_output_flow = ga.populate()

        return pass_aid, pass_output_flow
