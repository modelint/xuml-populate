""" table_expr.py -- Walk through a table expression and populate elements """

import logging
from typing import TYPE_CHECKING, List
from class_model_dsl.populate.actions.expressions.instance_set import InstanceSet
from class_model_dsl.populate.actions.aparse_types import TableFlow_ap
from class_model_dsl.populate.actions.aparse_types import InstanceFlow_ap, MaxMult

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
    component_iflow = None  # Component instance flow
    component_tflow = None  # Component table flow

    @classmethod
    def process(cls, mmdb: 'Tk', operator: str, operands: List, anum: str, input_instance_flow: InstanceFlow_ap,
                domain: str, activity_path: str, scrall_text: str) -> TableFlow_ap:
        cls.mmdb = mmdb
        cls.domain = domain
        cls.anum = anum
        cls.activity_path = activity_path
        cls.scrall_text = scrall_text
        cls.component_flow = input_instance_flow
        cls.text = cls.walk(operator, operands)

        # TODO: Populate output table flow

    @classmethod
    def walk(cls, operator: str, operands: List) -> str:
        """

        :param operator:
        :param operands:
        :return: Text representation of this invocation of walk
        """
        text = f" {operator} "  # Flatten operator into temporary string
        for o in operands:
            match type(o).__name__:
                case 'INST_a':
                    cls.component_iflow = InstanceSet.process(mmdb=cls.mmdb, anum=cls.anum,
                                                              input_instance_flow=cls.component_iflow,
                                                              iset_components=o.components, domain=cls.domain,
                                                              activity_path=cls.activity_path,
                                                              scrall_text=cls.scrall_text)
                    pass
                    # TODO: Convert instance flow to table flow

        return text
