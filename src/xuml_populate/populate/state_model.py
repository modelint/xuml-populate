"""
state_model.py – Process parsed lifecycle to p
"""

# System
import logging
from enum import Enum
from typing import Tuple

# Model Integration
from xsm_parser.state_model_parser import StateModel_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction


# xUML Populate
from xuml_populate.populate.actions.aparse_types import SMType, Method_Output_Type
from xuml_populate.populate.state_activity import StateActivity
from xuml_populate.config import mmdb
from xuml_populate.exceptions.mp_exceptions import MismatchedStateSignature, BadStateModelName
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.signature import Signature
from xuml_populate.populate.activity import Activity
from xuml_populate.populate.mm_type import MMtype
from xuml_populate.names import IPS_name
from xuml_populate.populate.mmclass_nt import (State_Model_i, Lifecycle_i, Non_Deletion_State_i, State_i, Real_State_i,
                                               Deletion_State_i, Initial_Pseudo_State_i, State_Signature_i,
                                               Initial_Transition_i, Event_Response_i, Transition_i, Non_Transition_i,
                                               Event_Specification_i, Monomorphic_Event_Specification_i,
                                               Monomorphic_Event_i, Effective_Event_i, Event_i, Parameter_i, Assigner_i,
                                               Multiple_Assigner_i, Single_Assigner_i)

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)
tr_SM = 'State Model'

class StateModel:
    """
    Create a State Model relation
    """

    def __init__(self, subsys: str, sm: StateModel_a, parse_actions: bool):
        """Constructor"""

        self.cname = sm.lifecycle
        self.rnum = sm.assigner_rnum
        # Ensure that only cname or rnum is set
        if not self.cname and not self.rnum:
            msg = f"No state model rnum or class name specified"
            _logger.exception(msg)
            raise BadStateModelName(msg)
        if self.cname and self.rnum:
            msg = f"State model must be either lifecycle (cname) or assigner (rnum), not both"
            _logger.exception(msg)
            raise BadStateModelName(msg)
        self.pclass = sm.assigner_pclass  # Establishes a multiple assigner with a partitioning class
        self.sm_name = self.cname if self.cname else self.rnum
        self.signums = {}  # Remember signature of each inserted state for processing transitions
        self.signatures = {}
        self.parse_actions = parse_actions
        self.states: dict[str, dict] = {}
        self.domain = sm.domain

        # Populate
        # It is easiest to create all events and states at once before checking constraints
        Transaction.open(db=mmdb, name=tr_SM)
        Relvar.insert(db=mmdb, tr=tr_SM, relvar='State Model', tuples=[
            State_Model_i(Name=self.sm_name, Domain=sm.domain)
        ])
        if self.cname:  # Lifecycle state model
            self.sm_type = SMType.LIFECYCLE
            _logger.info(f"Populating Lifecycle [{self.cname}]")
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Lifecycle', tuples=[
                Lifecycle_i(Class=self.cname, Domain=sm.domain)
            ])
        else:  # Assigner state model
            _logger.info(f"Populating Assigner [{self.rnum}]")
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Assigner', tuples=[
                Assigner_i(Rnum=self.rnum, Domain=sm.domain)
            ])
            if self.pclass:
                # Multiple assigner with a partitioning class
                self.sm_type = SMType.MA
                Relvar.insert(db=mmdb, tr=tr_SM, relvar='Multiple Assigner', tuples=[
                    Multiple_Assigner_i(Rnum=self.rnum, Partitioning_class=self.pclass, Domain=sm.domain)
                ])
            else:
                # Single assigner
                self.sm_type = SMType.SA
                Relvar.insert(db=mmdb, tr=tr_SM, relvar='Single Assigner', tuples=[
                    Single_Assigner_i(Rnum=self.rnum, Domain=sm.domain)
                ])

        # Populate the states
        for s in sm.states:
            pass
            # Create Real State and all associated model elements
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='State', tuples=[
                State_i(Name=s.state.name, State_model=self.sm_name, Domain=sm.domain)
            ])
            # Create its Activity
            state_info = Activity.populate_state(
                tr=tr_SM, subsys=subsys, actions=s.activity,
                state_model=self.sm_name, domain=sm.domain,
                parse_actions=self.parse_actions, sm_type=self.sm_type)
            self.states[s.state.name] = state_info
            anum = state_info["anum"]

            # Signature
            sig_params = frozenset(s.state.signature)
            shared_sig = False
            if sig_params not in self.signatures:
                # Add new signature if it doesn't exist
                # First create signature superclass instance in Activity subsystem
                signum = Signature.populate(tr=tr_SM, domain=sm.domain)
                self.signatures[sig_params] = signum  # Save the SIGnum as a value, keyed to the frozen params
                Relvar.insert(db=mmdb, tr=tr_SM, relvar='State Signature', tuples=[
                    State_Signature_i(SIGnum=signum, State_model=self.sm_name, Domain=sm.domain)
                ])
            else:
                shared_sig = True
                # Otherwise, just get the id of the matching signature
                signum = self.signatures[sig_params]

            # Now we need to create Data Flows and Parameters
            for p in s.state.signature:
                # Create a Data flow
                # Populate the Parameter's type if it hasn't already been populated
                MMtype.populate_unknown(name=p.type, domain=sm.domain)
                if not shared_sig:
                    # We populate Parameters only if this is a new Signature
                    Relvar.insert(db=mmdb, tr=tr_SM, relvar='Parameter', tuples=[
                        Parameter_i(Name=p.name, Signature=signum, Domain=sm.domain, Type=p.type)
                    ])
                input_fid = Flow.populate_data_flow_by_type(mm_type=p.type, anum=anum,
                                                            domain=sm.domain, label=p.name,
                                                            activity_tr=tr_SM).fid
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Real State', tuples=[
                Real_State_i(Name=s.state.name, State_model=self.sm_name, Domain=sm.domain, Signature=signum,
                             Activity=anum)
            ])
            # We need to look up the sid when matching events on incoming transitions
            self.signums[s.state.name] = signum
            if self.rnum or self.cname and not s.state.deletion:
                # Assigner cannot have a Deletion State
                Relvar.insert(db=mmdb, tr=tr_SM, relvar='Non Deletion State', tuples=[
                    Non_Deletion_State_i(Name=s.state.name, State_model=self.sm_name, Domain=sm.domain)
                ])
            else:
                Relvar.insert(db=mmdb, tr=tr_SM, relvar='Deletion State', tuples=[
                    Deletion_State_i(Name=s.state.name, Class=self.cname, Domain=sm.domain)
                ])

        # Populate the events
        # TODO: Handle polymorphic events
        for ev_name in sm.events:
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Event', tuples=[
                Event_i(Name=ev_name, State_model=self.sm_name, Domain=sm.domain)
            ])
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Effective Event', tuples=[
                Effective_Event_i(Name=ev_name, State_model=self.sm_name, Domain=sm.domain)
            ])
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Monomorphic Event', tuples=[
                Monomorphic_Event_i(Name=ev_name, State_model=self.sm_name, Domain=sm.domain)
            ])
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Monomorphic Event Specification', tuples=[
                Monomorphic_Event_Specification_i(Name=ev_name, State_model=self.sm_name, Domain=sm.domain)
            ])
            # Cannot create Event Specification until we process transitions to determine signature for at least
            # one target state

        # Populate the transitions
        inserted_especs = {}
        if sm.initial_transitions:
            # Create a Delegated Creation Activity
            # We set the actions to an empty string since they will generated later
            state_info = Activity.populate_state(
                tr=tr_SM, subsys=subsys, actions='',
                state_model=self.sm_name, domain=sm.domain,
                parse_actions=self.parse_actions, sm_type=self.sm_type, initial_pseudo_state=True)
            self.states[IPS_name] = state_info
            dc_anum = state_info["anum"]  # Delegated Creation Activity anum
            # Create the intial pseudo state
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Initial Pseudo State', tuples=[
                Initial_Pseudo_State_i(Name=IPS_name, Class=self.sm_name, Domain=sm.domain, Creation_activity=dc_anum)
            ])
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='State', tuples=[
                State_i(Name=IPS_name, State_model=self.sm_name, Domain=sm.domain)
            ])
        for t in sm.initial_transitions:
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Initial Transition', tuples=[
                Initial_Transition_i(From_state=IPS_name, Class=self.sm_name, Domain=sm.domain, Event=t.event)
            ])
            signum = self.signums[t.to_state]
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Event Specification', tuples=[
                Event_Specification_i(Name=t.event, State_model=self.sm_name, Domain=sm.domain,
                                      State_signature=signum)
            ])
            inserted_especs[t.event] = signum
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Event Response', tuples=[
                Event_Response_i(State=IPS_name, Event=t.event, State_model=self.sm_name, Domain=sm.domain)
            ])
            Relvar.insert(db=mmdb, tr=tr_SM, relvar='Transition', tuples=[
                Transition_i(From_state=IPS_name, Event=t.event, State_model=self.sm_name, Domain=sm.domain,
                             To_state=t.to_state)
            ])
            for e in sm.events:
                if e != t.event:
                    Relvar.insert(db=mmdb, tr=tr_SM, relvar='Event Response', tuples=[
                        Event_Response_i(State=IPS_name, Event=e, State_model=self.sm_name, Domain=sm.domain)
                    ])
                    Relvar.insert(db=mmdb, tr=tr_SM, relvar='Non Transition', tuples=[
                        Non_Transition_i(State=IPS_name, Event=e, State_model=self.sm_name, Domain=sm.domain,
                                         Behavior='CH',
                                         Reason="Transition is only legal response from "
                                                "initial_pseudo_state pseudo state")
                    ])

        for s in sm.states:
            if s.state.deletion:
                break  # There are no transitions out of a deletion state
            for t in s.transitions:
                if t.to_state:
                    # Insert or check event spec signature
                    if t.event not in inserted_especs:
                        # The event spec will assume the signature of the first target state encountered
                        signum = self.signums[t.to_state]
                        Relvar.insert(db=mmdb, tr=tr_SM, relvar='Event Specification', tuples=[
                            Event_Specification_i(Name=t.event, State_model=self.sm_name, Domain=sm.domain,
                                                  State_signature=signum)
                        ])
                        inserted_especs[t.event] = signum  # Remember for matching in the else clause below
                    else:
                        # We need to verify that the to_state's signature matches that of the event spec
                        state_sig = self.signums[t.to_state]
                        espec_sig = inserted_especs[t.event]
                        if state_sig != espec_sig:
                            _logger.error(
                                f"Mismatched espec sig: <{t.event}:{espec_sig}> state sig: [{t.to_state}:{state_sig}]")
                            raise MismatchedStateSignature(event=t.event, state=t.to_state)
                    # Create transition event response
                    Relvar.insert(db=mmdb, tr=tr_SM, relvar='Event Response', tuples=[
                        Event_Response_i(State=s.state.name, Event=t.event, State_model=self.sm_name, Domain=sm.domain)
                    ])
                    Relvar.insert(db=mmdb, tr=tr_SM, relvar='Transition', tuples=[
                        Transition_i(From_state=s.state.name, Event=t.event, State_model=self.sm_name, Domain=sm.domain,
                                     To_state=t.to_state)
                    ])
                else:  # Create Non Transition ignore response
                    Relvar.insert(db=mmdb, tr=tr_SM, relvar='Event Response', tuples=[
                        Event_Response_i(State=s.state.name, Event=t.event, State_model=self.sm_name, Domain=sm.domain)
                    ])
                    Relvar.insert(db=mmdb, tr=tr_SM, relvar='Non Transition', tuples=[
                        Non_Transition_i(State=s.state.name, Event=t.event, State_model=self.sm_name, Domain=sm.domain,
                                         Behavior='IGN', Reason="<none_specified>")
                    ])

        # All event specs have been created, now fill in the can't happens
        for s in sm.states:
            tr_ign_events = set(t.event for t in s.transitions)
            for e in sm.events:
                if e not in tr_ign_events:
                    Relvar.insert(db=mmdb, tr=tr_SM, relvar='Event Response', tuples=[
                        Event_Response_i(State=s.state.name, Event=e, State_model=self.sm_name, Domain=sm.domain)
                    ])
                    ch_reason = "<none_specified>" if not s.state.deletion else "Event cannot happen in deletion state"
                    Relvar.insert(db=mmdb, tr=tr_SM, relvar='Non Transition', tuples=[
                        Non_Transition_i(State=s.state.name, Event=e, State_model=self.sm_name, Domain=sm.domain,
                                         Behavior='CH', Reason=ch_reason)
                    ])

        Transaction.execute(db=mmdb, name=tr_SM)

    def process_states(self, method_output_types: dict[str, Method_Output_Type]):
        """
        """
        for name, s_data in self.states.items():
            sa = StateActivity(state_name=name, state_model=self, state_parse=s_data,
                               method_output_types=method_output_types)
            pass

