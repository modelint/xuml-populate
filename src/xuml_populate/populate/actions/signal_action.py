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
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Signal

_logger = logging.getLogger(__name__)

# Transactions
tr_Signal = "Signal Action"

class SignalAction:
    """
    Create all relations for a Signal Action.  For now we assume that the signal is a Signal Instance Set Action.
    We'll implement the other subclasses of Signal Action later.
    """
    # TODO: Implement other Signal Action subclasses
    def __init__(self, statement_parse:Signal_a, activity_data: Activity_ap):
        """
        Initialize with everything the Signal statement requires

        Args:
            statement_parse: Parsed representation of the Signal statement
            activity_data: Collected info about the activity
        """
        self.statement_parse = statement_parse
        self.activity_data = activity_data

        self.dest_iflow = None
        self.parameter_values = None
        self.delay_sflow = None
        self.process()

    # def process(self, dest_iflow: Flow_ap, parameter_values: Optional[Sequence[Flow_ap]],
    #             delay_sflow: Optional[Flow_ap] = None):
    def process(self):
        """
        Initialize with everything the Signal statement requires

        Args:
            dest_iflow: A signal is delivered to each instance in this flow
            parameter_values: An optional sequence of Data Flows providing input for any parameters required by
             the event
            delay_sflow: A scalar value giving us either a duration or a specific point in time to deliver the signal
        """
        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Signal)
        action_id = Action.populate(tr=tr_Signal, anum=self.activity_data.anum, domain=self.activity_data.domain,
                                    action_type="signal")  # Transaction open
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Action', tuples=[
            Sign(Attribute=a, Class=cname, Read_action=action_id, Activity=anum,
                                    Domain=domain, Output_flow=of.fid)
        ])

        pass
        # self.dest_iflow = dest_iflow
        # self.parameter_values = [] if parameter_values is None else parameter_values
        # self.delay_sflow = delay_sflow

