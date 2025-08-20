"""
decision_action.py – Populate a decision action instance in PyRAL
"""

# System
import logging

# Model Integration
from scrall.parse.visitor import Decision_a, Signal_a
from pyral.relvar import Relvar
from pyral.relvar import Relation
from pyral.transaction import Transaction

# xUML populate
from xuml_populate.utility import print_mmdb
from xuml_populate.populate.actions.computation_action import ComputationAction
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.populate.mmclass_nt import Result_i, Decision_Action_i
from xuml_populate.exceptions.action_exceptions import *

_logger = logging.getLogger(__name__)

# Transactions
tr_Decision = "Decision Action"

class DecisionAction:
    """
    Create all relations for a Decision Action.
    """
    # TODO: Implement other Signal Action subclasses
    def __init__(self, statement_parse: Decision_a, activity_data: ActivityAP):
        """
        Initialize with everything the Signal statement requires

        Args:
            statement_parse: Parsed representation of the Signal statement
            activity_data: Collected info about the activity
        """
        self.action_id = None
        self.statement_parse = statement_parse
        self.activity_data = activity_data
        self.anum = activity_data.anum
        self.domain = activity_data.domain
        self.decision_input_flow = None

    def process(self) -> Boundary_Actions:
        """
        Returns:
            Boundary_Actions: The signal action id is both the initial and final action id
        """
        # Process the input to the transaction to obtain an input data flow
        # This can be any kind of data, but during Model Execution, the flowing value must resolve to true or false
        # For example, an instance flow with zero instances would be false
        # A scalar 0 would be false with any other value interpreted as true
        # And relation flow is false if it contains zero tuples, otherwise true

        # Process the decision input, creating whatever actions are necessary resulting in a Decision Input flow
        decision_input = self.statement_parse.input  # Expression to be evaluated as true or false during execution

        decision_input_type = type(decision_input).__name__
        input_init_aid: set[str] = {}  # Default to empty set of strings
        match decision_input_type:
            case 'INST_PROJ_a':
                # We need to evaluate an instance set and a possible projection
                iset = InstanceSet(input_instance_flow=self.activity_data.xiflow,
                                   iset_components=decision_input.iset.components, activity_data=self.activity_data)
                input_init_aid, input_final_aid, self.decision_input_flow = iset.process()
                if self.statement_parse.input.projection:
                    # We have an attribute value to extract and test as a scalar value most likely
                    # TODO: Handle decision input projection
                    pass
            case 'N_a':
                # We have the name of a flow, verify it exists
                iset = InstanceSet(iset_components=[decision_input], activity_data=self.activity_data)
                # It's just a flow, so the returned initial, final actions should be empty
                _, _, self.decision_input_flow = iset.process()
            case 'BOOL_a':
                ca = ComputationAction(expr=decision_input, activity_data=self.activity_data)
                _, self.decision_input_flow = ca.populate()
            case _:
                pass

        # We'll need a control flow for the true and false results enabling any number of newly populated Actions
        true_result = self.statement_parse.true_result
        false_result = self.statement_parse.false_result

        # Handle if/then signaling shorthand
        # --
        # Process ev1 -> : ev2 -> target   -- Scrall shorthand where target is the dest of both events
        # The Scrall parser doesn't copy the target into ev1, it just sets the dest of that event to None
        # So we need to re-specify ev1 with a complete Signal statement if we are using this shorthand
        # This is only relevant if the true_result is a Signal statement with no explicit destination
        # --
        # TODO: Rethink shared dest so that xunits are handled properly
        # shared_dest = None
        # true_statement = true_result.statement  # We'll need to change this if the shorthand was used
        if type(true_result.statement).__name__ == 'Signal_a' and not true_result.statement.dest:
            pass
        #     # The false_result must be a Signal supplying the shared destination
        #     # Verify that a shared destination is provided by the false result
        #     if type(false_result.statement).__name__ != 'Signal_a':
        #         msg = f"No destination specified for signal in true result"
        #         _logger.error(msg)
        #         raise ActionException(msg)
        #     shared_dest = false_result.statement.dest  # Grab the false result signal's destination
        #     # But make sure that the false result signal statement actually supplied a destination
        #     if not shared_dest:
        #         msg = f"No destination specified for signal in false result"
        #         _logger.error(msg)
        #         raise ActionException(msg)
        #
        # if shared_dest:
        #     # We have two signal statements with a shared destination,
        #     # so need to create a new Signal_a tuple with the shared_dest value inserted
        #     true_statement = Signal_a(event=true_result.statement.event,
        #                               supplied_params=true_result.statement.supplied_params, dest=shared_dest)

        # We'll use true_statement instead of true_result.statement in case we had to ammend

        # Populate the true and false result statements and grab the initial actions of each so we can enable them
        from xuml_populate.populate.xunit import ExecutionUnit
        t_boundary_actions = ExecutionUnit.process_statement_set(activity_data=self.activity_data,
                                                                 content=true_result)
        true_init_actions = t_boundary_actions.ain

        if false_result:
            f_boundary_actions = ExecutionUnit.process_statement_set(activity_data=self.activity_data,
                                                                     content=false_result)
            false_init_actions = f_boundary_actions.ain
            d_final_aids = t_boundary_actions.aout | f_boundary_actions.aout

        Transaction.open(db=mmdb, name=tr_Decision)
        # Populate Action / Decision Action
        self.action_id = Action.populate(tr=tr_Decision, anum=self.anum, domain=self.domain, action_type="decision")
        Relvar.insert(db=mmdb, tr=tr_Decision, relvar='Decision Action', tuples=[
            Decision_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                              Boolean_input=self.decision_input_flow.fid)
        ])
        # Populate Results (Control Flows)
        true_result_flow = Flow.populate_control_flow(tr=tr_Decision, enabled_actions=true_init_actions,
                                                      anum=self.anum, domain=self.domain,
                                                      label=f"_{self.action_id[4:]}_true")
        Relvar.insert(db=mmdb, tr=tr_Decision, relvar='Result', tuples=[
            Result_i(Decision=True, Decision_action=self.action_id, Activity=self.anum, Domain=self.domain,
                     Flow=true_result_flow)
        ])
        false_result_flow = Flow.populate_control_flow(tr=tr_Decision, enabled_actions=false_init_actions,
                                                       anum=self.anum, domain=self.domain,
                                                       label=f"_{self.action_id[4:]}_false")
        Relvar.insert(db=mmdb, tr=tr_Decision, relvar='Result', tuples=[
            Result_i(Decision=False, Decision_action=self.action_id, Activity=self.anum, Domain=self.domain,
                     Flow=false_result_flow)
        ])
        Transaction.execute(db=mmdb, name=tr_Decision)

        return Boundary_Actions(ain={input_init_aid}, aout=d_final_aids)
