"""
rank_restrict_action.py – Populate a Rank Restrict Action instance in PyRAL
"""
# System
import logging
from typing import Set, TYPE_CHECKING, Optional

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation  # Here for debugging
from pyral.transaction import Transaction
from scrall.parse.visitor import Criteria_Selection_a, Rank_Selection_a, Rank_Criterion_a

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.actions.expressions.restriction_condition import RestrictCondition
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.iterator import IteratorAction
from xuml_populate.populate.actions.method_extender import MethodExtender
# from xuml_populate.populate.actions.type_operation_extender import TypeOperationExtender
from xuml_populate.populate.mmclass_nt import Relational_Action_i, Table_Action_i, Rank_Restrict_Action_i

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

# Transactions
tr_Rank_Restrict_Action = "Rank Restrict Action"
tr_TypeOp_Extender = "Type Operation Extender"


class RankRestrictAction:
    """
    Create all relations for a Restrict Action
    """

    def __init__(self, input_flow: Flow_ap, selection_parse: Rank_Selection_a, activity: 'Activity'):
        """
        Populate the Rank Restrict Action
         -> (str, Flow_ap, Set[Flow_ap])
        :param input_flow: The source table flow into this restriction
        :param selection_parse:  The parsed Scrall select action group
        :param activity:
        :return: The select action id, the output flow, and any scalar flows input for attribute comparison
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        self.activity = activity
        self.domain = activity.domain
        self.anum = activity.anum

        self.rr_parse = selection_parse
        self.input_flow = input_flow
        self.output_relation_flow = None
        self.action_id = None

    def populate(self) -> Optional[tuple[str, Flow_ap]]:
        for c in self.rr_parse.criteria:
            self.populate_ranked_attr(c) if c.attr else self.populate_ranked_call(c)

    def populate_ranked_call(self, c: Rank_Criterion_a) -> Optional[tuple[str, Flow_ap]]:
        """
        Populate a ranked type operation( on an attribute ) or method

        Returns:
            The action id and output Relation Flow
        """
        # Examine the call parse to determine what kind of Extender we are populating
        call_expr = c.call.call.components[0]
        if type(call_expr).__name__ == 'Op_a':
            # We are invoking an unqualified operation (.some method)
            method_ex = MethodExtender(op_parse=call_expr, input_iflow=self.input_flow, activity=self.activity)
            method_ex.populate()
            pass
        else:
            # We have some kind of scalar expression like an attribute name or maybe some math
            pass

        pass

    def populate_ranked_attr(self, c: Rank_Criterion_a) -> Optional[tuple[str, Flow_ap]]:
        """
        Populate the a ranked attribute or scalar flow

        Returns:
            The action id and output Relation Flow
        """
        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Rank_Restrict_Action)
        self.action_id = Action.populate(tr=tr_Rank_Restrict_Action, anum=self.anum, domain=self.domain,
                                         action_type="rank restrict")

        # Populate the output Table Flow using same Table as input flow
        # TODO: This is a tuple flow if the cardinality is one
        self.output_relation_flow = Flow.populate_relation_flow_by_reference(
            ref_flow=self.input_flow, anum=self.anum, domain=self.domain, tuple_flow=self.rr_parse.card == 'ONE')

        Relvar.insert(db=mmdb, tr=tr_Rank_Restrict_Action, relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Rank_Restrict_Action, relvar='Table_Action', tuples=[
            Table_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                           Input_a_flow=self.input_flow.fid, Output_flow=self.output_relation_flow.fid)
        ])
        Relvar.insert(db=mmdb, tr=tr_Rank_Restrict_Action, relvar='Rank_Restrict_Action', tuples=[
            Rank_Restrict_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                   Attribute=self.self.rr_parse.attr, Non_scalar_type=self.input_flow.tname,
                                   Selection_cardinality=self.self.rr_parse.card, Extent=self.self.rr_parse.rankr)
        ])
        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute(db=mmdb, name=tr_Rank_Restrict_Action)  # Restrict Action
