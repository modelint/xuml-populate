"""
identifier_projection.py – Attempt to populate an identifier projection
"""

# System
import logging
from typing import TYPE_CHECKING, Optional
from collections import namedtuple

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Identifier_Projection_i, Flow_Connector_i, Instance_Action_i

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

# Transactions
tr_ID_Project = "Identifier Projection"

class IdentifierProjection:
    """
    We populate an Identifier Projection if a subset of the supplied Table Attributes matches the identifier
    of the specified Class.

    An additional constraint, checked during model execution, is that the corresponding Relation Flow
    must be a subset of the target Class population.

    See the Identifier Projection class and relationship descriptions for more details.
    """
    def __init__(self, relation_flow: Flow_ap, class_name: str, activity: 'Activity'):
        """
        Collect the data necessary to populate an Identifier Projection action

        Args:
            relation_flow: A Relation Flow
            class_name: We're attempting to cast the relation to an instance flow from this Class
            activity: The enclosing Activity object
        """
        self.relation_flow = relation_flow
        self.class_name = class_name

        self.anum = activity.anum
        self.domain = activity.domain
        self.activity = activity

        self.action_id = None

    def populate(self) -> Optional[tuple[str, Flow_ap]]:
        """
        Populate the Identifier Project Action

        Returns:
            The action id and output Instance Flow
        """
        pass
        #
        # Transaction.open(db=mmdb, name=tr_ID_Project)
        # aid = Action.populate(tr=tr_ID_Project, anum=self.anum, domain=self.domain, action_type="idproject")
        #
        #
        # Relvar.insert(db=mmdb, tr=tr_ID_Project, relvar='Instance Action', tuples=[
        #     Instance_Action_i(ID=aid, Activity=self.anum, Domain=self.domain)
        # ])
        # Relvar.insert(db=mmdb, tr=tr_ID_Project, relvar='Flow Connector', tuples=[
        #     Flow_Connector_i(ID=aid, Activity=self.anum, Domain=self.domain)
        # ])
        # # Relvar.insert(db=mmdb, tr=tr_ID_Project, relvar='Pass Action', tuples=[
        # #     Pass_Action_i(ID=aid, Activity=self.anum, Domain=self.domain, Input_flow=self.input_fid,
        # #                   Output_flow=pass_output_flow.fid)
        # # ])
        # Transaction.execute(db=mmdb, name=tr_ID_Project)
        #
        #
        # return aid, iflow
