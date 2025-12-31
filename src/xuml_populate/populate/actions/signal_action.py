"""
signal_action.py – Populate a signal action instance in PyRAL
"""

# System
import logging
from typing import TYPE_CHECKING, Optional

# Model Integration
from scrall.parse.visitor import Signal_a, External_Signal_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

from xuml_populate.exceptions.action_exceptions import ActionException, IncompleteActionException

# xUML populate
if __debug__:
    from xuml_populate.utility import print_mmdb

if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity

from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.names import IPS_name  # Initial pseudo-state name
from xuml_populate.populate.delegated_creation import DelegatedCreationActivity
from xuml_populate.populate.actions.expressions.enumflow import EnumFlow
from xuml_populate.populate.actions.aparse_types import Boundary_Actions, SMType
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.populate.flow import Flow_ap
from xuml_populate.populate.actions.gate_action import GateAction
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.mmclass_nt import (
    Signal_Action_i, Supplied_Parameter_Value_i, Signal_Instance_Action_i, Delivery_Time_i,
    Multiple_Assigner_Partition_Instance_i, Signal_Assigner_Action_i, Instance_Action_i, Initial_Signal_Action_i,
    Signal_Completion_Action_i, Signal_Instance_Action_i, Cancel_Delayed_Signal_Action_i, Signaled_Creation_i,
    Send_Signal_Action_i, External_Service_i, External_Signal_Action_i, External_Event_i, External_Signal_Parameter_i
)

_logger = logging.getLogger(__name__)

# Transactions
tr_Signal = "Signal Action"

class SignalAction:
    """
    Populate all Signal Action subsystem model elements
    """
    def __init__(self, statement_parse: Signal_a | External_Signal_a, activity: 'Activity'):
        """
        Initialize with everything the Signal statement requires

        Args:
            statement_parse: Parsed representation of the Signal statement
            activity: The enclosing Activity object
        """
        self.external_dest = type(statement_parse).__name__ == 'External_Signal_a'
        # Ensure that this is a state model activity
        # Signals may only be issued by State Activities
        if not activity.state_model:
            msg = f"Only a State Activity can send a signal. Signal action encounterd in: {self.activity.path}"
            _logger.error(msg)
            ActionException(msg)
        self.event_name = statement_parse.event  # Event specification name
        self.action_id = None  # Assigned during population of Action
        self.statement_parse = statement_parse  # The parsed Scrall signal statement
        self.target_iset = None if self.external_dest else statement_parse.dest.target_iset  # The destination parse, if any of this Action

        self.activity = activity  # The enclosing Activity object
        self.anum = activity.anum
        self.domain = activity.domain
        # xiflow for Lifecycle or Method, piflow for Multiple Assigner, or None for Single Assigner
        self.input_instance_flow = activity.xiflow if activity.xiflow is not None else activity.piflow

        # If this is a self directed signal, set the destination and status
        self.self_directed = False  # Status set for convenient future reference
        self.dest_sm = None  # Determined during population if not to self
        if self.target_iset is not None and type(self.target_iset).__name__ == 'N_a' and self.target_iset.name == 'me':
            self.dest_sm = activity.state_model
            self.self_directed = True

        # These are set during population
        self.dest_iflow = None
        self.parameter_values = None
        self.delay_sflow = None
        self.aids_in: set[str] = set()
        self.aids_out: set[str] = set()
        self.action_id: str = None
        self.signal_dest = None
        self.dest_sig = None
        self.initial_signal_action = False  # Default assumption

        # Does this signal delegate creation of a new instance?
        # If so, it's an Initial Signal Action  (asynchronous creation)
        if type(self.target_iset).__name__ == "INST_a":
            if len(self.target_iset.components) == 1 and type(self.target_iset.components[0]).__name__ == 'New_inst_a':
                self.initial_signal_action = True

    def populate(self) -> Boundary_Actions:
        """
        Populate the Signal Action based on the provided initialization data

        Returns:
            Boundary_Actions: The signal action id is both the initial_pseudo_state and final action id
        """
        # TODO: Fix Boundary_Actions comment above

        # Initiate the Signal Action transaction
        Transaction.open(db=mmdb, name=tr_Signal)

        # Populate the Action superclass instance and obtain its action_id
        self.action_id = Action.populate(tr=tr_Signal, anum=self.anum, domain=self.domain, action_type="signal")

        self.populate_subclass()

        # We return the upstream aids as ain and our signal acction as the aout
        return Boundary_Actions(ain=self.aids_in, aout={self.action_id})

    def populate_subclass(self):
        """
        Branch to the appropriate population method for the specific Signal Action subclass
        """
        # External signal (mapped to service outside our domain)
        if self.external_dest:
            self.populate_external_signal()  # No returned destination
            return

        # Cancel Delayed Signal Action
        if self.statement_parse.dest.cancel:
            self.populate_cancel_delayed_signal_action()
            return

        # Initial Signal Action (asynchronous creation)
        if self.initial_signal_action:
            self.populate_initial_signal()  # Returned destination is the target class name
            return

        # Signal Completion Action
        # If the destination is 'me' with no delay specified, this is a Signal Completion Action
        if self.self_directed and not self.statement_parse.dest.delay:
            self.populate_signal_completion_action()
            return

        # Signal Assigner Action
        # Check for invalid parse
        if self.target_iset and self.statement_parse.dest.assigner_dest:
            # Only one of these two should be set
            msg = (f"Instance set and assigner destinations are mutually exclusive as a signal destination.\n"
                   f"But both have been specified for signal {self.event_name} in {self.activity.activity_path}")
            _logger.error(msg)
            raise ActionException(msg)

        if self.statement_parse.dest.assigner_dest:
            self.process_signal_assigner_action()
            return

        # Signal Instance Action
        # The target is a Lifecycle
        # A distinct signal may be generated for each target instance, but they all target the same lifecycle
        # so there is still only one destination State Model
        if self.target_iset:
            self.process_signal_instance_action()
            return

        # No recognized subclass
        msg = (f"Unrecognized signal action subclass defined for event {self.event_name} in:"
               f" {self.activity.activity_path}")
        _logger.error(msg)
        raise ActionException(msg)

    def populate_external_signal(self):
        """
        Populate an External Event
        (will be mapped to an external service in some other Domain through implicit bridging)
        """
        # Validate the External Event and lookup the signature
        R = f"Name:<{self.event_name}>, Domain:<{self.domain}>"
        external_event_r = Relation.restrict(db=mmdb, relation="External Event", restriction=R)
        if not external_event_r.body:
            msg = f"External Event {self.domain}::{self.event_name} not defined in: {self.activity.activity_path}"
            _logger.error(msg)
            raise ActionException(msg)
        # We need the External Signature number so we can populate any supplied params
        external_service_r = Relation.semijoin(db=mmdb, rname2='External Service')
        signum = external_service_r.body[0]['Signature']
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='External Signal Action', tuples=[
                External_Signal_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                         External_event=self.event_name)
            ])

        # Populate any parameters in the External Signature
        param_r = Relation.semijoin(db=mmdb, rname2='Parameter', attrs={'Signature': 'Signature', 'Domain': 'Domain'})
        sig_params = {t["Name"]: t["Type"] for t in param_r.body}
        if sig_params:
            self.populate_ext_sig_params()

        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])

        # TODO: Delayed external events not yet supported, requires Delivery Time from Signal Instance Action

        Transaction.execute(db=mmdb, name=tr_Signal)


    def populate_cancel_delayed_signal_action(self):
        """
        Populate a Cancel Delayed Signal Action
        """
        dest_iflow = self.find_dest_flow()
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Cancel Delayed Signal Action', tuples=[
            Cancel_Delayed_Signal_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                           Instance_flow=dest_iflow.fid)
        ])
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Action', tuples=[
            Signal_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])

        # The boundary actions are always just this one signal action id
        self.aids_in.add(self.action_id)
        self.aids_out.add(self.action_id)

    def populate_initial_signal(self):
        """
        Populate an Initial Signal Action

        This is a signal that delegates creation of an instance to a target class
        (asynchronous creation)

        Returns:
            Destination state model name which must be a class since an instance will be created
        """
        # Create a Delegated Creation Activity associated with the target class Initial Pseudo State
        # It will populate itself based on the informaiton in the statement_parse

        # Grab the parse of the destination, initial attributes and references
        new_inst_parse = self.target_iset.components[0]
        ref_inits: dict[str, list[str]] = {}  # Flows with references keyed by rnum

        # An instance of the dest_class will be created via delegation
        # It must have a lifecycle with an initial psuedo state
        dest_class = new_inst_parse.cname.name
        self.dest_sm = dest_class

        # We need to break down any scalar expressions in the non-referential attribute flows
        attr_init_flows: dict[str, str] = {}
        attr_init_exprs = {a.attr.name: a.scalar_expr for a in new_inst_parse.attrs}
        for attr_name, attr_expr in attr_init_exprs.items():
            expr_type = type(attr_expr).__name__
            match expr_type:
                case 'Enum_a':
                    e = EnumFlow(parse=attr_expr, activity=self.activity)
                    ef = e.populate_attr_assignment(attr_name=attr_name, class_name=dest_class)
                    attr_init_flows[attr_name] = ef.fid
                case _:
                    # se = ScalarExpr(expr=attr_expr, input_instance_flow=None, activity=self.activity)
                    # b, sflows = se.process()
                    pass

        # We need to break down any instance sets in the to_refs
        for ref in new_inst_parse.rels:
            # ref holds one or two references that formalize a relationship
            # one if its a simple association or generalization and two if it is associative
            # A reference is a single instance flow that is either already populated in our activity
            # or we need to create it and any required Actions that produce the flow

            # Create list of one or two parsed out single-instance set references
            # Start with iset1 which must always have a value, i.e. a relationship requires at least one reference
            if not ref.iset1:
                msg = f"No reference instance set for event: {self.event_name} in {self.activity.activity_path}"
                _logger.error(msg)
                raise ActionException(msg)
            iset_parses = [ref.iset1, ref.iset2] if ref.iset2 else [ref.iset1]
            ref_inits[ref.rnum.rnum] = []
            for ip in iset_parses:
                if type(ip).__name__ == 'N_a':
                    # The reference is just the name of a non scalar flow already populated in our activity
                    # InstanceSet will expect a list of components, so we'll just make this a single component list
                    iset_comps = [ip]
                    # After processing the InstanceSet below we'll obtain one ns flow and zero actions (ain,aout)
                    # empty sets for ain, aout and the matching ns_flow already
                    # populated in this Activity
                else:
                    # TODO: <1> Test this when we have an example
                    iset_comps = ip # Should be a list of components
                iset = InstanceSet(iset_components=iset_comps, activity=self.activity)
                ain, aout, f = iset.process()
                # Add the flow id holding the reference to the ref1 slot for the rnum
                ref_inits[ref.rnum.rnum].append(f.fid)
                # TODO: <1> Figure out what to do about ain, aout for else case above

        # Now we just need to populate the Initial Signal Action itself
        # Since all the heavy lifting happens in the creation activity, there isn't much to do here
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Initial Signal Action', tuples=[
            Initial_Signal_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                    Class=dest_class, Pseudo_state=IPS_name)
        ])
        # Look up the Initial Pseudo State and get the associated activity number
        R = f"Class:<{dest_class}>, Domain:<{self.domain}>"
        ip_state_r = Relation.restrict(db=mmdb, relation='Initial Pseudo State', restriction=R)
        if len(ip_state_r.body) != 1:
            msg = f"Single initial_pseudo_state Pseudo State for Lifecycle: [{self.class_name}] not defined in metamodel"
            _logger.error(msg)
            raise ActionException(msg)
        creation_activity_anum = ip_state_r.body[0]["Creation_activity"]

        # The Initial Signal Action is signaling this Delegated Creation Activity
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signaled Creation', tuples=[
            Signaled_Creation_i(Signal_action=self.action_id, Signal_activity=self.anum,
                                Domain=self.domain, Creation_activity=creation_activity_anum)
        ])
        # The boundary actions are always just this one signal action id
        self.aids_in.add(self.action_id)
        self.aids_out.add(self.action_id)

        self.complete_send_signal_transaction()

        DelegatedCreationActivity(signal_action=self.action_id, signal_activity=self.activity,
                                  creation_activity_anum=creation_activity_anum,
                                  class_name=dest_class, attr_init_flows=attr_init_flows, ref_inits=ref_inits)

    def find_dest_flow(self) -> Optional[Flow_ap]:
        """
        Find the populated Instance Flow supplying the parsed target destination and return its summary.

        Returns:
            Summary of the destination flow or None if not found or its a completion event
        """
        if self.self_directed:
            return self.input_instance_flow
        iset_type = type(self.target_iset).__name__
        match iset_type:
            case 'N_a' | 'IN_a':
                iset = InstanceSet(input_instance_flow=self.input_instance_flow,
                                   iset_components=[self.target_iset],
                                   activity=self.activity)
                _, _, dest_flow = iset.process()
                if not dest_flow:
                    msg = (f"Cound not find destination flow: [{self.target_iset.name}] for Signal Instance Set Action "
                           f"in {self.activity.activity_path}")
                    _logger.error(msg)
                    raise ActionException(msg)
                self.dest_sm = dest_flow.tname
                self.aids_in.add(self.action_id)
                # self.aids_out.add(self.action_id)
                return dest_flow
            case 'INST_a':
                iset = InstanceSet(input_instance_flow=self.activity.xiflow,
                                   iset_components=self.target_iset.components,
                                   activity=self.activity)
                ain, aout, dest_flow = iset.process()
                self.dest_sm = dest_flow.tname
                self.aids_in.add(ain)
                # self.aids_out.add(aout)
                return dest_flow
            case _:
                msg = f"Unimplemented or undefined instance set in: {self.activity.activity_path}"
                _logger.error(msg)
                raise ActionException(msg)

    def process_signal_instance_action(self):
        """
        """
        # An instance set destination was specified, so a signal will be sent to each instance in the set
        dest_iflow = self.find_dest_flow()

        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Instance Action', tuples=[
            Signal_Instance_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                     Instance_flow=dest_iflow.fid)
        ])

        self.complete_send_signal_transaction()

    def process_signal_assigner_action(self):
        """
        """
        dest_sm = self.statement_parse.dest.assigner_dest.rnum.rnum
        pi_flow = None
        # The signal will be addressed to an assigner state machine associated with a target association
        # Verify that the rnum is in fact an association (not an ordinal or a generalization relationship)

        # It's a safe assumption that we're signaling an assigner from a lifecycle state machine or a method
        # So we should have an xi flow
        if not self.activity.xiflow:
            msg = (f"Handle case where an assigner is sending a signal to another assigner "
                   f"at {self.activity.activity_path}")
            _logger.error(msg)
            raise IncompleteActionException(msg)
            # TODO: Handle case where an assigner is sending a signal to another assigner

        iset = InstanceSet(input_instance_flow=self.activity.xiflow,
                           iset_components=self.statement_parse.dest.assigner_dest.partition.components,
                           activity=self.activity)
        ain, aout, f = iset.process()
        self.aids_in.add(ain)
        self.aids_out.add(aout)

        # If the destination is a Multiple Assigner, populate the partition instance
        R = f"Rnum:<{dest_sm}>, Domain:<{self.domain}>"
        multiple_assigner_r = Relation.restrict(db=mmdb, relation="Multiple Assigner", restriction=R)
        if multiple_assigner_r.body:
            Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Multiple Assigner Partition Instance', tuples=[
                Multiple_Assigner_Partition_Instance_i(Action=self.action_id, Activity=self.anum,
                                                       Domain=self.domain,
                                                       Partition=f.fid)
            ])

        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Assigner Action', tuples=[
            Signal_Assigner_Action_i(ID=self.action_id, Activity=self.anum,
                                     Domain=self.domain,
                                     Association=dest_sm)
        ])
        self.dest_sm = dest_sm

        self.complete_send_signal_transaction()

    def populate_signal_completion_action(self):
        """
        No input flows are necessary since we know this signal is directed back at the same state model where
        it originated. So we simply populate the Signal Action subclass instance
        """
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Completion Action', tuples=[
            Signal_Completion_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        self.dest_sm = self.activity.state_model
        # The boundary actions are always just this one signal action id
        self.aids_in.add(self.action_id)
        self.aids_out.add(self.action_id)

        self.complete_send_signal_transaction()

    def complete_send_signal_transaction(self):
        """
        Populates common superclasses for Send Signal Actions and Delivery Time, if delayed
        """
        # Populate any Supplied Parameters
        self.populate_supplied_params()

        # Populate the superclasses
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Send Signal Action', tuples=[
            Send_Signal_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain,
                                 Event_spec=self.statement_parse.event, State_model=self.dest_sm)
        ])
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Action', tuples=[
            Signal_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])

        if self.statement_parse.dest.delay:
            self.populate_delay(delay_parse=self.statement_parse.dest.delay)

        Transaction.execute(db=mmdb, name=tr_Signal)

    def populate_ext_sig_params(self):
        """
        Populate any External Signal Parameters
        """
        # Validate Operation Call params (ensure that the call matches the Operation's populated signature
        R = f"Name:<{self.event_name}>, Domain:<{self.domain}>"
        ext_service_sv = 'ext_service_sv'
        ext_service_r = Relation.restrict(db=mmdb, relation='External Service', restriction=R,
                                          svar_name=ext_service_sv)
        if len(ext_service_r.body) != 1:
            msg = f"External operation not defined in: {self.activity.activity_path}"
            _logger.error(msg)
            raise ActionException(msg)
        signum = ext_service_r.body[0]['Signature']
        param_r = Relation.semijoin(db=mmdb, rname2='Parameter', attrs={'Signature': 'Signature', 'Domain': 'Domain'})
        sig_params = {t["Name"]: t["Type"] for t in param_r.body}

        # Populate each Parameter specified in the signature with an incoming Data Flow
        from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
        sp_pnames: set[str] = set()

        for sp in self.statement_parse.supplied_params:
            # Set the supplied parameter name
            pname = sp.pname.lower()
            # Scrall short hand lets you omit the parameter name when the value name matches.
            # So instead of typing 'shaft: Shaft', the user can just supply the value, attribute name, in this example.
            # leaving us with just 'Shaft'.
            # Attribute names are initial title case by convention. So we would end up with 'Shaft' as the pname.
            # So we make it lcase to obtain the actual parameter name. This avoids an issue when we validate the
            # input flow type match further down.
            sp_pnames.add(pname)

            # Resolve the supplied value to a flow or constant value
            sval_name = None
            sval_type = type(sp.sval).__name__
            sval_flow = None
            match sval_type:
                case 'N_a' | 'IN_a':
                    sval_name = sp.sval.name
                case 'INST_PROJ_a':
                    se = ScalarExpr(expr=sp.sval, input_instance_flow=self.activity.xiflow, activity=self.activity)
                    bactions, scalar_flows = se.process()
                    if len(scalar_flows) != 1:
                        msg = f"Type operation output is not a single scalar flow, instead got {scalar_flows}"
                        _logger.error(msg)
                        raise ActionException(msg)
                    sval_flow = scalar_flows[0]
                    self.aids_in.update(bactions.ain)
                case '_':
                    pass

            if sval_flow is None:
                # Populate parameter data flows
                if sval_name is not None:
                    # We have either a flow label or an attribute name
                    R = f"Name:<{sval_name}>, Class:<{self.activity.xiflow.tname}>, Domain:<{self.domain}>"
                    attr_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
                    if attr_r.body:
                        ra = ReadAction(input_single_instance_flow=self.activity.xiflow,
                                        attrs=(sval_name,), anum=self.anum, domain=self.domain)
                        aid, sflows = ra.populate()
                        self.aids_in.add(aid)  # Read action is an initial input to this signal action
                        sval_flow = sflows[0]
                    else:
                        sval_flows = Flow.find_labeled_scalar_flow(name=sval_name, anum=self.anum, domain=self.domain)
                        sval_flow = sval_flows[0] if sval_flows else None
                        # TODO: Check for case where multiple are returned
                else:
                    msg = f"No input flow found for operation call {self.action_id} input source for param {pname}"
                    _logger.error(msg)
                    raise ActionException(msg)

            # Validate type match
            if sval_flow.tname != sig_params[pname]:
                msg = (f"Supplied parameter flow type for {pname} does not match signature Parameter type "
                       f"{sig_params[pname]}")
                _logger.error(msg)
                raise ActionException  # TODO : Type define mismatch exception

            Relvar.insert(db=mmdb, tr=tr_Signal, relvar='External Signal Parameter', tuples=[
                External_Signal_Parameter_i(
                    Signal_action=self.action_id, Activity=self.anum, Parameter=pname,
                    Signature=signum, Domain=self.domain, Flow=sval_flow.fid)
            ])


    def populate_supplied_params(self):
        """
        Populate any Supplied Parmaeters
        """
        # Make sure the event spec exists while setting its state sig num
        R = f"Name:<{self.event_name}>, State_model:<{self.dest_sm}>, Domain:<{self.domain}>"
        event_spec_r = Relation.restrict(db=mmdb, relation="Event Specification", restriction=R)
        if not event_spec_r.body:
            msg = f"Event specification {self.event_name} in {self.activity.activity_path} not found"
            _logger.error(msg)
            raise ActionException(msg)
        evspec_sig = event_spec_r.body[0]['State_signature']

        for p in self.statement_parse.supplied_params:
            # Validate the parameter
            R = f"Name:<{p.pname}>, Signature:<{evspec_sig}>, Domain:<{self.domain}>"
            parameter_r = Relation.restrict(db=mmdb, relation="Parameter", restriction=R)
            if not parameter_r.body:
                msg = f"No parameters defined for event {self.event_name} with signature: {evspec_sig}"
                _logger.error(msg)
                raise ActionException(msg)

            se = ScalarExpr(expr=p.sval, input_instance_flow=self.activity.xiflow, activity=self.activity)
            b, sflows = se.process()
            # Verify that a scalar flow was found
            if len(sflows) != 1:
                msg = f"Scalar flow not found for parameter {p.pname} in scalar expression at {self.activity.path}"
                _logger.error(msg)
                ActionException(msg)
            param_flow = sflows[0]
            Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Supplied Parameter Value', tuples=[
                Supplied_Parameter_Value_i(Parameter=p.pname, Signature=evspec_sig, Action=self.action_id,
                                           Activity=self.anum, Domain=self.domain, Data_flow=param_flow.fid)
            ])

    def populate_delay(self, delay_parse):
        """
        Populate the delay on this signal

        Args:
            delay_parse: A scalar expression flowing in a duration or time value
        """
        # Resolve the input flow
        se = ScalarExpr(expr=delay_parse, input_instance_flow=self.input_instance_flow, activity=self.activity)
        _, sflows = se.process()
        if len(sflows) == 1:
            signal_delay_input_flow = sflows[0]
        elif len(sflows) > 1:
            # We need a gate
            ga = GateAction(input_fids=[f.fid for f in sflows], output_flow_label=delay_parse.name, activity=self.activity)
            _, gate_output_flow = ga.populate()
            signal_delay_input_flow = gate_output_flow
        else:
            msg = (f"Signal delay requires a scalar input flow and none found for: delay {delay_parse} "
                   f"in {self.activity.activity_path}")
            _logger.error(msg)
            raise ActionException

        # Validate the delivery time Scalar Flow type
        delay_types = {'Duration', 'Time'}
        if signal_delay_input_flow.tname not in delay_types:
            msg = f"Signal delivery scalar type not in set {delay_types} at: {self.activity.activity_path}"
            _logger.exception(msg)
            ActionException(msg)

        relative = True if signal_delay_input_flow.tname == 'Duration' else False

        # Populate
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Delivery Time', tuples=[
            Delivery_Time_i(Action=self.action_id, Activity=self.anum, Domain=self.domain,
                            Flow=signal_delay_input_flow.fid, Relative=relative)
        ])
