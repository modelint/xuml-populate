"""
update_ref_action.py – Populate an Update Reference Action
"""

# System
import logging
from typing import List, TYPE_CHECKING

# Model Integration
from scrall.parse.visitor import Update_ref_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.actions.aparse_types import Boundary_Actions
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.mmclass_nt import (
    Instance_Action_i, Reference_Action_i, Update_Reference_Action_i,
    From_Ref_Instance_i, To_Ref_Instance_i, Referenced_Instance_i
)

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

tr_Update = 'UpdateReferenceAction'

class UpdateReferenceAction:
    """

    """
    def __init__(self, activity: 'Activity', statement_parse: Update_ref_a):
        """
        """
        self.parse = statement_parse
        self.activity = activity
        self.anum = activity.anum
        self.domain = activity.domain

        self.rnum = statement_parse.to_ref.rnum
        self.action_id = None

        self.input_aids: set[str] = set()  # The boundary input actions
        pass

    def populate(self) -> Boundary_Actions:
        """

        Returns:
            Flow ID of a tuple of referential attribute values
        """
        Transaction.open(db=mmdb, name=tr_Update)
        self.action_id = Action.populate(tr=tr_Update, anum=self.activity.anum, domain=self.activity.domain,
                                         action_type="update ref")

        Relvar.insert(db=mmdb, tr=tr_Update, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        # TODO: Update mmdb to move R791 to New Reference Action, not needed for Update Reference
        Relvar.insert(db=mmdb, tr=tr_Update, relvar='Reference Action', tuples=[
            Reference_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                               Association=self.rnum)
        ])

        # Resolve the instance flow of the from side of the association (instance to be updated)
        if self.parse.iset == 'ME':
            from_ref_iflow = self.activity.xiflow
        else:
            ie = InstanceSet(iset_components=self.parse.iset.components, activity=self.activity,
                             input_instance_flow=self.activity.xiflow)
            ain, aout, from_ref_iflow = ie.process()
            self.input_aids.add(ain)

        # Resolve the instance flow of the instance to be referenced
        ie = InstanceSet(iset_components=self.parse.to_ref.iset.components, activity=self.activity,
                         input_instance_flow=self.activity.xiflow)
        ain, _, to_ref_iflow = ie.process()
        self.input_aids.add(ain)


        Relvar.insert(db=mmdb, tr=tr_Update, relvar='Update Reference Action', tuples=[
            Update_Reference_Action_i(
                ID=self.action_id, Activity=self.anum, Domain=self.domain,
                From_instance=from_ref_iflow.fid, To_instance=to_ref_iflow.fid
            )
        ])

        Relvar.insert(db=mmdb, tr=tr_Update, relvar='Referenced Instance', tuples=[
            Referenced_Instance_i(
                Flow=from_ref_iflow.fid, Activity=self.anum, Domain=self.domain
            )
        ])
        Relvar.insert(db=mmdb, tr=tr_Update, relvar='From Ref Instance', tuples=[
            Referenced_Instance_i(
                Flow=from_ref_iflow.fid, Activity=self.anum, Domain=self.domain
            )
        ])
        Relvar.insert(db=mmdb, tr=tr_Update, relvar='Referenced Instance', tuples=[
            Referenced_Instance_i(
                Flow=to_ref_iflow.fid, Activity=self.anum, Domain=self.domain
            )
        ])
        Relvar.insert(db=mmdb, tr=tr_Update, relvar='To Ref Instance', tuples=[
            Referenced_Instance_i(
                Flow=to_ref_iflow.fid, Activity=self.anum, Domain=self.domain
            )
        ])

        Transaction.execute(db=mmdb, name=tr_Update)

        return Boundary_Actions(ain=self.input_aids, aout={self.action_id})
