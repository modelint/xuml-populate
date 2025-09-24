"""
signal_action.py – Populate a signal action instance in PyRAL
"""

# System
import logging
from typing import TYPE_CHECKING, Optional

# Model Integration
from scrall.parse.visitor import Signal_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

from xuml_populate.exceptions.action_exceptions import ActionException

# xUML populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.delegated_creation import DelegatedCreationActivity
from xuml_populate.populate.actions.expressions.enumflow import EnumFlow
from xuml_populate.populate.actions.aparse_types import Boundary_Actions, SMType
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow_ap
from xuml_populate.populate.actions.gate_action import GateAction
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.mmclass_nt import (Signal_Action_i, Supplied_Parameter_Value_i,
                                               Signal_Instance_Set_Action_i, Delivery_Time_i,
                                               Multiple_Assigner_Partition_Instance_i, Signal_Assigner_Action_i,
                                               Instance_Action_i, Initial_Signal_Action_i, Signal_Completion_Action_i,
                                               Signal_Instance_Action_i, Cancel_Delayed_Signal_Action_i,
                                               Cancel_Delayed_Interaction_Signal_i, Interaction_Signal_Action_i,
                                               Cancel_Delayed_Completion_Signal_i)

_logger = logging.getLogger(__name__)

# Transactions
tr_Signal = "Signal Action"
ips_name = 'Initial_Pseudo_State'  # All Initial Pseudo States have the same name

class SignalAction:
    """
    Create all relations for a Signal Action.
    """
    # TODO: Implement other Signal Action subclasses
    # TODO: activity type should be ActivityAP
    def __init__(self, statement_parse: Signal_a, activity: 'Activity'):
        """
        Initialize with everything the Signal statement requires

        Args:
            statement_parse: Parsed representation of the Signal statement
            activity: Collected info about the activity
        """
        self.event_name = statement_parse.event
        self.action_id = None
        self.statement_parse = statement_parse
        self.target_iset = statement_parse.dest.target_iset
        # Check for completion event
        if self.target_iset is not None and type(self.target_iset).__name__ == 'N_a' and self.target_iset.name == 'me':
            self.completion_event = True
        else:
            self.completion_event = False
        self.activity = activity
        self.input_instance_flow = activity.xiflow if activity.xiflow is not None else activity.piflow
        # Will still be None if the Activity is in an Assigner state model

        self.dest_iflow = None
        self.parameter_values = None
        self.delay_sflow = None
        self.aids_in: set[str] = set()
        self.aids_out: set[str] = set()
        self.action_id: str = None
        self.signal_dest = None
        self.dest_sm = None
        self.initial_signal_action = False  # Default assumption
        self.external_dest = False

        if type(statement_parse).__name__ == 'External_signal_a':
            self.external_dest = True

        # Is the target of this signal a creation action? - if so, it's an Initial Signal Action?
        if type(self.target_iset).__name__ == "INST_a":
            if len(self.target_iset.components) == 1 and type(self.target_iset.components[0]).__name__ == 'New_inst_a':
                self.initial_signal_action = True

    def populate_external_signal(self):
        pass  # TODO: Implement this case

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
            pass
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
            Initial_Signal_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain,
                                    Class=dest_class, Pseudo_state=ips_name)
        ])
        # The boundary actions are always just this one signal action id
        self.aids_in.add(self.action_id)
        self.aids_out.add(self.action_id)

        self.complete_transaction()
        DelegatedCreationActivity(class_name=dest_class, attr_init_flows=attr_init_flows, ref_inits=ref_inits,
                                  delegating_activity=self.activity)

    def find_dest_flow(self) -> Optional[Flow_ap]:
        """
        Find the populated Instance Flow supplying the parsed target destination and return its summary.

        Returns:
            Summary of the destination flow or None if not found or its a completion event
        """
        if self.completion_event:
            return None
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
                self.aids_out.add(self.action_id)
                return dest_flow
            case 'INST_a':
                iset = InstanceSet(input_instance_flow=self.activity.xiflow,
                                   iset_components=self.target_iset.components,
                                   activity=self.activity)
                ain, aout, dest_flow = iset.process()
                self.dest_sm = dest_flow.tname
                self.aids_in.add(ain)
                self.aids_out.add(aout)
                return dest_flow
            case _:
                msg = f"Unimplemented or undefined instance set in: {self.activity.activity_path}"
                _logger.error(msg)
                raise ActionException(msg)

    def process_signal_instance_set_action(self, dest):
        """
        """

        # An instance set destination was specified, so a signal will be sent to each instance lifecycle
        # state machine in the set
        dest_flow = None
        iset_type = type(dest).__name__
        match iset_type:
            case 'N_a':
                if dest.name == 'me':
                    self.dest_sm = self.activity.state_model
                    dest_flow = self.activity.xiflow
                    # TODO: This is NOT a signal instance set action if target is assigner
                    # TODO: In fact, this is a completion event
                else:
                    # Resolve the destination instance flow
                    iset = InstanceSet(input_instance_flow=self.input_instance_flow,
                                       iset_components=[dest],
                                       activity=self.activity)
                    _, _, dest_flow = iset.process()
                    if not dest_flow:
                        msg = (f"Cound not find destination flow: [{dest.name}] for Signal Instance Set Action "
                               f"in {self.activity.activity_path}")
                        _logger.error(msg)
                        raise ActionException(msg)
                    self.dest_sm = dest_flow.tname
                    self.aids_in.add(self.action_id)
                    self.aids_out.add(self.action_id)
            case 'IN_a':
                pass  # It is an input parameter
                self.aids_in.add(self.action_id)
                self.aids_out.add(self.action_id)
            case 'INST_a':
                iset = InstanceSet(input_instance_flow=self.activity.xiflow,
                                   iset_components=dest.components,
                                   activity=self.activity)
                ain, aout, dest_flow = iset.process()
                self.dest_sm = dest_flow.tname
                self.aids_in.add(ain)
                self.aids_out.add(aout)
            case _:
                pass  # Includes case where a more complex instance set expression is supplied

        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Instance Action', tuples=[
            Signal_Instance_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Interaction Signal Action', tuples=[
            Interaction_Signal_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain,
                                        Instance_flow=dest_flow.fid)
        ])
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Instance Set Action', tuples=[
            Signal_Instance_Set_Action_i(ID=self.action_id, Activity=self.activity.anum,
                                         Domain=self.activity.domain)
        ])
        self.complete_transaction()

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
            pass  # TODO: Handle case where an assigner is sending a signal to another assigner

        iset = InstanceSet(input_instance_flow=self.activity.xiflow,
                           iset_components=self.statement_parse.dest.assigner_dest.partition.components,
                           activity=self.activity)
        ain, aout, f = iset.process()
        self.aids_in.add(ain)
        self.aids_out.add(aout)

        # If the destination is a Multiple Assigner, populate the partition instance
        R = f"Rnum:<{dest_sm}>, Domain:<{self.activity.domain}>"
        multiple_assigner_r = Relation.restrict(db=mmdb, relation="Multiple Assigner", restriction=R)
        if multiple_assigner_r.body:
            Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Multiple Assigner Partition Instance', tuples=[
                Multiple_Assigner_Partition_Instance_i(Action=self.action_id, Activity=self.activity.anum,
                                                       Domain=self.activity.domain,
                                                       Partition=f.fid)
            ])

        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Assigner Action', tuples=[
            Signal_Assigner_Action_i(ID=self.action_id, Activity=self.activity.anum,
                                     Domain=self.activity.domain,
                                     Association=dest_sm)
        ])
        self.dest_sm = dest_sm

    def populate_cancel_delayed_signal_action(self):
        """
        Populate a Cancel Delayed Signal Action (either Completion or Interaction)
        """
        if self.completion_event:
            # Destination is self, so no instance input flow required
            Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Cancel Delayed Completion Signal', tuples=[
                Cancel_Delayed_Completion_Signal_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain)
            ])
            self.dest_sm = self.activity.state_model
        else:
            # It's an interaction event, so we need to set the target instance flow
            dest_flow = self.find_dest_flow()
            Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Cancel Delayed Interaction Signal', tuples=[
                Cancel_Delayed_Interaction_Signal_i(ID=self.action_id, Activity=self.activity.anum,
                                                    Domain=self.activity.domain)
            ])
            Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Interaction Signal Action', tuples=[
                Interaction_Signal_Action_i(ID=self.action_id, Activity=self.activity.anum,
                                            Domain=self.activity.domain, Instance_flow=dest_flow.fid)
            ])

        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Cancel Delayed Signal Action', tuples=[
            Cancel_Delayed_Signal_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain)
        ])

        # The boundary actions are always just this one signal action id
        self.aids_in.add(self.action_id)
        self.aids_out.add(self.action_id)

        self.complete_transaction()

    def populate_signal_completion_action(self):
        """
        No input flows are necessary since we know this signal is directed back at the same state model where
        it originated. So we simply populate the Signal Action subclass instance
        """
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Instance Action', tuples=[
            Signal_Instance_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Completion Action', tuples=[
            Signal_Completion_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain)
        ])
        self.dest_sm = self.activity.state_model
        # The boundary actions are always just this one signal action id
        self.aids_in.add(self.action_id)
        self.aids_out.add(self.action_id)

        self.complete_transaction()

    def populate_subclass(self):
        """
        """
        # Is this a signal that will be mapped to a counterpart in another domain?
        # In early Shlaer-Mellor this was an event to an external entity
        if self.external_dest:
            self.populate_external_signal()  # No returned destination
            return

        if self.statement_parse.dest.cancel:
            self.populate_cancel_delayed_signal_action()
            return

        # Is this a signal delegation creation of a lifecycle instance on an initial psuedo state transition?
        if self.initial_signal_action:
            self.populate_initial_signal()  # Returned destination is the target class name
            return

        # If the destination is 'me' this must be a Signal Completion Action
        # since we've alredy ruled out a Cancel Delayed Completion Signal Action
        if self.completion_event:
            self.populate_signal_completion_action()
            return

        assigner_dest = self.statement_parse.dest.assigner_dest
        if self.target_iset and assigner_dest:
            # Only one of these two should be set
            msg = (f"Instance set and assigner destinations are mutually exclusive as a signal destination.\n"
                   f"But both have been specified for signal {self.event_name} in {self.activity.activity_path}")
            _logger.error(msg)
            raise ActionException(msg)

        # It's a signal to an assigner
        if assigner_dest:
            self.process_signal_assigner_action()
            return

        # The destination must be an instance set so the target is a lifecycle state model
        # A distinct signal may be generated for each in the target instance set, but they all share the same lifecycle
        # so there is still only one destination state model
        if self.target_iset:
            self.process_signal_instance_set_action(dest=self.target_iset)
            return

        msg = f"No destination defined for event {self.event_name} in {self.activity.activity_path}"
        _logger.error(msg)
        raise ActionException(msg)

    def complete_transaction(self):
        # Populate the superclasses
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Action', tuples=[
            Signal_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain,
                            Event_spec=self.statement_parse.event, State_model=self.dest_sm)
        ])
        Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain)
        ])

        if self.statement_parse.supplied_params:
            # TODO: Populate Supplied Parameter Value instances for each
            pass
        if self.statement_parse.dest.delay != 0:
            # TODO: Populate Delivery Time
            pass

        Transaction.execute(db=mmdb, name=tr_Signal)

        if self.statement_parse.dest.delay:
            self.populate_delay(delay_parse=self.statement_parse.dest.delay)

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
        Relvar.insert(db=mmdb, relvar='Delivery Time', tuples=[
            Delivery_Time_i(Action=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain,
                            Flow=signal_delay_input_flow.fid, Relative=relative)
        ])
        pass

    def populate(self) -> Boundary_Actions:
        """
        Returns:
            Boundary_Actions: The signal action id is both the initial_pseudo_state and final action id
        """
        # Initiate the Signal Action transaction
        Transaction.open(db=mmdb, name=tr_Signal)
        # Populate the Action superclass instance and obtain its action_id
        self.action_id = Action.populate(tr=tr_Signal, anum=self.activity.anum, domain=self.activity.domain,
                                         action_type="signal")  # Transaction open

        self.populate_subclass()

        return Boundary_Actions(ain=self.aids_in, aout=self.aids_out)
