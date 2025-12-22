"""
gate_action.py – Populate a Gate Action instance
"""

# System
import logging
from typing import Sequence, TYPE_CHECKING, Optional
import re

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

from xuml_populate.exceptions.action_exceptions import ActionException

# xUML populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Gate_Input_i, Gate_Action_i, Instance_Action_i, Flow_Connector_i

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

# Transactions
tr_Gate = "Gate Action"

class GateAction:
    """
    A Gate Action takes two or more mutually exclusive input flows and produces
    a single output flow corresponding to one of the inputs (selected during model execution).

    All flows in and out must match in both structure and multiplicity.

    For example:

        If the input flows are scalar, the output flow is scalar.

        If the input flows are mutliple instance flows, the output is a multiple instance flow.
    """
    @classmethod
    def gate_duplicate_labeled_nsflow(cls, aid: str, fid: str, label: str, activity: 'Activity'):
        """
        Given the flow label name, check to see if there is another Labeled Flow with the same name
        in the Activity. If so, populate a Gate, name the output of the gate using the duplicate label,
        and then change the name of each input flow to the format _aid_label, where aid is the
        action id of the gate input flow source, and the label is the duplicate flow label name.

        For example, if aid=ACTN23 and fid=F32 and we see that F32 is labeled with the name 'countable aslevs',
        and we find a duplicate labeled flow with fid=F34,
        we should have gate inputs labeled '_32_countable aslevs' and '_34_countable aslevs' with a gate output labeled
        'countable aslevs'.

        If there is no duplicate, we save the fid and its source in the dictionary for possible later comparison.

        Args:
            aid: The id of the Action that is the source of the fid flow
            fid: The Flow ID of a labeled flow
            label: The name of the flow label
            activity:  The enclosing Activity object
        """
        # Find all matching labeled Non Scalar Flows
        ns_flows = Flow.find_labeled_ns_flow(name=label, anum=activity.anum, domain=activity.domain)

        # This method requires an input labeled flow, so we fail if none are found
        if not ns_flows:
            msg = f"No Labeled Non Scalar Flow for {fid} in {activity.activity_path}"
            _logger.error(msg)
            raise ActionException(msg)

        # If there is no duplicate, we don't need a gate and just return
        if len(ns_flows) == 1:
            return

        # There should never be more than two since we rename the inputs as we attache
        # each to a new or existing gate
        if len(ns_flows) > 2:
            msg = f"Extra duplicate Labeled Non Scalar Flow for {fid} in {activity.activity_path}"
            _logger.error(msg)
            raise ActionException(msg)

        # We have the specified fid, and another Flow with a duplicate label name
        # That duplicate is either the output of an existing Gate Action or we need to populate
        # a Gate Action with both the fids as input. Figure out which of the two found flows is which
        f0, f1 = ns_flows
        if f0.fid == fid:
            supplied_flow, duplicate_flow = f0, f1
        else:
            supplied_flow, duplicate_flow = f1, f0

        # Check for existing gate
        # That gate will use the label name as its output
        R = f"Output_flow:<{duplicate_flow.fid}>, Activity:<{activity.anum}>, Domain:<{activity.domain}>"
        gate_action_r = Relation.restrict(db=mmdb, relation="Gate Action", restriction=R)
        if gate_action_r.body:
            # We need to attach the specified input as a gate input and relabel it
            pass
        else:
            # We need to create a new Gate Action
            ga = cls(input_fids=[supplied_flow.fid, duplicate_flow.fid], output_flow_label=label, activity=activity)
            gate_aid, gate_output_flow = ga.populate()
        return

    def __init__(self, input_fids: list[str], output_flow_label: str, activity: 'Activity'):
        """
        Collect the data necessary to populate a Gate Action

        Args:
            input_fids: The ids of two or more input_flows
            output_flow_label: The name of the gate output flow to be created
            activity: The enclosing Activity
        """
        self.anum = activity.anum
        self.domain = activity.domain
        self.activity = activity

        if len(input_fids) < 2:
            msg = f"Gate requires at least two input flow ids, but got: {input_fids} at {self.activity.activity_path}"
            _logger.error(msg)
            raise ActionException(msg)

        # Get Flow_ap for each fid
        self.input_flows = [Flow.lookup_data(fid=f, anum=self.anum, domain=self.domain) for f in input_fids]

        self.output_flow_label = output_flow_label

        self.action_id = None

    def populate(self) -> tuple[str, Flow_ap]:
        """
        Populate the Gate Action

        Returns:
            A tuple with the action id and output Data Flow
        """
        # Populate the Gate Action and get an action id
        Transaction.open(db=mmdb, name=tr_Gate)

        # Create the output flow by copying the structure of one of the input flows
        # Both anums are set the local activity number
        gate_output_flow = Flow.copy_data_flow(tr=tr_Gate, ref_fid=self.input_flows[0].fid, ref_anum=self.anum,
                                               new_anum=self.anum, domain=self.domain, label=self.output_flow_label)

        # Obtain an action id
        gate_aid = Action.populate(tr=tr_Gate, anum=self.anum, domain=self.domain, action_type="gate")

        # Populate all relevant classes
        Relvar.insert(db=mmdb, tr=tr_Gate, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=gate_aid, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Gate, relvar='Flow Connector', tuples=[
            Flow_Connector_i(ID=gate_aid, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Gate, relvar='Gate Action', tuples=[
            Gate_Action_i(ID=gate_aid, Output_flow=gate_output_flow.fid, Activity=self.anum, Domain=self.domain)
        ])

        # Populate each input flow
        for f in self.input_flows:
            Relvar.insert(db=mmdb, tr=tr_Gate, relvar='Gate Input', tuples=[
                Gate_Input_i(Gate_action=gate_aid, Input_flow=f.fid, Activity=self.anum, Domain=self.domain)
            ])

        Transaction.execute(db=mmdb, name=tr_Gate)

        pass
        # TODO: Rename the input flows
        for f in self.input_flows:
            source_aid_num = self.activity.labeled_outputs[f.fid][4:]
            new_label = f'_{source_aid_num}_{self.output_flow_label}'
            Flow.relabel_flow(new_label=new_label, fid=f.fid, anum=self.anum, domain=self.domain)

        return gate_aid, gate_output_flow
