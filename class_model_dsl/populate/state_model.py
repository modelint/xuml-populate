"""
state_model.py – Populate a lifecycle instance into the metamodel
"""

import logging
from PyRAL.relvar import Relvar
from PyRAL.transaction import Transaction
from typing import TYPE_CHECKING

from class_model_dsl.populate.pop_types import State_Model_i, Lifecycle_i

if TYPE_CHECKING:
    from tkinter import Tk

class StateModel:
    """
    Create a State Model relation
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def populate(cls, mmdb: 'Tk', sm):
        """Constructor"""

        cname = sm.lifecycle
        rnum = sm.assigner
        sm_name = cname if cname else rnum

        # Populate
        Transaction.open(mmdb)
        Relvar.insert(relvar='State_Model', tuples=[
            State_Model_i(Name=sm_name, Domain=sm.domain)
        ])
        if cname:
            cls._logger.info(f"Populating Lifecycle [{cname}]")
            Relvar.insert(relvar='Lifecycle', tuples=[
                Lifecycle_i(Class=cname, Domain=sm.domain)
            ])
            for s in sm.states:
                pass

        else:
            cls._logger.info(f"Populating Assigner [{rnum}]")