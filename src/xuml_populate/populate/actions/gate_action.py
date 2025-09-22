"""
gate_action.py – Populate a Gate Action instance
"""

# System
import logging
from typing import Sequence, TYPE_CHECKING
import re

# Model Integration
from pyral.relvar import Relvar
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

        return gate_aid, gate_output_flow
