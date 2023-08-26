"""
table_assignment.py – Populate elements of a table assignment
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from xuml_populate.populate.mmclass_nt import Labeled_Flow_i
from xuml_populate.populate.actions.expressions.table_expr import TableExpr
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content

from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

from collections import namedtuple

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class TableAssignment:
    """
    Break down a table assignment statement into action semantics and populate them

    """

    input_instance_flow = None  # The instance flow feeding the next component on the RHS
    input_instance_ctype = None  # The class type of the input instance flow
    domain = None
    anum = None
    mmdb = None
    activity_path = None
    scrall_text = None

    @classmethod
    def process(cls, mmdb: 'Tk', anum: str, cname: str, domain: str, table_assign_parse,
                xi_flow_id: str, activity_path: str, scrall_text: str):
        """
        Given a parsed table assignment consisting of an LHS and an RHS, populate each component action
        and return the resultant table flow

        We'll need an initial flow and we'll need to create intermediate instance flows to connect the components.
        The final output flow must be a table flow. The associated Table determines the type of the
        assignment. If the LHS spcifies an explicit Table, the resultant Table which must match.

        :param mmdb: The metamodel db
        :param cname: The class (for an operation it is the proxy class)
        :param domain: In this domain
        :param anum: The Activity Number
        :param table_assign_parse: A parsed instance assignment
        :param xi_flow_id: The ID of the executing instance flow (the instance executing this activity)
        :param activity_path: Human readable path to the activity for error reporting
        :param scrall_text: The parsed scrall text for error reporting
        """
        lhs = table_assign_parse.lhs
        rhs = table_assign_parse.rhs
        cls.input_instance_flow = xi_flow_id

        # The executing instance is by nature a single instance flow
        xi_instance_flow = Flow_ap(fid=xi_flow_id, content=Content.INSTANCE, tname=cname, max_mult=MaxMult.ONE)

        output_flow = TableExpr.process(mmdb, rhs=rhs, anum=anum,
                                        input_instance_flow=xi_instance_flow, domain=domain,
                                        activity_path=activity_path, scrall_text=scrall_text)

        output_flow_label = lhs
        # TODO: handle case where lhs is an explicit table assignment

        # Migrate the output_flow to a labeled flow
        _logger.info(f"Labeling output of table expression to [{lhs}]")
        Transaction.open(mmdb)
        # Delete the Unlabeled flow
        Relvar.deleteone(mmdb, "Unlabeled_Flow",
                         tid={"ID": output_flow.fid, "Activity": anum, "Domain": domain}, defer=True)
        # Insert the labeled flow
        Relvar.insert(relvar='Labeled_Flow', tuples=[
            Labeled_Flow_i(ID=output_flow.fid, Activity=anum, Domain=domain, Name=output_flow_label)
        ])
        Transaction.execute()
