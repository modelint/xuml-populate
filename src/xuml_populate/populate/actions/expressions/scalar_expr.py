""" sexpr.py -- Walk through a scalar expression and populate elements """

import logging
from typing import TYPE_CHECKING, List, NamedTuple
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.exceptions.action_exceptions import ScalarOperationOrExpressionExpected
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from scrall.parse.visitor import Scalar_RHS_a, MATH_a, BOOL_a, INST_a, N_a, Projection_a, Op_chain_a, INST_PROJ_a
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

    term = (NOT SP*)? UNARY_MINUS? (scalar / "(" SP* sexpr SP* ")")
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
                domain: str, activity_path: str, scrall_text: str) -> List[Flow_ap]:
        """
        Walks through a scalar expression on the right hand side of a scalar assignment to
        obtain a tuple flow with one or more attributes. Each attribute value will be assigned.
        The order in which attributes are specified in the action language is returned along with
        the tuple flow.

        :param mmdb:
        :param rhs: The right hand side of a table assignment
        :param anum:
        :param input_instance_flow:
        :param domain:
        :param activity_path:
        :param scrall_text:
        :return:  The output tuple flow and the attribute names as ordered in the RHS text expression
        """
        cls.mmdb = mmdb
        cls.domain = domain
        cls.anum = anum
        cls.activity_path = activity_path
        cls.scrall_text = scrall_text

        rhs = cls.walk(sexpr=rhs.expr, input_flow=input_instance_flow)
        return rhs

    @classmethod
    def resolve_iset(cls, iset: INST_a, op_chain: Op_chain_a = None, projection: Projection_a = None) -> List[Flow_ap]:
        pass

    @classmethod
    def walk(cls, sexpr: INST_PROJ_a | MATH_a | BOOL_a | N_a, input_flow: Flow_ap) -> [Flow_ap]:
        """

        :param sexpr:  Parsed scalar expression
        :param input_flow:
        :return:  Output scalar flow
        """
        component_flow = input_flow
        match type(sexpr).__name__:
            case 'INST_PROJ_a':
                component_flow = InstanceSet.process(mmdb=cls.mmdb, anum=cls.anum,
                                                     input_instance_flow=component_flow,
                                                     iset_components=sexpr.iset.components,
                                                     domain=cls.domain, activity_path=cls.activity_path,
                                                     scrall_text=cls.scrall_text)
                sflows = ReadAction.populate(cls.mmdb, input_single_instance_flow=component_flow,
                                             projection=sexpr.projection, anum=cls.anum, domain=cls.domain,
                                             activity_path=cls.activity_path, scrall_text=cls.scrall_text)
                return sflows
            case 'N_a':
                pass
            case 'BOOL_a':
                pass
            case 'MATH_a':
                operand_flows = []
                op_name = sexpr.op
                for o in sexpr.operands:
                    match type(o).__name__:
                        case 'INST_PROJ_a':
                            component_flow = InstanceSet.process(mmdb=cls.mmdb, anum=cls.anum,
                                                                 input_instance_flow=component_flow,
                                                                 iset_components=o.iset.components,
                                                                 domain=cls.domain, activity_path=cls.activity_path,
                                                                 scrall_text=cls.scrall_text)
                            if o.iset.select:
                                pass
                            if o.projection:
                                tflow = ProjectAction.populate(mmdb=cls.mmdb, projection=o.projection,
                                                               anum=cls.anum,
                                                               input_nsflow=component_flow,
                                                               domain=cls.domain,
                                                               activity_path=cls.activity_path,
                                                               scrall_text=cls.scrall_text)
                                pass
                            pass
                        case _:
                            pass

                    operand_flows.append(cls.walk(sexpr=o, input_flow=component_flow))
                pass
            case 'Op_chain_a':
                pass
            case _:
                _logger.error(
                    f"Expected .... but received {type(sexpr).__name__} during sexpr walk")
                raise ScalarOperationOrExpressionExpected
        # Process optional header, selection, and projection actions for the TEXPR
        return component_flow
