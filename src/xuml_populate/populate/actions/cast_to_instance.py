"""
cast_to_instance.py – Attempt to populate a Cast To Instance action
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
from xuml_populate.populate.mmclass_nt import Cast_To_Instance_i, Flow_Connector_i, Instance_Action_i

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

# Transactions
tr_CastToInstance = "Cast To Instance"

class CastToInstance:
    """
    We populate a Cast To Instance if a subset of the supplied Table Attributes matches the identifier
    of the specified Class.

    An additional constraint, checked during model execution, is that the corresponding Relation Flow
    must be a subset of the target Class population.

    See the Cast To Instance class and relationship descriptions for more details.
    """
    def __init__(self, relation_flow: Flow_ap, class_name: str, activity: 'Activity'):
        """
        Collect the data necessary to populate an Cast To Instance action

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
        Populate the Cast To Instance action

        Returns:
            The action id and output Instance Flow
        """
        # First check to see if the Relation Flow can be cast to an Instance Flow
        if not Flow.table_to_instance_compatible(
                class_name=self.class_name, table=self.relation_flow.tname, domain=self.domain):
            return None

        cast_iflow = Flow.populate_instance_flow(cname=self.class_name, anum=self.anum, domain=self.domain)

        Transaction.open(db=mmdb, name=tr_CastToInstance)
        aid = Action.populate(tr=tr_CastToInstance, anum=self.anum, domain=self.domain, action_type="cast to instance")

        Relvar.insert(db=mmdb, tr=tr_CastToInstance, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=aid, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_CastToInstance, relvar='Flow Connector', tuples=[
            Flow_Connector_i(ID=aid, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_CastToInstance, relvar='Cast To Instance', tuples=[
            Cast_To_Instance_i(ID=aid, Activity=self.anum, Domain=self.domain, Instance_flow=cast_iflow.fid,
                               Relation_flow=self.relation_flow.fid)
        ])
        Transaction.execute(db=mmdb, name=tr_CastToInstance)

        return aid, cast_iflow
