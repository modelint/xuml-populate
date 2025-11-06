"""
computation_action.py – Populate a computation action instance in PyRAL
"""

# System
import logging
from typing import Sequence, TYPE_CHECKING

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from scrall.parse.visitor import BOOL_a, MATH_a, IN_a, N_a


# xUML populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.exceptions.action_exceptions import ActionException
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.actions.expressions.table_expr import TableExpr
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Boundary_Actions
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Computation_Action_i, Computation_Input_i, Instance_Action_i

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

# Transactions
tr_Compute = "Computation Action"

class ComputationAction:
    """
    Populate a Compute Action
    """

    def __init__(self, expr: BOOL_a | MATH_a, activity: 'Activity'):
        """
        Collect all data required to populate a Computation Action

        Args:
            expr: A boolean or math scalar expression parse
            activity: The enclosing Activity
        """
        self.expr = expr

        self.anum = activity.anum
        self.domain = activity.domain
        self.activity = activity

        self.action_id = None
        self.operand_flows: list[str] = []
        self.expr_text = ''  # String will be filled out during population
        self.output_type = None
        self.output_flow = None

        # self.input_aids - input action ids
        # --
        # Each operand may or may not be have a scalar expression that requires the population of actions
        # to get the required input. An operand representing an attribute, for example, will require the
        # population of a Read Action to get the value.

        # Regardless of how many intermediate actions are required to get the input for an operatnd, we only care
        # about the Action(s) on the input boundary -- those furthest out from our Computation Action, typically
        # just one.
        self.input_aids: set[str] = set()  # The boundary input actions of each scalar expression creating actions

        self.input_instance_flow = activity.xiflow if activity.xiflow is not None else activity.piflow
        # Will still be None if the Activity is in an Assigner state model

    def walk(self, comp_expr: MATH_a | BOOL_a | N_a | IN_a):
        """
        Args:
            comp_expr:
        """
        from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
        operands = list()
        comp_expr_type = type(comp_expr).__name__
        match comp_expr_type:
            case 'BOOL_a':
                self.output_type = 'Boolean'
                op = comp_expr.op
                if op == 'NOT':
                    match type(comp_expr.operands).__name__:
                        case 'INST_PROJ_a':
                            self.expr_text = f"{self.expr_text} {op}"
                            se = ScalarExpr(expr=comp_expr.operands, input_instance_flow=self.input_instance_flow,
                                            activity=self.activity)
                            b, sflows = se.process()
                            if len(sflows) != 1:
                                msg = (f"Scalar flow not resolved in instance projection: [{self.expr_text}]"
                                       f" at: {self.activity.activity_path}")
                                _logger.error(msg)
                                ActionException(msg)
                            operand_symbol = sflows[0].fid
                            self.operand_flows.append(operand_symbol)
                            operands.append(operand_symbol)
                            self.expr_text = f"{self.expr_text} <{operand_symbol}>"
                            self.input_aids.update(b.ain)  # Just add the input boundary actions
                        case 'N_a' | 'IN_a':
                            self.expr_text = f"{self.expr_text} {op}"
                            name_expr = comp_expr.operands  # We know this is a Name_a namedtuple with a single value
                            fids = Flow.find_labeled_flows(name=name_expr.name, anum=self.anum, domain=self.domain)
                            if len(fids) == 1:
                                operand_symbol = fids[0]
                            elif len(fids) > 1:
                                # Not sure why this would occur, but not certain it won't!
                                msg = (f"Found multiple labeled flows with the same name as input to computation "
                                       f"action in: {self.activity.activity_path}")
                                _logger.error(msg)
                                raise ActionException(msg)
                            else:
                                # There is no matching labeled flow, so we probably have to generate
                                # an input data flow (labled or not)
                                # Our Computation Action can take any Data Flow input so we need to
                                # try resolving a scalar, instance, or table expression

                                # Scalar expression?
                                se = ScalarExpr(expr=name_expr, input_instance_flow=self.input_instance_flow,
                                                activity=self.activity)
                                _, sflows = se.process()
                                if sflows:
                                    operand_symbol = sflows[0].fid
                                else:
                                    # Instance set?
                                    ie = InstanceSet(iset_components=name_expr, input_instance_flow=self.input_instance_flow,
                                                     activity=self.activity)
                                    _, _, iflows = ie.process()
                                    if iflows:
                                        operand_symbol = iflows[0].fid
                                    else:
                                        # Table expression?
                                        # _, tflow = TableExpr.process(tuple_output=)
                                        # if tflow:
                                        #     operand_symbol = tflow.fid
                                        msg = (f"Could not resolve input to computation "
                                               f"at: {self.activity.activity_path}")
                                        _logger.error(msg)
                                        raise ActionException(msg)
                                        # TODO: Make table expression more like the other two for consitency
                                        # TODO: It currently assumes an RHS input, for example
                                        # TODO: also update TableExpr to return multiple flows consistency as well
                                    # else:
                                    #     # Give up

                            self.operand_flows.append(operand_symbol)
                            operands.append(operand_symbol)
                            # Append the flow and op to the expression text
                            # op_text = f" {op} " if count+1 < len(comp_expr.operands) else ""
                            self.expr_text = f"{self.expr_text} <{operand_symbol}>"
                            pass
                        case _:
                            # TODO: Add more cases
                            msg = f"DEBUG: {self.activity.activity_path}"
                            raise ActionException(msg)
                else:
                    # Not a unary boolean expr, so there can be multiple operands (using the same op)
                    # For example: A and B and C
                    for count, o_expr in enumerate(comp_expr.operands):
                        o_expr_type = type(o_expr).__name__
                        match o_expr_type:
                            case 'Enum_a':
                                op_text = f"{op}" if count + 1 < len(comp_expr.operands) else ""
                                self.expr_text = f"{self.expr_text} <{o_expr.value.name}> {op_text}"
                                pass
                            case 'BOOL_a' | 'MATH_a':
                                if count > 1:
                                    self.expr_text = f"{self.expr_text} {op}"
                                self.walk(o_expr)
                                pass
                            case 'N_a' | 'IN_a':
                                # See if the name matches a labeled scalar or non scalar flow
                                labeled_flow_ids = Flow.find_labeled_flows(name=o_expr.name, anum=self.anum, domain=self.domain)
                                if len(labeled_flow_ids) > 1:
                                    msg = f"Multiple labeled flows in Boolean operand {o_expr} at {self.activity.activity_path}"
                                    _logger.error(msg)
                                    raise ActionException(msg)
                                if labeled_flow_ids:
                                    expr_fid = labeled_flow_ids[0]
                                    self.operand_flows.append(expr_fid)
                                    # Append the flow and op to the expression text
                                    op_text = f"{op}" if count + 1 < len(comp_expr.operands) else ""
                                    self.expr_text = f"{self.expr_text} <{expr_fid}> {op_text}"
                                else:
                                    # Process as a scalar expression
                                    se = ScalarExpr(expr=o_expr, input_instance_flow=self.input_instance_flow,
                                                    activity=self.activity)
                                    b, sflows = se.process()
                                    self.input_aids.update(b.ain)  # Just add the input boundary actions
                                    if len(sflows) > 1:
                                        msg = f"Multiple scalar flows in Boolean operand {o_expr} at {self.activity.activity_path}"
                                        _logger.error(msg)
                                        raise ActionException(msg)
                                    expr_fid = sflows[0].fid
                                    self.operand_flows.append(expr_fid)
                                    # Append the flow and op to the expression text
                                    op_text = f"{op}" if count+1 < len(comp_expr.operands) else ""
                                    self.expr_text = f"{self.expr_text} <{expr_fid}> {op_text}"
                            case _:  # Not a simple name
                                # Process as a scalar expression
                                se = ScalarExpr(expr=o_expr, input_instance_flow=self.input_instance_flow,
                                                activity=self.activity)
                                b, sflows = se.process()
                                self.input_aids.update(b.ain)  # Just add the input boundary actions
                                if len(sflows) > 1:
                                    msg = (f"Multiple scalar flows in Boolean operand {o_expr} at "
                                           f"{self.activity.activity_path}")
                                    _logger.error(msg)
                                    raise ActionException(msg)
                                expr_fid = sflows[0].fid
                                self.operand_flows.append(expr_fid)
                                # Append the flow and op to the expression text
                                op_text = f" {op}" if count+1 < len(comp_expr.operands) else ""
                                self.expr_text = f"{self.expr_text} <{expr_fid}>{op_text}"
                        pass
            case 'MATH_a':
                pass  # TODO: Fill out
            case _:
                pass  # TODO: Raise exception
        pass

    def populate(self) -> tuple[Boundary_Actions, Flow_ap]:
        """
        Populate the Compute Action

        Returns:
            The computation's action id and result output flow
        """
        # At this point I don't have a good enough example to think this thing through
        # so this is just a placeholder.
        self.walk(self.expr)

        Transaction.open(db=mmdb, name=tr_Compute)
        self.output_flow = Flow.populate_scalar_flow(scalar_type=self.output_type, anum=self.anum, domain=self.domain,
                                                     label=f"_{self.expr_text.strip()}", activity_tr=tr_Compute)
        self.action_id = Action.populate(tr=tr_Compute, anum=self.anum, domain=self.domain, action_type="computation")
        Relvar.insert(db=mmdb, tr=tr_Compute, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Compute, relvar='Computation Action', tuples=[
            Computation_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                 Output_flow=self.output_flow.fid, Expression=self.expr_text)
        ])
        for f in self.operand_flows:
            Relvar.insert(db=mmdb, tr=tr_Compute, relvar='Computation Input', tuples=[
                Computation_Input_i(Computation=self.action_id, Activity=self.anum, Domain=self.domain, Input_flow=f)
            ])

        Transaction.execute(db=mmdb, name=tr_Compute)

        boundary_actions = Boundary_Actions(ain=self.input_aids, aout={self.action_id})
        return boundary_actions, self.output_flow
