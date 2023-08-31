"""
extract_action.py – Populate an Extract Action instance in PyRAL
"""

import logging
from xuml_populate.populate.actions.table import Table
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.exceptions.action_exceptions import (ProductForbidsCommonAttributes, UnjoinableHeaders,
                                                        SetOpRequiresSameHeaders)
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.ns_flow import NonScalarFlow
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Relational_Action_i, Extract_Action_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class ExtractAction:
    """
    Create all relations for an Extract Action
    """
    mmdb = None
    domain = None
    anum = None
    activity_path = None
    scrall_text = None
    action_id = None
    ns_type = None

    @classmethod
    def populate(cls, mmdb: 'Tk', tuple_flow: Flow_ap, attr: str, target_flow_name: str, anum: str,
                 domain: str, activity_path: str, scrall_text: str):
        """
        Populate the Extract Action

        :param mmdb: The metamodel database
        :param tuple_flow: The input Non Scalar Flow
        :param attr: Name of attribute to extract
        :param target_flow_name:  Name (label) of the output Scalar Flow
        :param anum: Activity number
        :param domain: Domain
        :param scrall_text:
        :param activity_path:
        :return: Set action output table flow
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        cls.mmdb = mmdb
        cls.domain = domain
        cls.anum = anum
        cls.activity_path = activity_path
        cls.scrall_text = scrall_text

        tuple_header = NonScalarFlow.header(mmdb, tuple_flow, domain)

        # Create the action (trannsaction open)
        cls.action_id = Action.populate(mmdb, anum, domain)

        # Create the labeled Scalar Flow
        sflow = Flow.populate_scalar_flow(mmdb, label=target_flow_name, scalar_type=tuple_header[attr],
                                          activity=anum, domain=domain)

        Relvar.insert(relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=cls.action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(relvar='Extract_Action', tuples=[
            Extract_Action_i(ID=cls.action_id, Activity=anum, Domain=domain, Input_tuple=tuple_flow.fid,
                             Table=tuple_flow.tname, Attribute=attr, Output_scalar=sflow.fid)
        ])
        Transaction.execute()

