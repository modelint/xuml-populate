""" table_expr.py -- Walk through a table expression and populate elements """

import logging
from typing import TYPE_CHECKING
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.rename_action import RenameAction
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap, Boundary_Actions
from xuml_populate.populate.actions.select_action import SelectAction
from xuml_populate.populate.actions.project_action import ProjectAction
from xuml_populate.populate.actions.set_action import SetAction
from xuml_populate.exceptions.action_exceptions import (TableOperationOrExpressionExpected, FlowException,
                                                        UndefinedHeaderExpressionOp)
from scrall.parse.visitor import TEXPR_a
from pyral.relation import Relation

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class TableExpr:
    """
    For reference, a table expression is defined in the scrall grammar as:

    table_expr = table_operation
    table_operation = table_term (TOP table_term)*
    table_term = table / "(" table_expr ")" header_expr? selection? projection?
    TOP = '^' / '+' / '-' / '*' / '%' / '##'
    table = instance_set header_expr? selection? projection?

    (whitespace tokens removed in the above extract)

    So we need to walk through the parse tree through the nested operations, possibly
    building instance sets and then handling various header expressions (rename, etc),
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
    activity_data = None
    action_inputs = None
    action_outputs = None

    @classmethod
    def process(cls, mmdb: 'Tk', activity_data: Activity_ap, rhs: TEXPR_a, input_instance_flow: Flow_ap) -> (
            Boundary_Actions, Flow_ap):
        """

        :param mmdb:
        :param activity_data:
        :param rhs: The right hand side of a table assignment
        :param input_instance_flow:
        :return:
        """
        cls.mmdb = mmdb
        cls.activity_data = activity_data
        cls.domain = activity_data.domain
        cls.anum = activity_data.anum
        cls.activity_path = activity_data.activity_path
        cls.scrall_text = activity_data.scrall_text

        cls.action_outputs = {}  # ID's of all Action output Data Flows
        cls.action_inputs = {}  # ID's of all Action input Data Flows

        x = cls.walk(texpr=rhs, input_flow=input_instance_flow)

        all_ins = {v for s in cls.action_inputs.values() for v in s}
        all_outs = {v for s in cls.action_outputs.values() for v in s}
        init_aids = {a for a in cls.action_inputs.keys() if not cls.action_inputs[a].intersection(all_outs)}
        final_aids = {a for a in cls.action_outputs.keys() if not cls.action_outputs[a].intersection(all_ins)}

        return Boundary_Actions(ain=init_aids, aout=final_aids), x

    @classmethod
    def walk(cls, texpr: TEXPR_a, input_flow: Flow_ap) -> Flow_ap:
        """

        :param input_flow:
        :param texpr: Parsed table expression
        """
        # Process the table component
        # It is either an instance set, name, or a nested table operation
        component_flow = input_flow
        match type(texpr.table).__name__:
            case 'N_a' | 'IN_a':
                # Is the name an existing Labeled Flow?
                R = f"Name:<{texpr.table.name}>, Activity:<{cls.anum}>, Domain:<{cls.domain}>"
                result = Relation.restrict(cls.mmdb, relation='Labeled_Flow', restriction=R)
                if result.body:
                    # Name corresponds to some Labled Flow instance
                    label_fid = result.body[0]['ID']
                    component_flow = Flow.lookup_data(fid=label_fid, anum=cls.anum, domain=cls.domain)
                else:
                    # Not a Labled Flow instance
                    # Is it a class name? If so, create a multiple instance flow and set component flow
                    R = f"Name:<{texpr.table.name}>, Domain:<{cls.domain}>"
                    result = Relation.restrict(cls.mmdb, relation='Class', restriction=R)
                    if result.body:
                        component_flow = Flow.populate_instance_flow(cls.mmdb, cname=texpr.table.name,
                                                                     activity=cls.anum, domain=cls.domain,
                                                                     label=None, pop=True)
                    else:
                        # Neither labeled flow or class
                        # TODO: check for other possible cases
                        _logger.error(f"Name [{texpr.table.name}] does not label any flow")
                        raise FlowException

            case 'INST_a':
                # Process the instance set and obtain its flow id
                input_flow = component_flow
                initial_aid, final_aid, component_flow = InstanceSet.process(mmdb=cls.mmdb,
                                                                             input_instance_flow=input_flow,
                                                                             iset_components=texpr.table.components,
                                                                             activity_data=cls.activity_data)
                # Add the output flow generated by the instance set expression to the set of ouput flows
                if initial_aid:
                    # For an InstanceSet with a single labled flow component, no action is created
                    # So don't process action inputs and outputs unless there is an initial_aid
                    cls.action_inputs[initial_aid] = {input_flow.fid}
                    if final_aid:
                        cls.action_outputs[final_aid] = {component_flow.fid}
            case 'TOP_a':
                # The table is an operation on one or more operands
                # We need to process each operand
                # text = f" {texpr.op} "  # Flatten operator into temporary string
                # insert Computation and set its operator attribute with texpr.op
                operand_flows = []
                for o in texpr.table.operands:
                    operand_flows.append(cls.walk(texpr=o, input_flow=component_flow))
                op_name = texpr.table.op
                aid, component_flow = SetAction.populate(cls.mmdb, a_input=operand_flows[0], b_input=operand_flows[1],
                                                         setop=op_name, activity_data=cls.activity_data)
                cls.action_inputs[aid] = {operand_flows[0].fid, operand_flows[1].fid}
                cls.action_outputs[aid] = {component_flow.fid}
                pass
            case _:
                _logger.error(
                    f"Expected INST, N, IN or TOP, but received {type(texpr).__name__} during table_expr walk")
                raise TableOperationOrExpressionExpected
        # Process optional header, selection, and projection actions for the TEXPR
        if texpr.hexpr:
            for header_op in texpr.hexpr:
                # Process each header operation
                match type(header_op).__name__:
                    case 'Rename_a':
                        # Populate a rename relational action
                        input_flow = component_flow
                        aid, component_flow = RenameAction.populate(cls.mmdb, input_nsflow=input_flow,
                                                                    from_attr=header_op.from_name,
                                                                    to_attr=header_op.to_name,
                                                                    activity_data=cls.activity_data)
                        cls.action_inputs[aid] = {input_flow.fid}
                        cls.action_outputs[aid] = {component_flow.fid}
                    case 'Extend':
                        print()
                    case _:
                        raise UndefinedHeaderExpressionOp
                pass
        if texpr.selection:
            # If there is a selection on the instance set, create the action and obtain its flow id
            input_flow = component_flow
            aid, component_flow = SelectAction.populate(cls.mmdb, input_instance_flow=input_flow,
                                                        select_agroup=texpr.selection, activity_data=cls.activity_data)
            cls.action_inputs[aid] = {input_flow.fid}
            cls.action_outputs[aid] = {component_flow.fid}
        if texpr.projection:
            # If there is a projection, create the action and obtain its flow id
            input_flow = component_flow
            aid, component_flow = ProjectAction.populate(cls.mmdb, input_nsflow=input_flow,
                                                         projection=texpr.projection, activity_data=cls.activity_data)
            cls.action_inputs[aid] = {input_flow.fid}
            cls.action_outputs[aid] = {component_flow.fid}
        return component_flow
