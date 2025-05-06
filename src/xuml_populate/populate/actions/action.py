"""
action.py – Populate an action superclass instance in PyRAL
"""

import logging
from typing import Set, Dict, List, Optional
from xuml_populate.config import mmdb
from scrall.parse.visitor import PATH_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from xuml_populate.populate.mmclass_nt import Action_i, Wave_i
from collections import namedtuple


_logger = logging.getLogger(__name__)

class Action:
    """
    A metamodel action
    """

    next_action_id = {}

    @classmethod
    def populate(cls, tr: str, anum: str, domain: str, action_type: str) -> str:
        """

        :param tr: Open db transaction
        :param anum: The Activity Number
        :param domain: Name of the domain
        :param action_type:  The subclass of this action
        :return: The action id
        """
        activity_key = f'{domain}:{anum}'  # combine attributes to get id
        if activity_key not in cls.next_action_id.keys():
            # Initialize the Action ID counter for a new Activity (anum)
            cls.next_action_id[activity_key] = 0
        # Get the next action ID for this Activity
        cls.next_action_id[activity_key] += 1
        actn_id = f'ACTN{cls.next_action_id[activity_key]}'

        # Now populate an instance of Action
        _logger.info("Transaction open: Action")


        # Populate the Statement superclass
        Relvar.insert(db=mmdb, tr=tr, relvar='Action', tuples=[
            Action_i(ID=actn_id, Activity=anum, Domain=domain, Type=action_type)
        ])
        return actn_id
