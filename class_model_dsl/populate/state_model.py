"""
state_model.py – Populate a lifecycle instance into the metamodel
"""

import logging
from PyRAL.relvar import Relvar
from PyRAL.transaction import Transaction
from typing import TYPE_CHECKING

from class_model_dsl.populate.pop_types import State_Model_i, Lifecycle_i,\
    Non_Deletion_State_i, State_i, Real_State_i, Deletion_State_i, Initial_Pseudo_State_i,\
    State_Signature_i, State_Parameter_i,\
    Event_Specification_i, Monomorphic_Event_Specification_i, Monomorphic_Event_i,\
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
        Transaction.open(mmdb) # It is easiest to create all events and states at once before checking constraints
        Relvar.insert(relvar='State_Model', tuples=[
            State_Model_i(Name=sm_name, Domain=sm.domain)
        ])
        if cname: # Lifecycle state model
            cls._logger.info(f"Populating Lifecycle [{cname}]")
            Relvar.insert(relvar='Lifecycle', tuples=[
                Lifecycle_i(Class=cname, Domain=sm.domain)
            ])
            # Populate the states
            # TODO: Create State parameters and state signature properly
            signatures = {}
            sig_id_counter = 1
            for s in sm.states:
                Relvar.insert(relvar='State', tuples=[
                    State_i(Name=s.state.name, State_model=cname, Domain=sm.domain)
                ])
                sig_params = frozenset(s.state.signature)
                if sig_params not in signatures.keys():
                    # Add new signature if it doesn't exist
                    sid = sig_id_counter
                    sig_id_counter += 1
                    signatures[sig_params] = sid
                    Relvar.insert(relvar='State_Signature', tuples=[
                        State_Signature_i(ID=sid, State_model=cname, Domain=sm.domain)
                    ])
                else:
                    # Otherwise, just get the id of the matching signature
                    sid = signatures[sig_params]
                Relvar.insert(relvar='Real_State', tuples=[
                    Real_State_i(Name=s.state.name, State_model=cname, Domain=sm.domain, Signature=sid)
                ])
                if not s.state.deletion:
                    Relvar.insert(relvar='Non_Deletion_State', tuples=[
                        Non_Deletion_State_i(Name=s.state.name, State_model=cname, Domain=sm.domain)
                    ])
                else:
                    Relvar.insert(relvar='Deletion_State', tuples=[
                        Deletion_State_i(Name=s.state.name, Class=cname, Domain=sm.domain)
                    ])
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
            if espec.signature:
                for p in espec.signature:
                    Transaction.open(mmdb)
                    Relvar.insert(relvar='Event_Parameter', tuples=[
                        Event_Parameter_i(Name=p.name, Event_specification=espec.name, Type=p.type,
                                          State_model=sm_name, Domain=sm.domain)
                    ])

        # Populate the transitions
        for s in sm.states:
            for t in s.transitions:
                pass


        Transaction.execute()
