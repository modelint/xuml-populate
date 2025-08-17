"""
read_action.py – Populate a read action instance in PyRAL
"""

# System
import logging
from typing import Set, List, Tuple

# Model Integration
from scrall.parse.visitor import Projection_a
from pyral.relvar import Relvar
from pyral.transaction import Transaction

# xUML populate
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, ActivityAP
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Read_Action_i, Attribute_Read_Access_i, Instance_Action_i

_logger = logging.getLogger(__name__)

# Transactions
tr_Read = "Read Action"

class ReadAction:
    """
    Populate a Read Action
    """

    def __init__(self, input_single_instance_flow: Flow_ap, attrs: Tuple[str], anum: str, domain: str):
        """
        Collect all data required to populate a Read Action

        Args:
            input_single_instance_flow: The summary of the input flow to the Read Action
            attrs: A tuple of attribute names to read
            anum: The activity number
            domain: The domain name
        """
        assert input_single_instance_flow.content == Content.INSTANCE
        assert input_single_instance_flow.max_mult == MaxMult.ONE

        self.input_instance_flow = input_single_instance_flow
        self.source_class = input_single_instance_flow.tname
        self.attrs = attrs
        self.anum = anum
        self.domain = domain
        self.action_id = None

    def populate(self) -> tuple[str, Tuple[Flow_ap]]:
        """
        Populate the Read Action

        Returns:
            A tuple of scalar flows matching the order of the specified attrs
        """
        # Get the class header
        class_attrs = MMclass.header(cname=self.source_class, domain=self.domain)

        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Read)
        self.action_id = Action.populate(tr=tr_Read, anum=self.anum, domain=self.domain, action_type="read")
        Relvar.insert(db=mmdb, tr=tr_Read, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Read, relvar='Read Action', tuples=[
            Read_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                          Instance_flow=self.input_instance_flow.fid)
        ])
        scalar_flows = []
        for a in self.attrs:
            of = Flow.populate_scalar_flow(scalar_type=class_attrs[a], anum=self.anum, domain=self.domain, label=None)
            Relvar.insert(db=mmdb, tr=tr_Read, relvar='Attribute_Read_Access', tuples=[
                Attribute_Read_Access_i(Attribute=a, Class=self.source_class, Read_action=self.action_id,
                                        Activity=self.anum, Domain=self.domain, Output_flow=of.fid)
            ])
            scalar_flows.append(of)

            # output_flows[pa] = of
        Transaction.execute(db=mmdb, name=tr_Read)
        return self.action_id, tuple(scalar_flows)
