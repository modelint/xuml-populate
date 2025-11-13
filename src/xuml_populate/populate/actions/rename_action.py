"""
rename_action.py – Populate a selection action instance in PyRAL
"""
# System
import logging
from typing import TYPE_CHECKING

# Model Integration
from pyral.relvar import Relvar
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.ns_flow import NonScalarFlow
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mmclass_nt import Relational_Action_i, Table_Action_i, Rename_Action_i

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

# Transactions
tr_Rename = "Rename Action"

class RenameAction:
    """
    Populate a Rename Action
    """

    def __init__(self, input_nsflow: Flow_ap, from_attr: str, to_attr: str, activity: 'Activity'):
        """
        Gather data to populate a Rename Action

        Args:
            input_nsflow:  Non scalar flow with attribute to be renamed
            from_attr: Rename this attribute
            to_attr: New name for attribute
            activity: Enclosing Activity object
        """
        self.input_nsflow = input_nsflow
        self.activity = activity
        self.anum = activity.anum
        self.domain = activity.domain

        self.from_attr = from_attr
        self.to_attr = to_attr

    def populate(self) -> tuple[str, Flow_ap]:
        """
        Populate a Rename Action

        Returns:
            Rename Action ID and renamed output Table Flow
        """

        # Get header for the input flow
        table_header = NonScalarFlow.header(ns_flow=self.input_nsflow, domain=self.domain)
        # Rename the from attr keeping the same scalar
        from_scalar = table_header[self.from_attr]
        del table_header[self.from_attr]
        table_header[self.to_attr] = from_scalar
        # Create output table flow
        output_tflow = Flow.populate_relation_flow_by_header(table_header=table_header, anum=self.anum,
                                                             domain=self.domain, max_mult=self.input_nsflow.max_mult)
        # Populate the Action
        Transaction.open(db=mmdb, name=tr_Rename)
        action_id = Action.populate(tr=tr_Rename, anum=self.anum, domain=self.domain, action_type="rename")
        Relvar.insert(db=mmdb, tr=tr_Rename, relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Rename, relvar='Table_Action', tuples=[
            Table_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain, Input_a_flow=self.input_nsflow.fid,
                           Output_flow=output_tflow.fid)
        ])
        Relvar.insert(db=mmdb, tr=tr_Rename, relvar='Rename_Action', tuples=[
            Rename_Action_i(
                ID=action_id, Activity=self.anum, Domain=self.domain,
                From_attribute=self.from_attr, From_non_scalar_type=self.input_nsflow.tname,
                To_attribute=self.to_attr, To_table=output_tflow.tname)
        ])
        Transaction.execute(db=mmdb, name=tr_Rename)

        return action_id, output_tflow
