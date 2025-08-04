"""
delete_action.py – Populate a delete action in PyRAL
"""

# System
import logging
from typing import Any

# Model Integration
from pyral.relation import Relation
from pyral.relvar import Relvar
from pyral.transaction import Transaction
from scrall.parse.visitor import INST_a

# xUML populate
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions
from xuml_populate.populate.actions.action import Action
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.mmclass_nt import Delete_Action_i
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet

_logger = logging.getLogger(__name__)

# Transactions
tr_Delete = "Delete Action"

class DeleteAction:
    """
    Create all relations for a Delete Action.
    """
    def __init__(self, iset_parse: INST_a, activity_data: ActivityAP):
        """
        Initialize with everything the Signal statement requires

        Args:
            statement_parse: Parsed representation of the New Instance expression
            activity_data: Collected info about the activity
        """
        self.action_id = None
        self.activity_data = activity_data
        self.iset_parse = iset_parse

        # Convenience
        self.anum = self.activity_data.anum
        self.domain = self.activity_data.domain

    def process(self) -> Boundary_Actions:
        """

        Returns:
            Boundary_Actions: The signal action id is both the initial and final action id
        """
        # Begin by populating the Action itself
        # Populate the Action superclass instance and obtain an action_id
        Transaction.open(db=mmdb, name=tr_Delete)
        self.action_id = Action.populate(tr=tr_Delete, anum=self.activity_data.anum, domain=self.activity_data.domain,
                                         action_type="delete")  # Transaction open
        # Process the input flow of instances to delete
        iset = InstanceSet(input_instance_flow=self.activity_data.xiflow,
                           iset_components=self.iset_parse.components, activity_data=self.activity_data)
        ain, aout, i_flow = iset.process()

        Relvar.insert(db=mmdb, tr=tr_Delete, relvar='Delete Action', tuples=[
            Delete_Action_i(ID=self.action_id, Activity=self.activity_data.anum, Domain=self.activity_data.domain,
                            Flow=i_flow.fid)
        ])

        Transaction.execute(db=mmdb, name=tr_Delete)

        return Boundary_Actions(ain={ain}, aout={self.action_id})
