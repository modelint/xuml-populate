"""
table_assignment.py – Populate elements of a table assignment
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from class_model_dsl.populate.actions.expressions.table_expr import TableExpr
from class_model_dsl.populate.flow import Flow

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
        Given a parsed instance set expression, populate each component action
        and return the resultant Class Type name

        We'll need an initial flow and we'll need to create intermediate instance flows to connect the components.
        The final output flow must be an instance flow. The associated Class Type determines the type of the
        assignment which must match any explicit type.

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

        output_flow = TableExpr.process(mmdb, operator=rhs.op, operands=rhs.operands, anum=anum, domain=domain,
                                        activity_path=activity_path, scrall_text=scrall_text)

        output_flow_label = lhs.name.name
        if lhs.exp_type and lhs.exp_type != cls.input_instance_ctype:
            # Raise assignment type mismatch exception
            pass
        Transaction.open(mmdb)
        assigned_flow = Flow.populate_table_flow(mmdb, tname=output_flow.ttype, activity=anum, domain=domain,
                                                 label=output_flow_label)

        _logger.info(f"INSERT Table Flow (assignment): ["
                     f"{domain}:{cls.input_instance_ctype}:{activity_path.split(':')[-1]}"
                     f":{output_flow_label}:{assigned_flow}]")
        Transaction.execute()
