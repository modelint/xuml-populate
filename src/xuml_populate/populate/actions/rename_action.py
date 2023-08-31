"""
rename_action.py – Populate a selection action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.actions.table import Table
from xuml_populate.populate.ns_flow import NonScalarFlow
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mmclass_nt import Relational_Action_i, Table_Action_i, Rename_Action_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class RenameAction:
    """
    Create all relations for a Select Statement
    """

    input_instance_flow = None  # We are selecting instances from this instance flow
    output_instance_flow = None
    anum = None
    expression = None
    comparison_criteria = []
    equivalence_criteria = []
    restriction_text = ""
    cardinality = None
    action_id = None
    domain = None  # in this domain
    mmdb = None  # The database
    criterion_ctr = 0
    activity_path = None
    scrall_text = None
    max_mult = None

    @classmethod
    def populate(cls, mmdb: 'Tk', input_nsflow: Flow_ap, from_attr: str, to_attr: str,
                 anum: str, domain: str, activity_path: str, scrall_text: str) -> Flow_ap:
        """

        :param mmdb:
        :param input_nsflow:
        :param from_attr:
        :param to_attr:
        :param anum:
        :param domain:
        :param activity_path:
        :param scrall_text:
        :return:
        """
        # Get header for the input flow
        table_header = NonScalarFlow.header(mmdb, ns_flow=input_nsflow, domain=domain)
        # Rename the from attr keeping the same scalar
        from_scalar = table_header[from_attr]
        del table_header[from_attr]
        table_header[to_attr] = from_scalar
        # Create output table flow
        output_tflow = Table.populate(mmdb, table_header=table_header, maxmult=input_nsflow.max_mult,
                                      anum=anum, domain=domain)

        # Create the action (trannsaction open)
        cls.action_id = Action.populate(mmdb, anum, domain)
        Relvar.insert(relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=cls.action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(relvar='Table_Action', tuples=[
            Table_Action_i(ID=cls.action_id, Activity=anum, Domain=domain, Input_a_flow=input_nsflow.fid,
                           Output_flow=output_tflow.fid)
        ])
        Relvar.insert(relvar='Rename_Action', tuples=[
            Rename_Action_i(ID=cls.action_id, Activity=anum, Domain=domain, From_attribute=from_attr,
                            From_non_scalar_type=input_nsflow.tname, To_attribute=to_attr, To_table=output_tflow.tname)
        ])
        Transaction.execute()
        return output_tflow
