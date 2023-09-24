"""
restrict_action.py – Populate a Restrict Action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set
from xuml_populate.populate.actions.aparse_types import Flow_ap, Activity_ap
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.actions.expressions.restriction_condition import RestrictCondition
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import (Relational_Action_i, Table_Action_i, Restrict_Action_i,
                                               Table_Restriction_Condition_i)
from pyral.relvar import Relvar
from pyral.relation import Relation  # Here for debugging
from pyral.transaction import Transaction
from scrall.parse.visitor import Selection_a

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class RestrictAction:
    """
    Create all relations for a Restrict Action
    """

    @classmethod
    def populate(cls, mmdb: 'Tk', input_relation_flow: Flow_ap, selection_parse: Selection_a,
                 activity_data: Activity_ap) -> (str, Flow_ap, Set[Flow_ap]):
        """
        Populate the Restrict Action

        :param mmdb:
        :param input_relation_flow: The source table flow into this restriction
        :param selection_parse:  The parsed Scrall select action group
        :param activity_data:
        :return: The select action id, the output flow, and any scalar flows input for attribute comparison
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        mmdb = mmdb
        domain = activity_data.domain
        anum = activity_data.anum

        # Populate the Action superclass instance and obtain its action_id
        action_id = Action.populate(mmdb, anum, domain)  # Transaction open

        # Populate the output Table Flow using same Table as input flow
        output_relation_flow = Flow.populate_table_flow(mmdb, activity=anum, domain=domain,
                                                        tname=input_relation_flow.tname, label=None, is_tuple=False)

        # Walk through the critieria parse tree storing any attributes or input flows
        _, sflows = RestrictCondition.process(mmdb, action_id=action_id, input_nsflow=input_relation_flow,
                                              selection_parse=selection_parse, activity_data=activity_data)
        # Restrict action does not use the returned cardinality since output is always a Table Flow

        Relvar.insert(relvar='Table_Restriction_Condition', tuples=[
            Table_Restriction_Condition_i(Restrict_action=action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(relvar='Relational_Action', tuples=[
            Relational_Action_i(ID=action_id, Activity=anum, Domain=domain)
        ])
        Relvar.insert(relvar='Table_Action', tuples=[
            Table_Action_i(ID=action_id, Activity=anum, Domain=domain,
                           Input_a_flow=input_relation_flow.fid, Output_flow=output_relation_flow.fid)
        ])
        Relvar.insert(relvar='Restrict_Action', tuples=[
            Restrict_Action_i(Action=action_id, Activity=anum, Domain=domain)
        ])
        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute()  # Restrict Action
        return action_id, output_relation_flow, sflows
