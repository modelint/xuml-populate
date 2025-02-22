"""
state_model.py – Process parsed lifecycle to p
"""

import logging
from xuml_populate.config import mmdb
from xsm_parser.state_model_parser import StateModel_a
from xuml_populate.exceptions.mp_exceptions import MismatchedStateSignature
from pyral.relvar import Relvar
from pyral.transaction import Transaction
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.signature import Signature
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.populate.mmclass_nt import State_Model_i, Lifecycle_i, \
    Non_Deletion_State_i, State_i, Real_State_i, Deletion_State_i, Initial_Pseudo_State_i, \
    State_Signature_i, Initial_Transition_i, \
    Event_Response_i, Transition_i, Non_Transition_i, \
    Event_Specification_i, Monomorphic_Event_Specification_i, Monomorphic_Event_i, \
    Effective_Event_i, Event_i, Parameter_i

ISP = 'Initial_Pseudo_State'  # Name of initial pseudo state

_logger = logging.getLogger(__name__)
tr_SM = 'State Model'


class StateModel:
    """
    Create a State Model relation
    """

    @classmethod
    def populate(cls, subsys: str, sm: StateModel_a):
        """Constructor"""

        cname = sm.lifecycle
        rnum = sm.assigner
        sm_name = cname if cname else rnum
        signums = {}  # Remember signature of each inserted state for processing transitions
        signatures = {}

        # Populate
        # It is easiest to create all events and states at once before checking constraints
        Transaction.open(mmdb, tr_SM)
        Relvar.insert(mmdb, tr=tr_SM, relvar='State_Model', tuples=[
            State_Model_i(Name=sm_name, Domain=sm.domain)
        ])
        if cname:  # Lifecycle state model
            _logger.info(f"Populating Lifecycle [{cname}]")
            Relvar.insert(mmdb, tr=tr_SM, relvar='Lifecycle', tuples=[
                Lifecycle_i(Class=cname, Domain=sm.domain)
            ])
            # Populate the states
            for s in sm.states:
                # Create Real State and all associated model elements
                Relvar.insert(mmdb, tr=tr_SM, relvar='State', tuples=[
                    State_i(Name=s.state.name, State_model=cname, Domain=sm.domain)
                ])
                # Create its Activity
                anum = Activity.populate_state(tr=tr_SM,
                                               state=s.state.name, subsys=subsys, actions=s.activity,
                                               state_model=cname, domain=sm.domain,
                                               )
                # Signature
                sig_params = frozenset(s.state.signature)
                if sig_params not in signatures:
                    # Add new signature if it doesn't exist
                    # First create signature superclass instance in Activity subsystem
                    signum = Signature.populate(tr=tr_SM, subsys=subsys, domain=sm.domain)
                    signatures[sig_params] = signum  # Save the SIGnum as a value, keyed to the frozen params
                    Relvar.insert(mmdb, tr=tr_SM, relvar='State_Signature', tuples=[
                        State_Signature_i(SIGnum=signum, State_model=cname, Domain=sm.domain)
                    ])
                    # Now we need to create Data Flows and Parameters
                    for p in s.state.signature:
                        # Create a Data flow
                        # Populate the Parameter's type if it hasn't already been populated
                        MMtype.populate_unknown(name=p.type, domain=sm.domain)
                        input_fid = Flow.populate_data_flow_by_type(mm_type=p.type, anum=anum,
                                                                    domain=sm.domain, label=None).fid
                        Relvar.insert(mmdb, tr=tr_SM, relvar='Parameter', tuples=[
                            Parameter_i(Name=p.name, Signature=signum, Domain=sm.domain,
                                        Input_flow=input_fid, Activity=anum, Type=p.type)
                        ])
                else:
                    # Otherwise, just get the id of the matching signature
                    signum = signatures[sig_params]
                Relvar.insert(mmdb, tr=tr_SM, relvar='Real_State', tuples=[
                    Real_State_i(Name=s.state.name, State_model=cname, Domain=sm.domain, Signature=signum,
                                 Activity=anum)
                ])
                # We need to look up the sid when matching events on incoming transitions
                signums[s.state.name] = signum
                if not s.state.deletion:
                    Relvar.insert(mmdb, tr=tr_SM, relvar='Non_Deletion_State', tuples=[
                        Non_Deletion_State_i(Name=s.state.name, State_model=cname, Domain=sm.domain)
                    ])
                else:
                    Relvar.insert(mmdb, tr=tr_SM, relvar='Deletion_State', tuples=[
                        Deletion_State_i(Name=s.state.name, Class=cname, Domain=sm.domain)
                    ])
        else:  # Assigner state model
            # TODO: Handle assigner state models
            _logger.info(f"Populating Assigner [{rnum}]")

        # Populate the events
        # TODO: Handle polymorphic events
        for ev_name in sm.events:
            Relvar.insert(mmdb, tr=tr_SM, relvar='Event', tuples=[
                Event_i(Name=ev_name, State_model=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(mmdb, tr=tr_SM, relvar='Effective_Event', tuples=[
                Effective_Event_i(Name=ev_name, State_model=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(mmdb, tr=tr_SM, relvar='Monomorphic_Event', tuples=[
                Monomorphic_Event_i(Name=ev_name, State_model=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(mmdb, tr=tr_SM, relvar='Monomorphic_Event_Specification', tuples=[
                Monomorphic_Event_Specification_i(Name=ev_name, State_model=sm_name, Domain=sm.domain)
            ])
            # Cannot create Event Specification until we process transitions to determine signature for at least
            # one target state

        # Populate the transitions
        inserted_especs = {}
        if sm.initial_transitions:
            # Create the intial pseudo state
            Relvar.insert(mmdb, tr=tr_SM, relvar=ISP, tuples=[
                Initial_Pseudo_State_i(Name=ISP, Class=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(mmdb, tr=tr_SM, relvar='State', tuples=[
                State_i(Name=ISP, State_model=sm_name, Domain=sm.domain)
            ])
        for t in sm.initial_transitions:
            Relvar.insert(mmdb, tr=tr_SM, relvar='Initial_Transition', tuples=[
                Initial_Transition_i(From_state=ISP, Class=sm_name, Domain=sm.domain, Event=t.event)
            ])
            signum = signums[t.to_state]
            Relvar.insert(mmdb, tr=tr_SM, relvar='Event_Specification', tuples=[
                Event_Specification_i(Name=t.event, State_model=sm_name, Domain=sm.domain,
                                      State_signature=signum)
            ])
            inserted_especs[t.event] = signum
            Relvar.insert(mmdb, tr=tr_SM, relvar='Event_Response', tuples=[
                Event_Response_i(State=ISP, Event=t.event, State_model=sm_name, Domain=sm.domain)
            ])
            Relvar.insert(mmdb, tr=tr_SM, relvar='Transition', tuples=[
                Transition_i(From_state=ISP, Event=t.event, State_model=sm_name, Domain=sm.domain,
                             To_state=t.to_state)
            ])
            for e in sm.events:
                if e != t.event:
                    Relvar.insert(mmdb, tr=tr_SM, relvar='Event_Response', tuples=[
                        Event_Response_i(State=ISP, Event=e, State_model=sm_name, Domain=sm.domain)
                    ])
                    Relvar.insert(mmdb, tr=tr_SM, relvar='Non_Transition', tuples=[
                        Non_Transition_i(State=ISP, Event=e, State_model=sm_name, Domain=sm.domain,
                                         Behavior='CH',
                                         Reason="Transition is only legal response from initial pseudo state")
                    ])

        for s in sm.states:
            if s.state.deletion:
                break  # There are no transitions out of a deletion state
            for t in s.transitions:
                if t.to_state:
                    # Insert or check event spec signature
                    if t.event not in inserted_especs:
                        # The event spec will assume the signature of the first target state encountered
                        signum = signums[t.to_state]
                        Relvar.insert(mmdb, tr=tr_SM, relvar='Event_Specification', tuples=[
                            Event_Specification_i(Name=t.event, State_model=sm_name, Domain=sm.domain,
                                                  State_signature=signum)
                        ])
                        inserted_especs[t.event] = signum  # Remember for matching in the else clause below
                    else:
                        # We need to verify that the to_state's signature matches that of the event spec
                        state_sig = signums[t.to_state]
                        espec_sig = inserted_especs[t.event]
                        if state_sig != espec_sig:
                            _logger.error(
                                f"Mismatched espec sig: <{t.event}:{espec_sig}> state sig: [{t.to_state}:{state_sig}]")
                            raise MismatchedStateSignature(event=t.event, state=t.to_state)
                    # Create transition event response
                    Relvar.insert(mmdb, tr=tr_SM, relvar='Event_Response', tuples=[
                        Event_Response_i(State=s.state.name, Event=t.event, State_model=sm_name, Domain=sm.domain)
                    ])
                    Relvar.insert(mmdb, tr=tr_SM, relvar='Transition', tuples=[
                        Transition_i(From_state=s.state.name, Event=t.event, State_model=sm_name, Domain=sm.domain,
                                     To_state=t.to_state)
                    ])
                else:  # Create Non Transition ignore response
                    Relvar.insert(mmdb, tr=tr_SM, relvar='Event_Response', tuples=[
                        Event_Response_i(State=s.state.name, Event=t.event, State_model=sm_name, Domain=sm.domain)
                    ])
                    Relvar.insert(mmdb, tr=tr_SM, relvar='Non_Transition', tuples=[
                        Non_Transition_i(State=s.state.name, Event=t.event, State_model=sm_name, Domain=sm.domain,
                                         Behavior='IGN', Reason="<none_specified>")
                    ])

        # All event specs have been created, now fill in the can't happens
        for s in sm.states:
            tr_ign_events = set(t.event for t in s.transitions)
            for e in sm.events:
                if e not in tr_ign_events:
                    Relvar.insert(mmdb, tr=tr_SM, relvar='Event_Response', tuples=[
                        Event_Response_i(State=s.state.name, Event=e, State_model=sm_name, Domain=sm.domain)
                    ])
                    ch_reason = "<none_specified>" if not s.state.deletion else "Event cannot happen in deletion state"
                    Relvar.insert(mmdb, tr=tr_SM, relvar='Non_Transition', tuples=[
                        Non_Transition_i(State=s.state.name, Event=e, State_model=sm_name, Domain=sm.domain,
                                         Behavior='CH', Reason=ch_reason)
                    ])

        Transaction.execute(mmdb, tr_SM)
