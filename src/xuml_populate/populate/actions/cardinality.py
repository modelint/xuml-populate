"""
cardinality.py – Process Cardinality (Action)
"""
# System
import logging
from typing import Optional
from collections import namedtuple

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.action import Action
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import Flow_ap
from xuml_populate.populate.mmclass_nt import Cardinality_Action_i, Relational_Action_i, Scalar_i, Type_i

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

tr_Card = "Cardinality Action"
tr_Scalar = "Scalar"
CARD_TYPE = "Posint"

class CardinalityAction:
    """
    Populate a Cardinality Action
    """

    def __init__(self, anum: str, domain: str, ns_flow: Flow_ap):
        """
        Gather data required to populate the action

        Args:
            anum:  The method's activity number
            domain: The name of the domain
            ns_flow:  A non scalar input flow whose tuples will be counted
        """
        self.anum = anum
        self.domain = domain
        self.ns_flow = ns_flow  # We count the tuples or instances in this flow

    def populate(self) -> tuple[str, Flow_ap]:
        """
        Populate the action

        Returns:
            This action id and the Scalar output cardinality flow
        """
        # Verify that the Posint Scalar is defined
        R = f"Name:<{CARD_TYPE}>, Domain:<{self.domain}>"
        scalar_r = Relation.restrict(db=mmdb, relation="Scalar", restriction=R)
        if not scalar_r.body:
            # Insert the Scalar
            Transaction.open(db=mmdb, name=tr_Scalar)
            Relvar.insert(db=mmdb, tr=tr_Scalar, relvar="Scalar", tuples=[Scalar_i(Name=CARD_TYPE, Domain=self.domain)])
            Relvar.insert(db=mmdb, tr=tr_Scalar, relvar="Type", tuples=[Type_i(Name=CARD_TYPE, Domain=self.domain)])
            Transaction.execute(db=mmdb, name=tr_Scalar)

        # Open transaction to populate the Cardinality Action
        Transaction.open(db=mmdb, name=tr_Card)

        # Populate the action superclass and obtain our action id
        action_id = Action.populate(tr=tr_Card, anum=self.anum, domain=self.domain, action_type="cardinality action")

        # Populate the output cardinality scalar flow
        sflow_out = Flow.populate_scalar_flow(scalar_type="Posint", anum=self.anum,
                                              domain=self.domain, activity_tr=tr_Card)

        # Insert the Cardinality Action
        Relvar.insert(db=mmdb, tr=tr_Card, relvar='Cardinality Action', tuples=[
            Cardinality_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain,
                                 Non_scalar_input_flow=self.ns_flow.fid,
                                 Output_cardinality_flow=sflow_out.fid)
        ])

        Relvar.insert(db=mmdb, tr=tr_Card, relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain)
        ])
        Transaction.execute(db=mmdb, name=tr_Card)
        return action_id, sflow_out
