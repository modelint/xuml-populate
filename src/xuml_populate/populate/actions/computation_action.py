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
from scrall.parse.visitor import BOOL_a, MATH_a

from xuml_populate.exceptions.action_exceptions import ActionException
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr

# xUML populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.utility import print_mmdb  # Debugging
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Computation_Action_i, Computation_Input_i, Instance_Action_i

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

        self.input_instance_flow = activity.xiflow if activity.xiflow is not None else activity.piflow
        # Will still be None if the Activity is in an Assigner state model

    def resolve_operand(self, operand: str) -> str:
        """
        Return a symbol, such as a flow ID, to represent the operand in the expression text

        Args:
            operand:

        Returns:
            symbol text
        """
        # TODO: Check for non-flow symbol cases (for now, flow assumed)
        fid = Flow.find_labeled_flow(name=operand, anum=self.anum, domain=self.domain)
        self.operand_flows.append(fid)
        return fid

    def populate(self) -> tuple[str, Flow_ap]:
        """
        Populate the Compute Action

        Returns:
            The computation's action id and result output flow
        """
        # At this point I don't have a good enough example to think this thing through
        # so this is just a placeholder.
        op = None
        operands = list()
        match type(self.expr).__name__:
            case 'BOOL_a':
                self.output_type = 'Boolean'
                op = self.expr.op
                if op == 'NOT':
                    match type(self.expr.operands).__name__:
                        case 'N_a' | 'IN_a':
                            operand_symbol = self.resolve_operand(operand=self.expr.operands.name)
                            if not operand_symbol:
                                msg = f"Could not resolve operand: {self.expr.operands.name} in NOT expression at {self.activity.activity_path}"
                                _logger.error(msg)
                                raise ActionException(msg)
                            operands.append(operand_symbol)
                        case _:
                            pass  # TODO: Add more cases
                else:
                    # Not a unary boolean expr, so there must be two operands
                    for o_expr in self.expr.operands:
                        se = ScalarExpr(expr=o_expr, input_instance_flow=self.input_instance_flow, activity=self.activity)
                        _, sflows = se.process()
                        if len(sflows) > 1:
                            msg = f"Multiple scalar flows in Boolean operand {o_expr} at {self.activity.activity_path}"
                            _logger.error(msg)
                            raise ActionException(msg)
                        self.operand_flows.append(sflows[0].fid)
            case 'MATH_a':
                pass  # TODO: Fill out
            case _:
                pass  # TODO: Raise exception

        if len(operands) == 1:
            self.expr_text = f"{op} <{operands[0]}>"
        else:
            self.expr_text = f"<{self.operand_flows[0]}> {op} <{self.operand_flows[1]}>"

        Transaction.open(db=mmdb, name=tr_Compute)
        self.output_flow = Flow.populate_scalar_flow(scalar_type=self.output_type, anum=self.anum, domain=self.domain,
                                                     label=f"_{self.expr_text}", activity_tr=tr_Compute)
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
        return self.action_id, self.output_flow
