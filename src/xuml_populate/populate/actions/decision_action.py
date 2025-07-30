"""
decision_action.py – Populate a decision action instance in PyRAL
"""

# System
import logging
from typing import Sequence, Tuple, Optional

# Model Integration
from scrall.parse.visitor import Decision_a
from pyral.relvar import Relvar
from pyral.transaction import Transaction

# xUML populate
from xuml_populate.utility import print_mmdb
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import (Flow_ap, MaxMult, Content, ActivityAP,
                                                         Boundary_Actions, SMType)
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import (Result_i, Decision_Input_i, Decision_Action_i, Control_Dependency_i)

_logger = logging.getLogger(__name__)

# Transactions
tr_Decision = "Decision Action"

class DecisionAction:
    """
    Create all relations for a Decision Action.
    """
    # TODO: Implement other Signal Action subclasses
    def __init__(self, statement_parse: Decision_a, activity_data: ActivityAP):
        """
        Initialize with everything the Signal statement requires

        Args:
            statement_parse: Parsed representation of the Signal statement
            activity_data: Collected info about the activity
        """
        self.action_id = None
        self.statement_parse = statement_parse
        self.activity_data = activity_data

    def process(self) -> Boundary_Actions:
        """
        Returns:
            Boundary_Actions: The signal action id is both the initial and final action id
        """
        # Process the input to the transaction to obtain an input data flow
        # This can be any kind of data, but during Model Execution, the flowing value must resolve to true or false
        # For example, an instance flow with zero instances would be false
        # A scalar 0 would be false with any other value interpreted as true
        # And relation flow is false if it contains zero tuples, otherwise true

        decision_input = self.statement_parse.input  # Expression to be evaluated as true or false during execution

        decision_input_type = type(decision_input).__name__
        match decision_input_type:
            case 'INST_PROJ_a':
                # We need to evaluate an instance set and a possible projection
                iset = InstanceSet(input_instance_flow=self.activity_data.xiflow,
                                   iset_components=decision_input.iset.components, activity_data=self.activity_data)
                _, _, decision_input_flow = iset.process()
                pass
            case _:
                pass



        Transaction.open(db=mmdb, name=tr_Decision)
        pass
