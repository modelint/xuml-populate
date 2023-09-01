"""
read_action.py – Populate a read action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content
from xuml_populate.populate.actions.action import Action
from scrall.parse.visitor import Projection_a
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mmclass_nt import Read_Action_i, Attribute_Read_Access_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class ReadAction:
    """
    Create all relations for a Read Action
    """

    input_instance_flow = None  # We are selecting instances from this instance flow
    output_instance_flow = None
    anum = None
    expression = None
    comparison_criteria = []
    equivalence_criteria = []
    restriction_text = ""
    cardinality = None
    action_id = None
    domain = None  # in this domain
    mmdb = None  # The database
    criterion_ctr = 0
    activity_path = None
    scrall_text = None
    max_mult = None


    @classmethod
    def populate(cls, mmdb: 'Tk', input_single_instance_flow: Flow_ap, projection: Projection_a, anum: str,
                 domain: str, activity_path: str, scrall_text: str):
        """
        Populate the Read Action

        :param mmdb:
        :param input_single_instance_flow: The source flow into this selection
        :param projection:
        :param input_single_instance_flow:
        :param anum:
        :param domain:
        :param select_agroup:  The parsed Scrall select action group
        :param scrall_text:
        :param activity_path:
        """
        # Save attribute values that we will need when creating the various select subsystem
        # classes
        cls.mmdb = mmdb
        cls.domain = domain
        cls.anum = anum
        cls.activity_path = activity_path
        cls.scrall_text = scrall_text
        # Here we convert from scrall parse '1', 'M' notation to user friendly 'ONE', 'ALL'
        # If 1, user wants at most one arbitrary instance, even if many are selected
        # If M, get them all.
        # TODO: Update scrall parser to yield these values
        cls.cardinality = 'ONE' if select_agroup.card == '1' else 'ALL'

        cls.input_instance_flow = input_instance_flow

        # Populate the Action superclass instance and obtain its action_id
        cls.action_id = Action.populate(mmdb, anum, domain)  # Transaction open
        Relvar.insert(relvar='Select_Action', tuples=[
            Select_Action_i(ID=cls.action_id, Activity=anum, Domain=domain, Input_flow=input_instance_flow.fid)
        ])
        cls.select_agroup = select_agroup
        # Walk through the critieria parse tree storing any attributes or input flows
        # Also check to see if we are selecting on an identifier
        cls.process_criteria(criteria=select_agroup.criteria)

        # We now have a transaction with all select-action instances, enter into the metamodel db
        Transaction.execute()  # Select Action
        return cls.output_instance_flow
