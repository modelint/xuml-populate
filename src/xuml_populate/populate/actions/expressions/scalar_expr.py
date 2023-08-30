""" scalar_expr.py -- Walk through a scalar expression and populate elements """

import logging
from typing import TYPE_CHECKING, List, NamedTuple
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.exceptions.action_exceptions import ScalarOperationOrExpressionExpected
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from scrall.parse.visitor import Scalar_RHS_a
from xuml_populate.populate.actions.project_action import ProjectAction
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class ScalarExpr:
    """
    For reference, a scalar expression in the scrall grammar consists of terms

    term = (NOT SP*)? UNARY_MINUS? (scalar / "(" SP* scalar_expr SP* ")")
    scalar = value / QTY? scalar_chain
    scalar_chain = (ITS op_chain) / ((scalar_source / instance_set projection?) op_chain?)
    scalar_source = type_selector / input_param
    op_chain = ('.' (scalar_op / name))*
    scalar_op = name supplied_params

    So we need to walk through the parse tree through the nested operations, possibly
    building instance sets.
    """
    text = None  # A text representation of the expression
    mmdb = None
    domain = None
    anum = None
    scrall_text = None
    activity_path = None
    component_flow = None
    output_tflow_id = None

    @classmethod
    def process(cls, mmdb: 'Tk', rhs: Scalar_RHS_a, anum: str, input_instance_flow: Flow_ap,
                domain: str, activity_path: str, scrall_text: str) -> Flow_ap:
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
        # cls.component_flow = input_instance_flow

        return cls.walk(scalar_expr=rhs, input_flow=input_instance_flow)

    @classmethod
    def walk(cls, scalar_expr: Scalar_RHS_a, input_flow: Flow_ap) -> Flow_ap:
        """

        :param scalar_expr:  Parsed scalar expression
        :param input_flow:
        """
        component_flow = input_flow
        for term in scalar_expr.expr:
            match type(term).__name__:
                case 'INST_a':
                    # Process the instance set and obtain its flow id
                    component_flow = InstanceSet.process(mmdb=cls.mmdb, anum=cls.anum,
                                                         input_instance_flow=component_flow,
                                                         iset_components=term.components,
                                                         domain=cls.domain, activity_path=cls.activity_path,
                                                         scrall_text=cls.scrall_text)
                case 'Projection_a':
                    component_flow = ProjectAction.populate(mmdb=cls.mmdb, projection=term, anum=cls.anum,
                                                            input_nsflow=component_flow,
                                                            domain = cls.domain, activity_path = cls.activity_path,
                                                            scrall_text = cls.scrall_text)
                    pass
                case _:
                    _logger.error(
                        f"Expected .... but received {type(scalar_expr.expr).__name__} during scalar_expr walk")
                    raise ScalarOperationOrExpressionExpected
        # Process optional header, selection, and projection actions for the TEXPR
        if scalar_expr.attrs:
            # If there is a projection, create the action and obtain its flow id
            component_flow = ProjectAction.populate(cls.mmdb, input_nsflow=component_flow,
                                                    projection=texpr.projection,
                                                    anum=cls.anum, domain=cls.domain,
                                                    activity_path=cls.activity_path,
                                                    scrall_text=cls.scrall_text)
        return component_flow
