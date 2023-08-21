""" table_expr.py -- Walk through a table expression and populate elements """

import logging
from typing import TYPE_CHECKING, List, NamedTuple
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.actions.aparse_types import TableFlow_ap
from xuml_populate.populate.actions.aparse_types import InstanceFlow_ap, MaxMult
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class TableExpr:
    """
    For reference, a table exrpression is defined in the scrall grammar as:

    table_expr = table_operation
    table_operation = table_term (TOP table_term)*
    table_term = table / "(" table_expr ")" header_expr? selection? projection?
    TOP = '^' / '+' / '-' / '*' / '%' / '##'
    table = instance_set header_expr? selection? projection?

    (whitespace tokens removed in the above extract)

    So we need to walk through the parse tree through the nested operations, possibly
    building instance sets adn then handling various header expressions (rename, etc),
    selections, and projections. These are all delegated elsewhere.

    Here we focus on unnesting all those table ops and operands.
    """
    text = None  # A text representation of the expression
    mmdb = None
    domain = None
    anum = None
    scrall_text = None
    activity_path = None
    component_flow = None

    @classmethod
    def process(cls, mmdb: 'Tk', rhs: NamedTuple, anum: str, input_instance_flow: InstanceFlow_ap,
                domain: str, activity_path: str, scrall_text: str) -> TableFlow_ap:
        """

        :param rhs: The right hand side of a table assignment
        :param mmdb:
        :param anum:
        :param input_instance_flow:
        :param domain:
        :param activity_path:
        :param scrall_text:
        :return:
        """
        cls.mmdb = mmdb
        cls.domain = domain
        cls.anum = anum
        cls.activity_path = activity_path
        cls.scrall_text = scrall_text
        cls.component_flow = input_instance_flow

        # Two cases: TOP_a or TEXPR_a (operation or expression)
        # If it's just an expression, there is no nesting and we can break it down here
        # Most likely it is an operation, and we need to walk the tree
        cls.walk(texpr=rhs)

        # TODO: Populate output table flow

    @classmethod
    def walk(cls, texpr) -> str:
        """

        :param texpr: Either a nested operation or a terminal table expression
        :return: Text representation of THIS invocation of walk
        """
        match type(texpr).__name__:
            case 'TOP_a':
                # The table is an operation on one or more operands
                # We need to process each operand
                text = f" {texpr.op} "  # Flatten operator into temporary string
                # insert Computation and set its operator attribute with texpr.op
                for o in texpr.operands:
                    match type(o.table).__name__:
                        case 'INST_a':
                            op_flow = InstanceSet.process(mmdb=cls.mmdb, anum=cls.anum,
                                                          input_instance_flow=cls.component_flow,
                                                          iset_components=o.table.components, domain=cls.domain,
                                                          activity_path=cls.activity_path,
                                                          scrall_text=cls.scrall_text)
                            pass
                            # Add operand
                            # Insert instance flow for op_flow
                        case 'N_a', 'IN_a':
                            print()
                            # Flow already exists as variable or input param
                            # Add operand
            case 'TEXPR_a':
                cls.walk(texpr.table)
                # Process h, s, and p if any
                # If p, we have a table flow.
                # Insert table type and then pass it to table flow population
                print()

            # TODO: Convert instance flow to table flow

        return text
