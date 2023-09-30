"""
extract_action.py – Populate an Extract Action instance in PyRAL
"""

import logging
from xuml_populate.populate.actions.table import Table
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
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
    @classmethod
    def populate(cls, mmdb: 'Tk', tuple_flow: Flow_ap, attr: str, anum: str,
                 domain: str, activity_data: Activity_ap, label: str = None) -> Flow_ap:
        """
        Populate the Extract Action

        :param mmdb: The metamodel database
        :param tuple_flow: The input Non Scalar Flow
        :param attr: Name of attribute to extract
        :param anum: Activity number
        :param domain: Domain
        :param activity_data:
        :param label:  Name (label) of the output Scalar Flow
        :return: Set action scalar flow
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes

        tuple_header = NonScalarFlow.header(mmdb, tuple_flow, domain)

        # Create the action (trannsaction open)
        action_id = Action.populate(mmdb, anum, domain)

        # Create the labeled Scalar Flow
        sflow = Flow.populate_scalar_flow(mmdb, label=label, scalar_type=tuple_header[attr],
                                          activity=anum, domain=domain)

        Relvar.insert(relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(relvar='Extract_Action', tuples=[
            Extract_Action_i(ID=action_id, Activity=anum, Domain=domain, Input_tuple=tuple_flow.fid,
                             Table=tuple_flow.tname, Attribute=attr, Output_scalar=sflow.fid)
        ])
        Transaction.execute()
        return sflow
