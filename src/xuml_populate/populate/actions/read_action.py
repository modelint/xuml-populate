"""
read_action.py – Populate a read action instance in PyRAL
"""

import logging
from typing import Set, List, Tuple
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
tr_Read = "Read Action"

class ReadAction:
    """
    Create all relations for a Read Action
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
    def populate(cls, input_single_instance_flow: Flow_ap, attrs: Tuple[str],
                 anum: str, domain: str) -> (str, Tuple[Flow_ap]):
        """
        Populate the Read Action

        :param input_single_instance_flow: The summary of the input flow to the Read Action
        :param attrs: A tuple of attribute names to read
        :param anum:  The activity number
        :param domain:  The domain name
        :return: A tuple of scalar flows matching the order of the specified attrs
        """
        # TODO: Avoid populating duplicate for reading the same attr set by maintaining dict of action/flows
        # TODO: for the current activity. If duplicate found, return its action id and output flows instead.
        # TODO: Ensure that the existing read action that has no incoming control flows

        assert input_single_instance_flow.content == Content.INSTANCE
        assert input_single_instance_flow.max_mult == MaxMult.ONE
        cname = input_single_instance_flow.tname

        # Get the class header
        class_attrs = MMclass.header(cname=cname, domain=domain)

        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(mmdb, tr_Read)
        action_id = Action.populate(tr=tr_Read, anum=anum, domain=domain)  # Transaction open
        Relvar.insert(mmdb, tr=tr_Read, relvar='Read_Action', tuples=[
            Read_Action_i(ID=action_id, Activity=anum, Domain=domain, Instance_flow=input_single_instance_flow.fid)
        ])
        scalar_flows = []
        for a in attrs:
            of = Flow.populate_scalar_flow(scalar_type=class_attrs[a], anum=anum, domain=domain, label=None)
            Relvar.insert(mmdb, tr=tr_Read, relvar='Attribute_Read_Access', tuples=[
                Attribute_Read_Access_i(Attribute=a, Class=cname, Read_action=action_id, Activity=anum,
                                        Domain=domain, Output_flow=of.fid)
            ])
            scalar_flows.append(of)

            # output_flows[pa] = of
        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute(mmdb, tr_Read)  # Select Action
        return action_id, tuple(scalar_flows)
