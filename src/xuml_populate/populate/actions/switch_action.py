"""
switch_action.py – Populate a switch action instance in PyRAL
"""

import logging
from typing import List
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mm_class import MMclass
from scrall.parse.visitor import Projection_a
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Read_Action_i, Attribute_Read_Access_i
from pyral.relvar import Relvar
from pyral.transaction import Transaction

_logger = logging.getLogger(__name__)

# Transactions
tr_Switch = "Switch Action"

class SwitchAction:
    """
    Create all relations for a Switch Action
    """

    input_instance_flow = None  # We are selecting instances from this instance flow
    output_instance_flow = None
    expression = None
    comparison_criteria = []
    equivalence_criteria = []
    restriction_text = ""
    cardinality = None
    action_id = None
    criterion_ctr = 0
    max_mult = None

    @classmethod
    def populate(cls, input_single_instance_flow: Flow_ap, projection: Projection_a,
                 activity_data: Activity_ap) -> (str, List[Flow_ap]):
        """
        Populate the Switch Action

        :param input_single_instance_flow: The source flow into this selection
        :param projection:
        :param input_single_instance_flow:
        :param activity_data:
        :return: A list of scalar flows in the order of the project statement
        """
        anum = activity_data.anum
        domain = activity_data.domain
        si_flow = input_single_instance_flow  # Short name for convenience

        # Get the class header
        class_attrs = MMclass.header(cname=si_flow.tname, domain=domain)

        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Switch)
        action_id = Action.populate(tr=tr_Switch, anum=anum, domain=domain, action_type="switch")  # Transaction open
        Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Read_Action', tuples=[
            Read_Action_i(ID=action_id, Activity=anum, Domain=domain, Instance_flow=input_single_instance_flow.fid)
        ])
        scalar_flows = []
        proj_attrs = [n.name for n in projection.attrs] if projection.expand != 'ALL' else list(class_attrs.keys())
        for pa in proj_attrs:
            of = Flow.populate_scalar_flow(scalar_type=class_attrs[pa], anum=anum, domain=domain, label=None)
            Relvar.insert(db=mmdb, tr=tr_Switch, relvar='Attribute_Read_Access', tuples=[
                Attribute_Read_Access_i(Attribute=pa, Class=si_flow.tname, Read_action=action_id, Activity=anum,
                                        Domain=domain, Output_flow=of.fid)
            ])
            scalar_flows.append(of)

            # output_flows[pa] = of
        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute(db=mmdb, name=tr_Switch)  # Select Action
        return action_id, scalar_flows
