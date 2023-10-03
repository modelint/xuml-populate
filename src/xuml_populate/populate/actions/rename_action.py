"""
rename_action.py – Populate a selection action instance in PyRAL
"""

import logging
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from xuml_populate.populate.actions.table import Table
from xuml_populate.populate.ns_flow import NonScalarFlow
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mmclass_nt import Relational_Action_i, Table_Action_i, Rename_Action_i
from pyral.relvar import Relvar
from pyral.transaction import Transaction

_logger = logging.getLogger(__name__)

# Transactions
tr_Rename = "Rename Action"

class RenameAction:
    """
    Create all relations for a Select Statement
    """

    @classmethod
    def populate(cls, input_nsflow: Flow_ap, from_attr: str, to_attr: str,
                 activity_data: Activity_ap ) -> (str, Flow_ap):
        """

        :param input_nsflow:
        :param from_attr:
        :param to_attr:
        :param activity_data:
        :return:
        """
        anum = activity_data.anum
        domain = activity_data.domain

        # Get header for the input flow
        table_header = NonScalarFlow.header(ns_flow=input_nsflow, domain=domain)
        # Rename the from attr keeping the same scalar
        from_scalar = table_header[from_attr]
        del table_header[from_attr]
        table_header[to_attr] = from_scalar
        # Create output table flow
        output_tflow = Table.populate(table_header=table_header, maxmult=input_nsflow.max_mult,
                                      anum=anum, domain=domain)

        # Create the action
        Transaction.open(mmdb, tr_Rename)
        action_id = Action.populate(mmdb, anum, domain)
        Relvar.insert(mmdb, tr=tr_Rename, relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(mmdb, tr=tr_Rename, relvar='Table_Action', tuples=[
            Table_Action_i(ID=action_id, Activity=anum, Domain=domain, Input_a_flow=input_nsflow.fid,
                           Output_flow=output_tflow.fid)
        ])
        Relvar.insert(mmdb, tr=tr_Rename, relvar='Rename_Action', tuples=[
            Rename_Action_i(ID=action_id, Activity=anum, Domain=domain, From_attribute=from_attr,
                            From_non_scalar_type=input_nsflow.tname, To_attribute=to_attr, To_table=output_tflow.tname)
        ])
        Transaction.execute(mmdb, tr_Rename)
        return action_id, output_tflow
