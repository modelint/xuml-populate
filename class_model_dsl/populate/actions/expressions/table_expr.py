""" table_expr.py -- Walk through a table expression and populate elements """

import logging
from typing import TYPE_CHECKING, List
from class_model_dsl.populate.actions.expressions.instance_set import InstanceSet
from class_model_dsl.populate.actions.aparse_types import TableFlow_ap

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

    @classmethod
    def process(cls, mmdb: 'Tk', operator: str, operands: List, anum: str, domain: str,
                activity_path: str, scrall_text: str) -> TableFlow_ap:
        cls.mmdb = mmdb
        cls.domain = domain
        cls.anum = anum
        cls.activity_path = activity_path
        cls.scrall_text = scrall_text
        cls.text = cls.walk(mmdb, operator, operands)

        # TODO: Populate output table flow

    @classmethod
    def walk(cls, mmdb: 'Tk', operator: str, operands: List) -> str:
        """

        :param mmdb:
        :param operator:
        :param operands:
        :return:
        """
        text = f" {operator} "  # Flatten operator into temporary string
        for o in operands:
            match type(o).__name__:
                case 'INST_a':
                    InstanceSet.process(mmdb=mmdb, anum=anum, iset_parse=o, domain=domain,
                                        activity_path=activity_path, scrall_text=scrall_text)
                    # TODO: Convert instance flow to table flow

        return text
