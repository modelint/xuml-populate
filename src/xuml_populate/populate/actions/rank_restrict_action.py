"""
rank_restrict_action.py – Populate a Rank Restrict Action instance in PyRAL
"""

import logging
from typing import Set
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, ActivityAP
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.actions.expressions.restriction_condition import RestrictCondition
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Relational_Action_i, Table_Action_i, Rank_Restrict_Action_i
from pyral.relvar import Relvar
from pyral.relation import Relation  # Here for debugging
from pyral.transaction import Transaction
from scrall.parse.visitor import Criteria_Selection_a, Rank_Selection_a

_logger = logging.getLogger(__name__)

# Transactions
tr_Rank_Restrict_Action = "Rank Restrict Action"

class RankRestrictAction:
    """
    Create all relations for a Restrict Action
    """

    def __init__(self, input_relation_flow: Flow_ap, selection_parse: Rank_Selection_a,
                 activity_data: ActivityAP):
        """
        Populate the Rank Restrict Action
         -> (str, Flow_ap, Set[Flow_ap])
        :param input_relation_flow: The source table flow into this restriction
        :param selection_parse:  The parsed Scrall select action group
        :param activity_data:
        :return: The select action id, the output flow, and any scalar flows input for attribute comparison
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        domain = activity_data.domain
        anum = activity_data.anum

        # Populate the Action superclass instance and obtain its action_id
        Transaction.open(db=mmdb, name=tr_Rank_Restrict_Action)
        self.action_id = Action.populate(tr=tr_Rank_Restrict_Action, anum=anum, domain=domain, action_type="rank restrict")

        # Populate the output Table Flow using same Table as input flow
        # TODO: This is a tuple flow if the cardinality is one
        self.output_relation_flow = Flow.populate_relation_flow_by_reference(
            ref_flow=input_relation_flow, anum=anum, domain=domain, tuple_flow=selection_parse.card == 'ONE')

        Relvar.insert(db=mmdb, tr=tr_Rank_Restrict_Action, relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=self.action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Rank_Restrict_Action, relvar='Table_Action', tuples=[
            Table_Action_i(ID=self.action_id, Activity=anum, Domain=domain,
                           Input_a_flow=input_relation_flow.fid, Output_flow=self.output_relation_flow.fid)
        ])
        Relvar.insert(db=mmdb, tr=tr_Rank_Restrict_Action, relvar='Rank_Restrict_Action', tuples=[
            Rank_Restrict_Action_i(ID=self.action_id, Activity=anum, Domain=domain,
                                   Attribute=selection_parse.attr, Non_scalar_type=input_relation_flow.tname,
                                   Selection_cardinality=selection_parse.card, Extent=selection_parse.rankr)
        ])
        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute(db=mmdb, name=tr_Rank_Restrict_Action)  # Restrict Action