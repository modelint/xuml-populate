"""
state_activity.py – Populates a State's activity
"""
# System
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from xuml_populate.populate.state_model import StateModel

# Model Integration
from pyral.relation import Relation  # For debugging

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.utility import print_mmdb
from xuml_populate.populate.actions.aparse_types import SMType, Flow_ap, Content, MaxMult, Method_Output_Type
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.actions.aparse_types import StateActivityAP

_logger = logging.getLogger(__name__)

# Transactions
tr_Method = "Method"
tr_Parameter = "Parameter"
tr_OutputFlow = "OutputFlow"


class StateActivity:
    """
    """
    def __init__(self, state_name: str, state_model: "StateModel", state_parse,
                 method_output_types: dict[str, Method_Output_Type]):
        """
        Populate a State's Activity

        Args:
            state_name: Name of the state
            state_model: Name of the state model
            state_parse: The activity Scrall parse
            activity: The activity object
            method_output_types: A dictionary of output types for each method in the domain
        """
        self.domain = state_model.domain
        self.state_model = state_model
        self.sm_name = state_model.sm_name
        self.sm_type = state_model.sm_type
        self.name = state_name
        self.signum = None
        self.anum = state_parse["anum"]
        self.xi_flow_id = None
        self.xi_flow = None
        self.pi_flow_id = None
        self.pi_flow = None
        self.pclass = None
        self.path = f"{self.domain}:{self.sm_name}[{self.name}]"
        self.state_parse = state_parse

        self.process_execution_units(method_output_types=method_output_types)

    def process_execution_units(self, method_output_types: dict[str, Method_Output_Type]):
        """

        """
        _logger.info(f"Populating state activity execution units: {self.path}")
        # Look up signature
        R = f"Name:<{self.name}>, State_model:<{self.sm_name}>, Domain:<{self.domain}>"
        real_state_r = Relation.restrict(db=mmdb, relation='Real State', restriction=R)
        if not real_state_r.body:
            # TODO: raise exception here
            pass
        self.signum = real_state_r.body[0]['Signature']

        match self.sm_type:
            case SMType.LIFECYCLE:
                # Look up the executing instance (xi) flow
                R = f"Anum:<{self.anum}>, Domain:<{self.domain}>"
                lifecycle_activity_r = Relation.restrict(db=mmdb, relation='Lifecycle Activity', restriction=R)
                if not lifecycle_activity_r.body:
                    # TODO: raise exception here
                    pass
                self.xi_flow_id = lifecycle_activity_r.body[0]['Executing_instance_flow']
                self.xi_flow = Flow_ap(fid=self.xi_flow_id, content=Content.INSTANCE, tname=self.sm_name,
                                       max_mult=MaxMult.ONE)
            case SMType.MA:
                # Look up the partitioning instance (pi) flow
                R = f"Anum:<{self.anum}>, Domain:<{self.domain}>"
                ma_activity_r = Relation.restrict(db=mmdb, relation='Multiple Assigner Activity', restriction=R)
                if not ma_activity_r.body:
                    # TODO: raise exception here
                    pass
                self.pi_flow_id = ma_activity_r.body[0]['Partitioning_instance_flow']
                self.pi_flow = Flow_ap(fid=self.pi_flow_id, content=Content.INSTANCE, tname=self.state_model.pclass,
                                       max_mult=MaxMult.ONE)
                R = f"Rnum:<{self.sm_name}>, Domain:<{self.domain}>"
                ma_r = Relation.restrict(db=mmdb, relation='Multiple Assigner', restriction=R)
                if not ma_r.body:
                    # TODO: raise exception here
                    pass
                self.pclass = ma_r.body[0]['Partitioning_class']
            case SMType.SA:
                pass  # No xi or pi flow (rnum only, no associated instance)

        state_activity_data = StateActivityAP(
            anum=self.anum, domain=self.domain, signum=self.signum,
            sname=self.name, state_model=self.sm_name, smtype=self.sm_type,
            xiflow=self.xi_flow, piflow=self.pi_flow, domain_method_output_types=method_output_types,
            activity_path=self.path, parse=self.state_parse["parse"], scrall_text=self.state_parse['text'])

        # Populate the State Activity Actions
        activity_obj = Activity(activity_data=state_activity_data)
        activity_obj.pop_actions()
        activity_obj.prep_for_execution()
