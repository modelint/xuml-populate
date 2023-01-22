"""
state_model.py – Populate a lifecycle instance into the metamodel
"""

import logging
from PyRAL.relvar import Relvar
from PyRAL.transaction import Transaction
from typing import TYPE_CHECKING

from class_model_dsl.populate.pop_types import State_Model_i, Lifecycle_i,\
    Non_Deletion_State_i, State_i, Real_State_i, Deletion_State_i, Initial_Pseudo_State_i

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
        Transaction.open(mmdb) # First transaction requires a Non Deletion State
        Relvar.insert(relvar='State_Model', tuples=[
            State_Model_i(Name=sm_name, Domain=sm.domain)
        ])
        if cname: # Lifecycle state model
            cls._logger.info(f"Populating Lifecycle [{cname}]")
            Relvar.insert(relvar='Lifecycle', tuples=[
                Lifecycle_i(Class=cname, Domain=sm.domain)
            ])
            pending_initial_nd_state = True # Transaction remains open until first Non Deletion State is added
            for s in sm.states:
                if not pending_initial_nd_state:  # We have executed a transaction to create the Lifecycle already
                    Transaction.open(mmdb)
                Relvar.insert(relvar='State', tuples=[
                    State_i(Name=s.name, State_model=cname, Domain=sm.domain)
                ])
                if s.type == 'creation':
                    Relvar.insert(relvar='Initial_Pseudo_State', tuples=[
                        Initial_Pseudo_State_i(Name=s.name, Class=cname, Domain=sm.domain)
                    ])
                else:
                    Relvar.insert(relvar='Real_State', tuples=[
                        Real_State_i(Name=s.name, State_model=cname, Domain=sm.domain)
                    ])
                    if s.type == 'non_deletion':
                        Relvar.insert(relvar='Non_Deletion_State', tuples=[
                            Non_Deletion_State_i(Name=s.name, State_model=cname, Domain=sm.domain)
                        ])
                        pending_initial_nd_state = False
                    else:
                        Relvar.insert(relvar='Deletion_State', tuples=[
                            Deletion_State_i(Name=s.name, Class=cname, Domain=sm.domain)
                        ])
                if not pending_initial_nd_state:
                    Transaction.execute() # Execute for each added state
        else: # Assigner state model
            cls._logger.info(f"Populating Assigner [{rnum}]")
