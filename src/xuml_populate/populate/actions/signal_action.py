"""
signal_action.py – Populate a signal action instance in PyRAL
"""

# System
import logging
from typing import TYPE_CHECKING

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
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.populate.mmclass_nt import (Signal_Action_i, Supplied_Parameter_Value_i,
                                               Signal_Instance_Set_Action_i,
                                               Delivery_Time_i, Absolute_Delivery_Time_i, Relative_Delivery_Time_i,
                                               Multiple_Assigner_Partition_Instance_i, Signal_Assigner_Action_i,
                                               Instance_Action_i, Initial_Signal_Action_i)

_logger = logging.getLogger(__name__)

# Transactions
tr_Signal = "Signal Action"

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
        self.activity = activity

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
        self.completion_event = False

        if type(statement_parse).__name__ == 'External_signal_a':
            self.external_dest = True

        # Is the target of this signal a creation action? - if so, it's an Initial Signal Action?
        target_iset = statement_parse.dest.target_iset
        if type(target_iset).__name__ == "INST_a":
            if len(target_iset.components) == 1 and type(target_iset.components[0]).__name__ == 'New_inst_a':
                self.initial_signal_action = True

    def populate_external_signal(self):
        pass  # TODO: Implement this case

    def populate_initial_signal(self) -> str:
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
        new_inst_parse = self.statement_parse.dest.target_iset.components[0]
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
            iset_parses = [ref.iset1]
            if ref.iset1:
                iset_parses.append(ref.iset2)
            else:
                msg = f"No reference instance set for event: {self.event_name} in {self.activity.activity_path}"
                _logger.error(msg)
                raise ActionException(msg)
            # Supplying one or two refs for this rnum
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
            Initial_Signal_Action_i(ID=self.action_id, Activity=self.activity.anum, Domain=self.activity.domain)
        ])
        # The boundary actions are always just this one signal action id
        self.aids_in.add(self.action_id)
        self.aids_out.add(self.action_id)

        self.complete_transaction()
        DelegatedCreationActivity(class_name=dest_class, attr_init_flows=attr_init_flows, ref_inits=ref_inits,
                                  delegating_activity=self.activity)
        return dest_class

    def process_signal_instance_set_action(self, dest) -> str:
        """
        Returns:
            Destination state model so we know where event specification is defined
        """

        dest_sm = dest  # Destination state machine to find the target Event Specification
        if self.signal_dest.target_iset:
            # An instance set destination was specified, so a signal will be sent to each instance lifecycle
            # state machine in the set
            dest_flow = None
            iset_type = type(self.signal_dest.target_iset).__name__
            match iset_type:
                case 'N_a':
                    dest_name = self.signal_dest.target_iset.name
                    if dest_name == 'me':
                        dest_sm = self.activity.state_model
                        # TODO: This is NOT a signal instance set action if target is assigner
                        # TODO: In fact, this is a completion event
                    else:
                        pass  # TODO: Destination is some other state model (via instance flow)
                    self.aids_in.add(self.action_id)
                    self.aids_out.add(self.action_id)
                case 'IN_a':
                    pass  # It is an input parameter
                    self.aids_in.add(self.action_id)
                    self.aids_out.add(self.action_id)
                case 'INST_a':
                    iset = InstanceSet(input_instance_flow=self.activity.xiflow,
                                       iset_components=self.signal_dest.target_iset.components,
                                       activity=self.activity)
                    ain, aout, dest_flow = iset.process()
                    dest_sm = dest_flow.tname
                    self.aids_in.add(ain)
                    self.aids_out.add(aout)
                case _:
                    pass  # Includes case where a more complex instance set expression is supplied

            Relvar.insert(db=mmdb, tr=tr_Signal, relvar='Signal Instance Set Action', tuples=[
                Signal_Instance_Set_Action_i(ID=self.action_id, Activity=self.activity.anum,
                                             Domain=self.activity.domain, Instance_flow=dest_flow.fid)
            ])
            return dest_sm

    def process_signal_assigner_action(self) -> str:
        """
        """
        if self.completion_event:
            dest_sm = self.activity.state_model
            self.aids_in.add(self.action_id)
            self.aids_out.add(self.action_id)
        else:
            dest_sm = self.statement_parse.dest.assigner_dest.rnum.rnum
            pi_flow = None
            # The signal will be addressed to an assigner state machine associated with a target association
            # Verify that the rnum is in fact an association (not an ordinal or a generalization relationship)

            # It's a safe assumption that we're signaling an assigner from a lifecycle state machine or a method
            # So we should have an xi flow
            if not self.activity.xiflow:
                pass  # TODO: Handle case where an assigner is sending a signal to another assigner

            iset = InstanceSet(input_instance_flow=self.activity.xiflow,
                               iset_components=self.signal_dest.assigner_dest.partition.components,
                               activity=self.activity)
            ain, aout, f = iset.process()
            self.aids_in.add(ain)
            self.aids_out.add(aout)

            # If the destination is a Multiple Assigner, populate the partition instance
            R = f"Rnum:<{dest_sm}>, Domain<{self.activity.domain}>"
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
        return dest_sm

    def populate_subclass(self):
        """
        """
        # Is this an signal that will be mapped to a counterpart in another domain?
        # In early Shlaer-Mellor this was an event to an external entity
        if self.external_dest:
            self.populate_external_signal()  # No returned destination
            return

        # Is this a signal delegation creation of a lifecycle instance on an initial psuedo state transition?
        if self.initial_signal_action:
            self.dest_sm = self.populate_initial_signal()  # Returned destination is the target class name
            return

        # The destination is either an instance set or an assigner
        target_iset = self.statement_parse.dest.target_iset
        if target_iset and type(target_iset).__name__ == 'N_a' and target_iset.name == 'me':
            self.completion_event = True
        assigner_dest = self.statement_parse.dest.assigner_dest
        if target_iset and assigner_dest:
            # Only one of these two should be set
            msg = (f"Instance set and assigner destinations are mutually exclusive as a signal destination.\n"
                   f"But both have been specified for signal {self.event_name} in {self.activity.activity_path}")
            _logger.error(msg)
            raise ActionException(msg)


        # It's an assigner destination if an assigner_iset is specified, or if the
        # destination is self AND self is an assigner
        if assigner_dest or self.completion_event and self.activity.smtype != SMType.LIFECYCLE:
            self.dest_sm = self.process_signal_assigner_action()
            return

        # The destination must be an instance set so the target is a lifecycle state model
        # A distinct signal may be generated for each in the target instance set, but they all share the same lifecycle
        # so there is still only one destination state model
        if self.signal_dest.target_iset:
            self.dest_sm = self.process_signal_instance_set_action(dest=target_iset)
            return

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
