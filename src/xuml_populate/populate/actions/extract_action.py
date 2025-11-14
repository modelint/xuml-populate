"""
extract_action.py – Populate an Extract Action instance in PyRAL
"""
# System
import logging
from typing import Set, Dict, List, Optional, TYPE_CHECKING

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.table import Table
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.exceptions.action_exceptions import (ProductForbidsCommonAttributes, UnjoinableHeaders,
                                                        SetOpRequiresSameHeaders)
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.ns_flow import NonScalarFlow
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Relational_Action_i, Extract_Action_i
from xuml_populate.exceptions.action_exceptions import *

_logger = logging.getLogger(__name__)

# Transactions
tr_Extract = "Extract Action"

class ExtractAction:
    """
    Create all relations for an Extract Action
    """
    def __init__(self, tuple_flow: Flow_ap, attr: str, activity: 'Activity', label: str = None):
        """
        Populate the Extract Action

        Args:
            tuple_flow: The input Non Scalar Flow
            attr: Name of attribute to extract
            activity: The enclosing Activity object
            label:  Name (label) of the output Scalar Flow
        """
        # Verify that we have an input Tuple Flow
        if tuple_flow.max_mult != MaxMult.ONE or tuple_flow.content != Content.RELATION:
            msg = (f"Cannot extract attribute values from non-tuple flow: {tuple_flow} "
                   f"at {activity.activity_path}")
            _logger.error(msg)
            raise ActionException(msg)

        self.anum = activity.anum
        self.domain = activity.domain
        self.activity = activity

        self.attr = attr
        self.tuple_flow = tuple_flow
        self.tuple_header = NonScalarFlow.header(ns_flow=tuple_flow, domain=activity.domain)
        self.label = label

    def populate(self) -> tuple[str, Flow_ap]:
        """
        Populate the Extract Action

        Returns:
            Action ID and the output scalar flow with the extracted attribute value
        """
        Transaction.open(db=mmdb, name=tr_Extract)
        action_id = Action.populate(tr=tr_Extract, anum=self.anum, domain=self.domain, action_type="extract")

        # Create the labeled Scalar Flow
        output_sflow = Flow.populate_scalar_flow(
            label=self.label, scalar_type=self.tuple_header[self.attr],
            anum=self.anum, domain=self.domain
        )

        Relvar.insert(db=mmdb, tr=tr_Extract, relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Extract, relvar='Extract_Action', tuples=[
            Extract_Action_i(ID=action_id, Activity=self.anum, Domain=self.domain, Input_tuple=self.tuple_flow.fid,
                             Table=self.tuple_flow.tname, Attribute=self.attr, Output_scalar=output_sflow.fid)
        ])
        Transaction.execute(db=mmdb, name=tr_Extract)

        return action_id, output_sflow
