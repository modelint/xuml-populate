""" table_expr.py -- Walk through a table expression and populate elements """

import logging
from typing import TYPE_CHECKING, List, NamedTuple
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.actions.aparse_types import TableFlow_ap
from xuml_populate.populate.actions.aparse_types import InstanceFlow_ap, MaxMult
from xuml_populate.populate.actions.select_action import SelectAction
from xuml_populate.populate.actions.project_action import ProjectAction
from xuml_populate.exceptions.action_exceptions import TableOperationOrExpressionExpected, FlowException
from scrall.parse.visitor import TOP_a, TEXPR_a
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
    output_tflow_id = None

    @classmethod
    def process(cls, mmdb: 'Tk', rhs: TEXPR_a, anum: str, input_instance_flow: InstanceFlow_ap,
                domain: str, activity_path: str, scrall_text: str) -> str:
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
        return cls.walk(texpr=rhs)

    @classmethod
    def walk(cls, texpr: TEXPR_a) -> str:
        """

        :param texpr: Parsed table expression
        """
        # Process the table component
        # It is either an instance set, name, or a nested table operation
        output_fid = cls.component_flow
        match type(texpr.table).__name__:
            case 'N_a' | 'IN_a':
                R = f"Name:<{texpr.table.name}>, Activity:<{cls.anum}>, Domain:<{cls.domain}>"
                result = Relation.restrict3(cls.mmdb, relation='Labeled_Flow', restriction=R)
                if result.body:
                    output_fid = result.body[0]['ID']
                else:
                    pass
            case 'INST_a':
                # Process the instance set and obtain its flow id
                output_fid = InstanceSet.process(mmdb=cls.mmdb, anum=cls.anum,
                                                 input_instance_flow=output_fid,
                                                 iset_components=texpr.table.components,
                                                 domain=cls.domain,
                                                 activity_path=cls.activity_path,
                                                 scrall_text=cls.scrall_text)
            case 'TOP_a':
                print()
                # The table is an operation on one or more operands
                # We need to process each operand
                # text = f" {texpr.op} "  # Flatten operator into temporary string
                # insert Computation and set its operator attribute with texpr.op
                operand_flows = []
                for o in texpr.table.operands:
                    operand_flows.append(cls.walk(o))
                pass  # Process the operation
            case _:
                _logger.error(
                    f"Expected INST, N, IN or TOP, but received {type(texpr).__name__} during table_expr walk")
                raise TableOperationOrExpressionExpected
        # Process optional header, selection, and projection actions for the TEXPR
        if texpr.hexpr:
            # TODO: Implement this case
            pass
        if texpr.selection:
            # If there is a selection on the instance set, create the action and obtain its flow id
            output_fid = cls.component_flow = SelectAction.populate(
                cls.mmdb, input_instance_flow=output_fid, anum=cls.anum,
                select_agroup=texpr.selection,
                domain=cls.domain,
                activity_path=cls.activity_path, scrall_text=cls.scrall_text)
        if texpr.projection:
            # If there is a projection, create the action and obtain its flow id
            output_fid = ProjectAction.populate(cls.mmdb, input_nsflow=output_fid,
                                                         projection=texpr.projection,
                                                         anum=cls.anum, domain=cls.domain,
                                                         activity_path=cls.activity_path,
                                                         scrall_text=cls.scrall_text)
        return output_fid
