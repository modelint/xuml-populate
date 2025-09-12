"""
pass_action.py – Populate a pass action instance in PyRAL
"""

# System
import logging
from typing import Sequence, TYPE_CHECKING

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
from xuml_populate.populate.mmclass_nt import Pass_Action_i, Instance_Action_i, Flow_Connector_i

_logger = logging.getLogger(__name__)

# Transactions
tr_Pass = "Pass Action"

class PassAction:
    """
    Populate a Pass Action
    """

    def __init__(self, input_flow: str, output_flow_label: str, activity: 'Activity'):
        """
        Collect the data necessary to populate a Pass Action

        Args:
            input_flow: The id of an existing Data Flow
            output_flow_label: The name of the passed output flow to be created
            activity: The enclosing Activity
        """
        self.input_flow = input_flow
        self.output_flow_label = output_flow_label

        self.anum = activity.anum
        self.domain = activity.domain
        self.activity = activity

        self.action_id = None

    def populate(self) -> tuple[str, Flow_ap]:
        """
        Populate the Pass Action

        Returns:
            A tuple with the action id and output Data Flow
        """
        Transaction.open(db=mmdb, name=tr_Pass)
        pass_output_flow = Flow.copy_data_flow(tr=tr_Pass, ref_fid=self.input_flow,
                                               ref_anum=self.anum, new_anum=self.anum, domain=self.domain,
                                               label=self.output_flow_label)

        pass_aid = Action.populate(tr=tr_Pass, anum=self.anum, domain=self.domain, action_type="pass")

        Relvar.insert(db=mmdb, tr=tr_Pass, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=pass_aid, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Pass, relvar='Flow Connector', tuples=[
            Flow_Connector_i(ID=pass_aid, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Pass, relvar='Pass Action', tuples=[
            Pass_Action_i(ID=pass_aid, Activity=self.anum, Domain=self.domain, Input_flow=self.input_flow,
                          Output_flow=pass_output_flow.fid)
        ])
        Transaction.execute(db=mmdb, name=tr_Pass)
        return pass_aid, pass_output_flow
