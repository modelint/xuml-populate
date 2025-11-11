""" table_expr.py -- Walk through a table expression and populate elements """

# System
import logging
from typing import TYPE_CHECKING

# Model Integration
from scrall.parse.visitor import Table_term_a, TOP_a
from pyral.relation import Relation

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.actions.expressions.class_accessor import ClassAccessor
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.rename_action import RenameAction
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Boundary_Actions
from xuml_populate.populate.actions.select_action import SelectAction
from xuml_populate.populate.actions.restrict_action import RestrictAction
from xuml_populate.populate.actions.project_action import ProjectAction
from xuml_populate.populate.actions.set_action import SetAction
from xuml_populate.exceptions.action_exceptions import (ActionException, TableOperationOrExpressionExpected,
                                                        FlowException,
                                                        UndefinedHeaderExpressionOp)
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
    tuple_output = None
    text = None  # A text representation of the expression
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
    def process(cls, tuple_output: bool, activity: 'Activity', rhs: TOP_a | Table_term_a, input_instance_flow: Flow_ap
                ) -> tuple[Boundary_Actions, Flow_ap]:
        """
        Initiate the recursive descent through a table expression and yield a final result as either a
        Table or Tuple Flow.

        :param tuple_output: The final output is a Tuple Flow
        :param activity: Context of the enclosing activity
        :param rhs: The right hand side of a table assignment
        :param input_instance_flow: This instance flow is available
        :return: boundary actions and a flow summary
        """
        cls.activity = activity
        cls.domain = activity.domain
        cls.anum = activity.anum
        cls.activity_path = activity.activity_path
        cls.scrall_text = activity.scrall_text

        cls.action_outputs = {}  # ID's of all Action output Data Flows
        cls.action_inputs = {}  # ID's of all Action input Data Flows

        final_output_flow = cls.walk(table_expr=rhs, input_nsflow=input_instance_flow)
        # If tuple output has been specified, for a tuple assignment for example, tighten the max multiplicity to one

        all_ins = {v for s in cls.action_inputs.values() for v in s}
        all_outs = {v for s in cls.action_outputs.values() for v in s}
        init_aids = {a for a in cls.action_inputs.keys() if not cls.action_inputs[a].intersection(all_outs)}
        final_aids = {a for a in cls.action_outputs.keys() if not cls.action_outputs[a].intersection(all_ins)}

        return Boundary_Actions(ain=init_aids, aout=final_aids), final_output_flow

    @classmethod
    def walk(cls, table_expr: TOP_a | Table_term_a, input_nsflow: Flow_ap) -> Flow_ap:
        """
        Args:
            table_expr:
            input_nsflow:

        Returns:
        """
        # Process the table component
        # It is either an instance set, name, or a nested table operation
        component_flow = input_nsflow
        match type(table_expr).__name__:
            case 'TOP_a':
                pass
                # The table is an operation on one or more operands
                # We need to process each operand
                # text = f" {texpr.op} "  # Flatten operator into temporary string
                # insert Computation and set its operator attribute with texpr.op
                operand_flows = []
                for o in table_expr.operands:
                    top_expr = o if type(o).__name__ == 'TOP_a' else TOP_a(op=None, operands=o)
                    operand_flows.append(cls.walk(table_expr=top_expr, input_nsflow=component_flow))
                op_name = table_expr.op
                aid, component_flow = SetAction.populate(a_input=operand_flows[0], b_input=operand_flows[1],
                                                         setop=op_name, activity=cls.activity)
                cls.action_inputs[aid] = {operand_flows[0].fid, operand_flows[1].fid}
                cls.action_outputs[aid] = {component_flow.fid}
            case 'Table_term_a':
                tt_type = type(table_expr.table).__name__
                match tt_type:
                    case 'N_a' | 'IN_a':
                        # Is the name an existing Labeled Flow?
                        R = f"Name:<{table_expr.table.name}>, Activity:<{cls.anum}>, Domain:<{cls.domain}>"
                        result = Relation.restrict(db=mmdb, relation='Labeled_Flow', restriction=R)
                        if result.body:
                            # Name corresponds to some Labeled Flow instance
                            label_fid = result.body[0]['ID']
                            component_flow = Flow.lookup_data(fid=label_fid, anum=cls.anum, domain=cls.domain)
                        else:
                            # Not a Labled Flow instance
                            # Is it a class name?  If so, we'll need a Class Accessor populated if we don't have one already
                            class_flow = ClassAccessor.populate(name=table_expr.table.name, anum=cls.anum, domain=cls.domain)
                            if class_flow:
                                # We have a Class Accessor either previously or just now populated
                                # Set its output flow to the current component output
                                component_flow = Flow_ap(fid=class_flow, content=Content.INSTANCE,
                                                         tname=table_expr.table.name, max_mult=MaxMult.MANY)
                            else:
                                # Neither labeled flow or class
                                # TODO: check for other possible cases
                                _logger.error(f"Name [{table_expr.table.name}] does not label any flow")
                                raise FlowException

                    case 'INST_a':
                        # Process the instance set and obtain its flow id
                        input_flow = component_flow
                        iset = InstanceSet(input_instance_flow=input_flow, iset_components=table_expr.table.components,
                                           activity=cls.activity)
                        initial_aid, final_aid, component_flow = iset.process()
                        # Add the output flow generated by the instance set expression to the set of ouput flows
                        if initial_aid:
                            # For an InstanceSet with a single labeled flow component, no action is created
                            # So don't process action inputs and outputs unless there is an initial_aid
                            cls.action_inputs[initial_aid] = {input_flow.fid}
                            if final_aid:
                                cls.action_outputs[final_aid] = {component_flow.fid}
                    case _:
                        msg = f"Unmatched table term case: {tt_type} during table_expr walk at {cls.activity.path}"
                        _logger.error(msg)
                        raise ActionException(msg)

                # Process optional header, selection, and projection actions for the TEXPR
                if table_expr.hexpr:
                    for header_op in table_expr.hexpr:
                        # Process each header operation
                        match type(header_op).__name__:
                            case 'Rename_a':
                                # Populate a rename relational action
                                input_flow = component_flow
                                aid, component_flow = RenameAction.populate(input_nsflow=input_flow,
                                                                            from_attr=header_op.from_name,
                                                                            to_attr=header_op.to_name,
                                                                            activity=cls.activity)
                                cls.action_inputs[aid] = {input_flow.fid}
                                cls.action_outputs[aid] = {component_flow.fid}
                            case 'Extend':
                                pass
                                # print()
                            case _:
                                raise UndefinedHeaderExpressionOp
                        pass
                if table_expr.selection:
                    # If there is a selection on the instance set, create the action and obtain its flow id
                    input_flow = component_flow  # TODO: input/component_flow redundant, just use component_flow
                    if input_flow.content == Content.RELATION:
                        aid, component_flow, input_sflows = RestrictAction.populate(input_relation_flow=input_flow,
                                                                                    selection_parse=table_expr.selection,
                                                                                    activity=cls.activity)
                        cls.action_inputs[aid] = {input_flow.fid}.union({f.fid for f in input_sflows})
                        cls.action_outputs[aid] = {component_flow.fid}
                    elif input_flow.content == Content.INSTANCE:
                        select_action = SelectAction(input_instance_flow=input_flow, selection_parse=table_expr.selection,
                                                     activity=cls.activity)
                        aid = select_action.action_id
                        component_flow = select_action.output_instance_flow
                        input_sflows = select_action.sflows
                        cls.action_inputs[aid] = {input_flow.fid}.union({f.fid for f in input_sflows})
                        cls.action_outputs[aid] = {component_flow.fid}
                    else:
                        raise ActionException
                if table_expr.projection:
                    # If there is a projection, create the action and obtain its flow id
                    input_flow = component_flow
                    aid, component_flow = ProjectAction.populate(input_nsflow=input_flow,
                                                                 projection=table_expr.projection, activity=cls.activity)
                    cls.action_inputs[aid] = {input_flow.fid}
                    cls.action_outputs[aid] = {component_flow.fid}
                        pass
        return component_flow
