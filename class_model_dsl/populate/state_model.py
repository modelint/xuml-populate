"""
state_model.py – Populate a lifecycle instance into the metamodel
"""

import logging
from class_model_dsl.mp_exceptions import MismatchedStateSignature
from PyRAL.relvar import Relvar
from PyRAL.transaction import Transaction
from typing import TYPE_CHECKING
from class_model_dsl.populate.pop_types import State_Model_i, Lifecycle_i,\
    Non_Deletion_State_i, State_i, Real_State_i, Deletion_State_i, Initial_Pseudo_State_i,\
    State_Signature_i, State_Parameter_i,\
    Event_Response_i, Transition_i, Non_Transition_i,\
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
        sigids = {}  # Remember signature of each inserted state for processing transitions
        signatures = {}

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
                    for p in s.state.signature:
                        Relvar.insert(relvar='State_Parameter', tuples=[
                            State_Parameter_i(Name=p.name, Signature=sid, State_model=cname, Domain=sm.domain, Type=p.type)
                        ])
                else:
                    # Otherwise, just get the id of the matching signature
                    sid = signatures[sig_params]
                Relvar.insert(relvar='Real_State', tuples=[
                    Real_State_i(Name=s.state.name, State_model=cname, Domain=sm.domain, Signature=sid)
                ])
                sigids[s.state.name] = sid # We need to look up the sid when matching events on incoming transitions
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
            Relvar.insert(relvar='Event', tuples=[
                Event_i(Name=espec.name, State_model=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(relvar='Effective_Event', tuples=[
                Effective_Event_i(Name=espec.name, State_model=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(relvar='Monomorphic_Event', tuples=[
                Monomorphic_Event_i(Name=espec.name, State_model=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(relvar='Monomorphic_Event_Specification', tuples=[
                Monomorphic_Event_Specification_i(Name=espec.name, State_model=sm_name, Domain=sm.domain)
            ])
            # Cannot create Event Specification until we process transitions to determine signature for at least
            # one target state

        # Populate the transitions
        inserted_especs = {}
        for s in sm.states:
            for t in s.transitions:
                if t.to_state:
                    # Insert or check event spec signature
                    if t.event not in inserted_especs.keys():
                        # The event spec will assume the signature of the first target state encountered
                        sid = sigids[t.to_state]
                        Relvar.insert(relvar='Event_Specification', tuples=[
                            Event_Specification_i(Name=t.event, State_model=sm_name, Domain=sm.domain,
                                                  State_signature=sid)
                        ])
                        inserted_especs[t.event] = sid  # Remember for matching in the else clause below
                    else:
                        # We need to verify that the to_state's signature matches that of the event spec
                        state_sig = sigids[t.to_state]
                        espec_sig = inserted_especs[t.event]
                        if state_sig != espec_sig:
                            cls._logger.error(f"Mismatched espec sig: <{t.event}:{espec_sig}> state sig: [{t.to_state}:{state_sig}]")
                            raise MismatchedStateSignature(event=t.event, state=t.to_state)
                    # Create transition event response
                    Relvar.insert(relvar='Event_Response', tuples=[
                        Event_Response_i(State=s.state.name, Event=t.event, State_model=sm_name, Domain=sm.domain)
                    ])
                    Relvar.insert(relvar='Transition', tuples=[
                        Transition_i(From_state=s.state.name, Event=t.event, State_model=sm_name, Domain=sm.domain, To_state=t.to_state)
                    ])
                else: # Create Non Transition ignore response
                    Relvar.insert(relvar='Non_Transition', tuples=[
                        Non_Transition_i(State=s.state.name, Event=t.event, State_model=sm_name, Domain=sm.domain, Behavior='IGN', Reason="<none_specified>")
                    ])


                        # Verify that to_state signature and
                    pass


        Transaction.execute()