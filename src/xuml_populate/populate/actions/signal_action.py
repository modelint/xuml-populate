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
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import (Flow_ap, MaxMult, Content, StateActivityAP,
                                                         Boundary_Actions, SMType)
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import (Signal_Action_i, Supplied_Parameter_Value_i,
                                               Signal_Instance_Set_Action_i,
                                               Delivery_Time_i, Absolute_Delivery_Time_i, Relative_Delivery_Time_i,
                                               Multiple_Assigner_Partition_Instance_i, Signal_Assigner_Action_i)

_logger = logging.getLogger(__name__)

# Transactions
tr_Signal = "Signal Action"

class SignalAction:
    """
    Create all relations for a Signal Action.
    """
    # TODO: Implement other Signal Action subclasses
    def __init__(self, statement_parse: Signal_a, activity_data: StateActivityAP):
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
        Returns:
            Boundary_Actions: The signal action id is both the initial and final action id
        """
        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Signal)
        self.action_id = Action.populate(tr=tr_Signal, anum=self.activity_data.anum, domain=self.activity_data.domain,
                                         action_type="signal")  # Transaction open

        # Extract the destination info from the parse
        signal_dest = self.statement_parse.dest

        # For now we handle two possible types of destination, a lifecycle or an assigner state machine
        dest_sm = None  # Destination state machine to find the target Event Specification
        if signal_dest.target_iset:
            # An instance set destination was specified, so a signal will be sent to each instance lifecycle
            # state machine in the set
            dest_flow = None
            iset_type = type(signal_dest.target_iset).__name__
            match iset_type:
                case 'N_a':
                    dest_name = signal_dest.target_iset.name
                    if dest_name == 'me':
                        if self.activity_data.xiflow:
                            dest_flow = self.activity_data.xiflow
                        dest_sm = self.activity_data.xiflow.tname  # The Event Spec is defined on my own state model
                    else:
                        pass  # TODO: Destination is some other state model
                case 'IN_a':
                    pass  # It is an input parameter
                case 'INST_a':
                    iset = InstanceSet(input_instance_flow=self.activity_data.xiflow,
                                       iset_components=signal_dest.target_iset.components,
                                       activity_data=self.activity_data)
                    _, _, dest_flow = iset.process()
                    dest_sm = dest_flow.tname
                case _:
                    pass  # Includes case where a more complex instance set expression is supplied

            Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Instance Set Action', tuples=[
                Signal_Instance_Set_Action_i(ID=self.action_id, Activity=self.activity_data.anum,
                                             Domain=self.activity_data.domain, Instance_flow=dest_flow.fid)
            ])
        elif signal_dest.assigner_dest:
            dest_sm = signal_dest.assigner_dest.rnum.rnum  # The signal destination state model name
            pi_flow = None
            # The signal will be addressed to an assigner state machine associated with a target association
            # Verify that the rnum is in fact an association (not an ordinal or a generalization relationship)

            # It's a safe assumption that we're signaling an assigner from a lifecycle state machine or a method
            # So we should have an xi flow
            if not self.activity_data.xiflow:
                pass  # TODO: Handle case where an assigner is sending a signal to another assigner

            iset = InstanceSet(input_instance_flow=self.activity_data.xiflow,
                               iset_components=signal_dest.assigner_dest.partition.components,
                               activity_data=self.activity_data)
            _, _, f = iset.process()

            Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Assigner Action', tuples=[
                Signal_Assigner_Action_i(ID=self.action_id, Activity=self.activity_data.anum,
                                         Domain=self.activity_data.domain,
                                         Association=dest_sm)
            ])
            Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Multiple Assigner Partition Instance', tuples=[
                Multiple_Assigner_Partition_Instance_i(Action=self.action_id, Activity=self.activity_data.anum,
                                                       Domain=self.activity_data.domain,
                                                       Partition=f.fid)
            ])
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Action', tuples=[
            Signal_Action_i(ID=self.action_id, Activity=self.activity_data.anum, Domain=self.activity_data.domain,
                            Event_spec=self.statement_parse.event, State_model=dest_sm)
        ])


        if self.statement_parse.supplied_params:
            # TODO: Populate Supplied Parameter Value instances for each
            pass
        if self.statement_parse.dest.delay != 0:
            # TODO: Populate Delivery Time
            pass

        Transaction.execute(db=mmdb, name=tr_Signal)
        return Boundary_Actions(ain={self.action_id}, aout={self.action_id})
