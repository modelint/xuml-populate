"""
state_activity.py – Populates a State's activity
"""
# System
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from xuml_populate.populate.state_model import StateModel

# Model Integration
from pyral.transaction import Transaction
from pyral.relvar import Relvar
from pyral.relation import Relation  # For debugging
from scrall.parse.parser import ScrallParser

# xUML Populate
from xuml_populate.populate.xunit import ExecutionUnit
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import SMType
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.signature import Signature
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mmclass_nt import (Method_Signature_i, Method_i, Parameter_i)
from xuml_populate.populate.actions.aparse_types import ActivityAP, StateActivityAP

_logger = logging.getLogger(__name__)

# Transactions
tr_Method = "Method"
tr_Parameter = "Parameter"
tr_OutputFlow = "OutputFlow"


class StateActivity:
    """
    """
    def __init__(self, state_name: str, state_model: "StateModel", activity_data):
        """
        Populate a State's Activity

        Args:
            state_name: Name of the state
            activity_data:
        """
        self.domain = state_model.domain
        self.state_model = state_model
        self.sm_name = state_model.sm_name
        self.sm_type = state_model.sm_type
        self.name = state_name
        self.xi_flow = None
        self.signum = None
        self.anum = activity_data["anum"]
        self.xi_flow_id = None
        self.pi_flow_id = None
        self.pclass = None
        self.path = f"{self.domain}:{self.sm_name}:{self.name}.mtd"
        self.activity_detail = None
        self.parse = activity_data['parse']
        self.activity_data = activity_data
        # Maintain a dictionary of seq token control flow dependencies
        # seq_token_out_action: {seq_token_in_actions}
        self.seq_flows: dict[str, set[str]] = {}
        # seq_token: output_action_ids
        self.seq_tokens: dict[str, set[str]] = {}

        self.process_execution_units()


    def process_execution_units(self):
        pass

        _logger.info(f"Populating state activity execution units: {self.path}")
        # Look up signature
        R = f"State_model:<{self.sm_name}>, Domain:<{self.domain}>"
        result = Relation.restrict(db=mmdb, relation='State Signature', restriction=R)
        if not result.body:
            # TODO: raise exception here
            pass
        self.signum = result.body[0]['SIGnum']

        match self.sm_type:
            case SMType.LIFECYCLE:
                # Look up the executign instance (xi) flow
                R = f"Anum:<{self.anum}>, Domain:<{self.domain}>"
                lifecycle_activity_r = Relation.restrict(db=mmdb, relation='Lifecycle Activity', restriction=R)
                if not lifecycle_activity_r.body:
                    # TODO: raise exception here
                    pass
                self.xi_flow_id = lifecycle_activity_r.body[0]['Executing_instance_flow']
            case SMType.MA:
                # Look up the partitioning instance (pi) flow
                R = f"Anum:<{self.anum}>, Domain:<{self.domain}>"
                ma_activity_r = Relation.restrict(db=mmdb, relation='Multiple Assigner Activity', restriction=R)
                if not ma_activity_r.body:
                    # TODO: raise exception here
                    pass
                self.pi_flow_id = ma_activity_r.body[0]['Paritioning_instance_flow']
                R = f"Anum:<{self.anum}>, Domain:<{self.domain}>"
                ma_r = Relation.restrict(db=mmdb, relation='Multiple Assigner', restriction=R)
                if not result.body:
                    # TODO: raise exception here
                    pass
                self.pclass = ma_r.body[0]['Partitioning_class']
            case SMType.SA:
                pass  # No xi or pi flow (rnum only, no associated instance)

        activity_detail = StateActivityAP(anum=self.anum, domain=self.domain,
                                          sname=self.name, state_model=self.sm_name,
                                          smtype=self.sm_type, xiflow=self.xi_flow_id,
                                          piflow=self.pi_flow_id, pclass=self.pclass,
                                          activity_path=self.path, scrall_text=self.activity_data['text'])

        # Here we process each statement set in the State Activity
        for count, xunit in enumerate(self.parse):  # Use count for debugging
            c = count + 1
            boundary_actions = ExecutionUnit.process_method_statement_set(
                activity_data=activity_detail, statement_set=xunit.statement_set)
            in_tokens, out_token = xunit.statement_set.input_tokens, xunit.output_token
            if out_token:
                # The statement has set an output_token (it cannot set more than one)
                # Register the new out_token
                if out_token in self.seq_tokens:
                    pass  # TODO: raise exception -- token can ony be set by one statement
                self.seq_tokens[out_token] = set()
                for a in boundary_actions.aout:
                    # Each output_action is the source of a control dependency named by that output token
                    # Register the output token and the emitting action
                    self.seq_tokens[out_token].add(a)
                    self.seq_flows[a] = set()  # Set is filled when in_tokens are processed
            for tk in in_tokens:
                for a_upstream in self.seq_tokens[tk]:  # All upstream actions that set the token
                    for a_in in boundary_actions.ain:  # All initial actions in this statement
                        self.seq_flows[a_upstream].add(a_in)  # Add that initial action to the downstream value

        a = Activity(name=self.name, class_name=self.class_name, activity_data=self.activity_detail)
        a.pop_flow_dependencies()
        a.assign_waves()
        a.populate_waves()

