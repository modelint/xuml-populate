"""
table_assignment.py – Populate elements of a table assignment
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from class_model_dsl.populate.actions.traverse_action import TraverseAction
from class_model_dsl.populate.actions.select_action import SelectAction
from class_model_dsl.populate.mm_class import MMclass
from class_model_dsl.populate.flow import Flow
from class_model_dsl.exceptions.action_exceptions import AssignZeroOneInstanceHasMultiple
from class_model_dsl.populate.actions.instance_set import InstanceSet

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
    def walk_table_expr(cls, operator, operands) -> str:
        text = f" {operator} "  # Flatten operator into temporary string
        for o in operands:
            match type(o).__name__:
                case 'INST_a':
                    InstanceSet.process(mmdb=cls.mmdb, anum=cls.anum, iset_parse=o, domain=cls.domain,
                                        activity_path=cls.activity_path, scrall_text=cls.scrall_text)

        pass

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
        cls.mmdb = mmdb
        cls.anum = anum
        cls.domain = domain
        cls.activity_path = activity_path
        cls.scrall_text = scrall_text
        lhs = table_assign_parse.lhs
        rhs = table_assign_parse.rhs
        ctype = cname  # Initialize with the instance/ee class
        cls.input_instance_flow = xi_flow_id

        # TODO: Walk table expression and populate components
        expr_txt = cls.walk_table_expr(rhs.op, rhs.operands)

        output_flow_label = lhs.name.name
        if lhs.exp_type and lhs.exp_type != cls.input_instance_ctype:
            # Raise assignment type mismatch exception
            pass
        Transaction.open(mmdb)
        # TODO: need value for Table Type Name
        assigned_flow = Flow.populate_table_flow(mmdb, tname='', activity=anum, domain=domain,
                                                 label=output_flow_label)

        _logger.info(f"INSERT Table Flow (assignment): ["
                     f"{domain}:{cls.input_instance_ctype}:{activity_path.split(':')[-1]}"
                     f":{output_flow_label}:{assigned_flow}]")
        Transaction.execute()
