"""
action.py – Populate an action superclass instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from scrall.parse.visitor import PATH_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from class_model_dsl.populate.pop_types import Action_i
from collections import namedtuple


if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)

class Action:
    """
    A metamodel action
    """

    next_action_id = {}

    @classmethod
    def populate(cls, mmdb: 'Tk', anum:str, domain:str) -> str:
        """

        :param mmdb:
        :param anum:
        :param domain:
        :return:
        """
        activity_key = f'{domain}:{anum}' # combine attributes to get id
        if activity_key not in cls.next_action_id.keys():
            # Initialize the Action ID counter for a new Activity (anum)
            cls.next_action_id[activity_key] = 0
        # Get the next action ID for this Activity
        cls.next_action_id[activity_key] += 1
        actn_id = f'ACTN{cls.next_action_id[activity_key]}'

        # Now populate an instance of Action
        Transaction.open(mmdb)  # Action of some type

        # Populate the Statement superclass
        Relvar.insert(relvar='Action', tuples=[
            Action_i(ID=actn_id, Activity=anum, Domain=domain)
        ])
        return actn_id