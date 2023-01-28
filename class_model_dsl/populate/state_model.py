"""
state_model.py – Populate a lifecycle instance into the metamodel
"""

import logging
from PyRAL.relvar import Relvar
from PyRAL.transaction import Transaction
from typing import TYPE_CHECKING

from class_model_dsl.populate.pop_types import State_Model_i, Lifecycle_i,\
    Non_Deletion_State_i, State_i, Real_State_i, Deletion_State_i, Initial_Pseudo_State_i,\
    Event_Parameter_i, Event_Specification_i, Monomorphic_Event_Specification_i, Monomorphic_Event_i,\
    Effective_Event_i, Event_i

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
            # Populate the states
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
            # TODO: Handle assigner state models
            cls._logger.info(f"Populating Assigner [{rnum}]")

        # Populate the events
        # TODO: Handle polymorphic events
        for espec in sm.events.values():
            Transaction.open(mmdb)
            Relvar.insert(relvar='Event', tuples=[
                Event_i(Name=espec.name, State_model=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(relvar='Effective_Event', tuples=[
                Effective_Event_i(Name=espec.name, State_model=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(relvar='Monomorphic_Event', tuples=[
                Monomorphic_Event_i(Name=espec.name, State_model=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(relvar='Event_Specification', tuples=[
                Event_Specification_i(Name=espec.name, State_model=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(relvar='Monomorphic_Event_Specification', tuples=[
                Monomorphic_Event_Specification_i(Name=espec.name, State_model=sm_name, Domain=sm.domain)
            ])
            Transaction.execute()
            if espec.signature:
                for p in espec.signature:
                    Transaction.open(mmdb)
                    Relvar.insert(relvar='Event_Parameter', tuples=[
                        Event_Parameter_i(Name=p.name, Event_specification=espec.name, Type=p.type,
                                          State_model=sm_name, Domain=sm.domain)
                    ])
                    Transaction.execute()

        # Populate the transitions
        for s in sm.states:
            for t in s.transitions:
                pass
