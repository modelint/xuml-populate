"""
signal_action.py – Populate a signal action instance in PyRAL
"""

# System
import logging
from typing import Sequence, Tuple, Optional

# Model Integration
from scrall.parse.visitor import Signal_a
from pyral.relvar import Relvar
from pyral.transaction import Transaction

# xUML populate
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, ActivityAP, Boundary_Actions
from xuml_populate.populate.actions.action import Action
from xuml_populate.pop_types import SMType
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import (Signal_Action_i, Supplied_Parameter_Value_i,
                                               Signal_Instance_Set_Action_i,
                                               Delivery_Time_i, Absolute_Delivery_Time_i, Relative_Delivery_Time_i)

_logger = logging.getLogger(__name__)

# Transactions
tr_Signal = "Signal Action"

class SignalAction:
    """
    Create all relations for a Signal Action.  For now we assume that the signal is a Signal Instance Set Action.
    We'll implement the other subclasses of Signal Action later.
    """
    # TODO: Implement other Signal Action subclasses
    def __init__(self, statement_parse: Signal_a, activity_data: ActivityAP):
        """
        Initialize with everything the Signal statement requires

        Args:
            statement_parse: Parsed representation of the Signal statement
            activity_data: Collected info about the activity
        """
        self.action_id = None
        self.statement_parse = statement_parse
        self.activity_data = activity_data

        self.dest_iflow = None
        self.parameter_values = None
        self.delay_sflow = None

    def process(self) -> Boundary_Actions:
        """
        Initialize with everything the Signal statement requires
        Returns:
            Boundary_Actions: The signal action id is both the initial and final action id
        """
        dest_name = self.statement_parse.dest.target_iset.name
        if dest_name == 'me':
            if self.activity_data.xiflow:
                dest_flow = Flow_ap(fid=self.activity_data.xiflow, content=Content.INSTANCE,
                                    tname=self.activity_data.state_model, max_mult=MaxMult.ONE)
            else:
                dest_flow = None  # TODO: Handle SA, MA assigner 'me' destination cases
        else:
            pass  # TODO: Process an instance set

        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Signal)
        self.action_id = Action.populate(tr=tr_Signal, anum=self.activity_data.anum, domain=self.activity_data.domain,
                                         action_type="signal")  # Transaction open
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Action', tuples=[
            Signal_Action_i(Action=self.action_id, Activity=self.activity_data.anum, Domain=self.activity_data.domain,
                            Event_spec=self.statement_parse.event, State_model=self.activity_data.state_model)
        ])
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Instance Set Action', tuples=[
            Signal_Instance_Set_Action_i(Action=self.action_id, Activity=self.activity_data.anum,
                                         Domain=self.activity_data.domain, Instance_flow=dest_flow.fid)
        ])
        if self.statement_parse.supplied_params:
            # TODO: Populate Supplied Parameter Value instances for each
            pass
        if self.statement_parse.dest.delay != 0:
            # TODO: Populate Delivery Time
            pass
        Transaction.execute(db=mmdb, name=tr_Signal)
        return Boundary_Actions(ain={self.action_id}, aout={self.action_id})
