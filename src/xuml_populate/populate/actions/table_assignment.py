"""
table_assignment.py – Populate elements of a table assignment
"""

import logging
from typing import Dict, Set
from xuml_populate.config import mmdb
from xuml_populate.populate.mmclass_nt import Labeled_Flow_i
from xuml_populate.populate.actions.expressions.table_expr import TableExpr
from xuml_populate.populate.actions.aparse_types import (Flow_ap, MaxMult, Content, Activity_ap, Boundary_Actions,
                                                         Labeled_Flow)
from scrall.parse.visitor import Table_Assignment_a

from pyral.relvar import Relvar
from pyral.relation import Relation  # Keep for debugging
from pyral.transaction import Transaction

_logger = logging.getLogger(__name__)

# Transactions
tr_Migrate = "Migrate to Label"


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
    def process(cls, activity_data: Activity_ap, table_assign_parse: Table_Assignment_a,
                case_name: str, case_outputs: Set[Labeled_Flow] = None) -> Boundary_Actions:
        """
        Given a parsed table assignment consisting of an LHS and an RHS, populate each component action
        and return the resultant table flow

        We'll need an initial flow and we'll need to create intermediate instance flows to connect the components.
        The final output flow must be a table flow. The associated Table determines the type of the
        assignment. If the LHS spcifies an explicit Table, the resultant Table which must match.

        :param activity_data:
        :param table_assign_parse: A parsed table assignment
        :param case_name:
        :param case_outputs:
        """

        lhs = table_assign_parse.lhs
        rhs = table_assign_parse.rhs
        cls.input_instance_flow = activity_data.xiflow

        # The executing instance is by nature a single instance flow
        xi_flow = Flow_ap(fid=activity_data.xiflow, content=Content.INSTANCE, tname=activity_data.cname,
                          max_mult=MaxMult.ONE)

        bactions, output_flow = TableExpr.process(tuple_output=table_assign_parse.assign_tuple, rhs=rhs, activity_data=activity_data, input_instance_flow=xi_flow)

        case_prefix = '' if not case_name else f"{case_name}_"
        output_flow_label = case_prefix + lhs
        if case_name:
            case_outputs.add(Labeled_Flow(label=lhs, flow=output_flow))
        # TODO: handle case where lhs is an explicit table assignment

        # Migrate the output_flow to a labeled flow
        _logger.info(f"Labeling output of table expression to [{lhs}]")
        Transaction.open(mmdb, tr_Migrate)
        # Delete the Unlabeled flow
        Relvar.deleteone(mmdb, tr=tr_Migrate, relvar_name="Unlabeled_Flow",
                         tid={"ID": output_flow.fid, "Activity": activity_data.anum, "Domain": activity_data.domain})
        # Insert the labeled flow
        Relvar.insert(mmdb, tr=tr_Migrate, relvar='Labeled_Flow', tuples=[
            Labeled_Flow_i(ID=output_flow.fid, Activity=activity_data.anum, Domain=activity_data.domain,
                           Name=output_flow_label)
        ])
        Transaction.execute(mmdb, tr_Migrate)
        return bactions
