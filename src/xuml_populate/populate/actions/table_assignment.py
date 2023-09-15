"""
table_assignment.py – Populate elements of a table assignment
"""

import logging
from typing import TYPE_CHECKING
from xuml_populate.populate.mmclass_nt import Labeled_Flow_i
from xuml_populate.populate.actions.expressions.table_expr import TableExpr
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap, Boundary_Actions
from scrall.parse.visitor import Table_Assignment_a

from pyral.relvar import Relvar
from pyral.transaction import Transaction

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
    def process(cls, mmdb: 'Tk', activity_data: Activity_ap, table_assign_parse: Table_Assignment_a
                ) -> Boundary_Actions:
        """
        Given a parsed table assignment consisting of an LHS and an RHS, populate each component action
        and return the resultant table flow

        We'll need an initial flow and we'll need to create intermediate instance flows to connect the components.
        The final output flow must be a table flow. The associated Table determines the type of the
        assignment. If the LHS spcifies an explicit Table, the resultant Table which must match.

        :param mmdb: The metamodel db
        :param activity_data:
        :param table_assign_parse: A parsed table assignment
        """
        lhs = table_assign_parse.lhs
        rhs = table_assign_parse.rhs
        cls.input_instance_flow = activity_data.xiflow

        # The executing instance is by nature a single instance flow
        xi_instance_flow = Flow_ap(fid=activity_data.xiflow, content=Content.INSTANCE, tname=activity_data.cname,
                                   max_mult=MaxMult.ONE)

        bactions, output_flow = TableExpr.process(mmdb, rhs=rhs, activity_data=activity_data,
                                        input_instance_flow=xi_instance_flow)

        output_flow_label = lhs
        # TODO: handle case where lhs is an explicit table assignment

        # Migrate the output_flow to a labeled flow
        _logger.info(f"Labeling output of table expression to [{lhs}]")
        Transaction.open(mmdb)
        # Delete the Unlabeled flow
        Relvar.deleteone(mmdb, "Unlabeled_Flow",
                         tid={"ID": output_flow.fid, "Activity": activity_data.anum, "Domain": activity_data.domain},
                         defer=True)
        # Insert the labeled flow
        Relvar.insert(relvar='Labeled_Flow', tuples=[
            Labeled_Flow_i(ID=output_flow.fid, Activity=activity_data.anum, Domain=activity_data.domain,
                           Name=output_flow_label)
        ])
        Transaction.execute()
        return bactions
