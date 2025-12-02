"""
table_assignment.py – Populate elements of a table assignment
"""
# System
import logging
from typing import Dict, Set, TYPE_CHECKING

# Model Integration
from scrall.parse.visitor import Table_Assignment_a
from pyral.relvar import Relvar
from pyral.relation import Relation  # Keep for debugging
from pyral.transaction import Transaction


# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.config import mmdb
from xuml_populate.populate.mmclass_nt import Labeled_Flow_i
from xuml_populate.populate.actions.gate_action import GateAction
from xuml_populate.populate.actions.expressions.table_expr import TableExpr
from xuml_populate.populate.actions.aparse_types import (Flow_ap, MaxMult, Content, Boundary_Actions, Labeled_Flow)

if __debug__:
    from xuml_populate.utility import print_mmdb

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
    def process(cls, activity: 'Activity', table_assign_parse: Table_Assignment_a, case_name: str) -> Boundary_Actions:
        """
        Given a parsed table assignment consisting of an LHS and an RHS, populate each component action
        and return the resultant table flow

        We'll need an initial_pseudo_state flow and we'll need to create intermediate instance flows to connect the components.
        The final output flow must be a table flow. The associated Table determines the type of the
        assignment. If the LHS spcifies an explicit Table, the resultant Table which must match.

        :param activity:
        :param table_assign_parse: A parsed table assignment
        :param case_name:
        """

        lhs = table_assign_parse.lhs
        rhs = table_assign_parse.rhs
        cls.input_instance_flow = activity.xiflow

        # The executing instance is by nature a single instance flow
        xi_flow = Flow_ap(fid=activity.xiflow.fid, content=Content.INSTANCE, tname=activity.class_name,
                          max_mult=MaxMult.ONE)

        te = TableExpr(tuple_output=table_assign_parse.assign_tuple, parse=rhs, activity=activity,
                       input_instance_flow=xi_flow)
        bactions, output_flow = te.process()
        # Verify that theref is a single output action and extract it for later use
        if not len(bactions.aout):
            # TODO: Check for non-action pass through
            msg = f"Table assignment needs pass action at {activity.activity_path}"
            _logger.error(msg)
            raise IncompleteActionException
        if len(bactions.aout) > 1:
            msg = f"Expected only one Action output in Table assignment at {activity.activity_path}"
            _logger.error(msg)
            raise ActionException
        # Save the final output action
        (final_output_aid,) = bactions.aout
        activity.labeled_outputs[output_flow.fid] = final_output_aid

        case_prefix = '' if not case_name else f"{case_name}_"
        output_flow_label = case_prefix + lhs
        # TODO: handle case where lhs is an explicit table assignment

        # Migrate the output_flow to a labeled flow
        _logger.info(f"Labeling output of table expression to [{lhs}]")
        Transaction.open(db=mmdb, name=tr_Migrate)
        # Delete the Unlabeled flow
        Relvar.deleteone(db=mmdb, tr=tr_Migrate, relvar_name="Unlabeled_Flow",
                         tid={"ID": output_flow.fid, "Activity": activity.anum, "Domain": activity.domain})
        # Insert the labeled flow
        Relvar.insert(db=mmdb, tr=tr_Migrate, relvar='Labeled_Flow', tuples=[
            Labeled_Flow_i(ID=output_flow.fid, Activity=activity.anum, Domain=activity.domain,
                           Name=output_flow_label)
        ])
        Transaction.execute(db=mmdb, name=tr_Migrate)

        pass
        GateAction.gate_duplicate_labeled_nsflow(aid=final_output_aid, fid=output_flow.fid, label=output_flow_label, activity=activity)

        return bactions
