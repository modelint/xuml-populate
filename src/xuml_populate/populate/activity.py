"""
activity.py – Populate an Activity
"""

# System
import logging
from typing import NamedTuple, Optional
# For debugging
from collections import namedtuple

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from pyral.rtypes import JoinCmd, ProjectCmd, SetCompareCmd, SetOp, Attribute, SumExpr, RelationValue
from scrall.parse.parser import ScrallParser

# xUML Populate
from xuml_populate.utility import print_mmdb
from xuml_populate.populate.actions.aparse_types import SMType, Method_Output_Type
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.utility import print_mmdb
from xuml_populate.populate.actions.sequence_flow import SequenceFlow
from xuml_populate.populate.xunit import ExecutionUnit
from xuml_populate.populate.mmclass_nt import Flow_Dependency_i, Wave_i, Wave_Assignment_i, \
    Delegated_Creation_Activity_i, Real_State_Activity_i
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow, Flow_ap
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.element import Element
from xuml_populate.populate.actions.aparse_types import (ActivityAP, SMType, ActivityType, Boundary_Actions)
from xuml_populate.populate.mmclass_nt import (Activity_i, State_Activity_i, Lifecycle_Activity_i,
                                               Multiple_Assigner_Activity_i, Single_Assigner_Activity_i,
                                               Synchronous_Output_i, Flow_Connector_i, Pass_Action_i,
                                               Instance_Action_i, Gate_Action_i, Gate_Input_i, Real_State_Activity_i)

_logger = logging.getLogger(__name__)

# Temporarily silence the noisy scrall visitor logger
null_handler = logging.NullHandler()
# print(logging.root.manager.loggerDict.keys())
slogger = logging.getLogger("scrall.parse.visitor")
slogger.handlers.clear()
slogger.addHandler(null_handler)
slogger.propagate = False


# TODO: This can be generated later by make_repo, ensure each name ends with 'Action'
class UsageAttrs(NamedTuple):
    cname: str
    id_attr: str | None
    in_attr: str | None
    out_attr: str | None
    in_attr2: str | None = None  # New Associative Reference Action for example

# We use the following list of tuples to extract the required input and output flows of each Action type
# Create a tuple for each class that specifies an input, output or both flows as part of some Action's subsystem
# Some Action's require one class while others may have two or three

# cname - the name of the class holding references to one or more required flows, PyRAL allows spaces in class name
# id_attr - The attribute holding the Action ID, so the type must be Action ID, PyRAL requires snake_case for attrs
# in_attr - The name of the required input, for now we assume there is only one, type of this attr must be Flow ID
# in_attr2 - Okay, make that two possible required inputs in rare cases, same rules as for in_attr
# out_attr - The name of a required output attr, again a Flow ID type

flow_attrs = [
    UsageAttrs(cname='Computation Input', id_attr='Computation', in_attr='Input_flow', out_attr=None),
    UsageAttrs(cname='Computation Action', id_attr='ID', in_attr=None, out_attr='Output_flow'),
    UsageAttrs(cname='Type Action', id_attr='ID', in_attr=None, out_attr='Output_flow'),
    UsageAttrs(cname='Type Operation', id_attr='ID', in_attr='Input_flow', out_attr=None),
    UsageAttrs(cname='Pass Action', id_attr='ID', in_attr='Input_flow', out_attr='Output_flow'),
    UsageAttrs(cname='Delete Action', id_attr='ID', in_attr='Flow', out_attr=None),
    UsageAttrs(cname='Method Call', id_attr='ID', in_attr='Instance_flow', out_attr=None),
    UsageAttrs(cname='Method Call Parameter', id_attr='Method_call', in_attr='Flow', out_attr=None),
    UsageAttrs(cname='Method Call Output', id_attr='Method_call', in_attr=None, out_attr='Flow'),
    UsageAttrs(cname='Decision Action', id_attr='ID', in_attr='Boolean_input', out_attr=None),
    UsageAttrs(cname='Result', id_attr='Decision_action', in_attr=None, out_attr='Flow'),
    UsageAttrs(cname='Reference Value Input', id_attr='Create_action', in_attr='Flow', out_attr=None),
    UsageAttrs(cname='Local Create Action', id_attr='ID', in_attr=None, out_attr='New_instance_flow'),
    UsageAttrs(cname='Reference Action', id_attr='ID', in_attr=None, out_attr='Ref_attr_values'),
    UsageAttrs(cname='New Associative Reference Action', id_attr='ID', in_attr='T_instance', in_attr2='P_instance',
               out_attr=None),
    UsageAttrs(cname='Multiple Assigner Partition Instance', id_attr='Action', in_attr='Partition', out_attr=None),
    UsageAttrs(cname='Signal Instance Set Action', id_attr='ID', in_attr='Instance_flow', out_attr=None),
    UsageAttrs(cname='Write Action', id_attr='ID', in_attr='Instance_flow', out_attr=None),
    UsageAttrs(cname='Attribute Write Access', id_attr='Write_action', in_attr='Input_flow', out_attr=None),
    UsageAttrs(cname='Select Action', id_attr='ID', in_attr='Input_flow', out_attr=None),
    UsageAttrs(cname='Traverse Action', id_attr='ID', in_attr='Source_flow', out_attr='Destination_flow'),
    UsageAttrs(cname='Many Select', id_attr='ID', in_attr=None, out_attr='Output_flow'),
    UsageAttrs(cname='Single Select', id_attr='ID', in_attr=None, out_attr='Output_flow'),
    UsageAttrs(cname='Table Action', id_attr='ID', in_attr='Input_a_flow', out_attr='Output_flow'),
    UsageAttrs(cname='Set Action', id_attr='ID', in_attr='Input_b_flow', out_attr=None),
    UsageAttrs(cname='Read Action', id_attr='ID', in_attr='Instance_flow', out_attr=None),
    UsageAttrs(cname='Attribute Read Access', id_attr='Read_action', in_attr=None, out_attr='Output_flow'),
    UsageAttrs(cname='Comparison Criterion', id_attr='Action', in_attr='Value', out_attr=None),
    UsageAttrs(cname='Gate Action', id_attr='ID', in_attr=None, out_attr='Output_flow'),
    UsageAttrs(cname='Gate Input', id_attr='Gate_action', in_attr='Input_flow', out_attr=None),
    UsageAttrs(cname='Case', id_attr='Switch_action', in_attr=None, out_attr='Flow'),
    UsageAttrs(cname='Control Dependency', id_attr='Action', in_attr='Control_flow', out_attr=None),
    UsageAttrs(cname='Extract Action', id_attr='ID', in_attr='Input_tuple', out_attr='Output_scalar'),
]

Action_i = namedtuple('Action_i', 'ID')

class Activity:
    """
    Create an Activity relation
    """
    # These dictionaries are for debugging purposes, delete once we get action semantics populated
    operations = {}
    domain = None

    def __init__(self, activity_data: ActivityAP):
        """
        Populate the Activity and perform any pre-runtime analysis or organization helpful for runtime
        execution.

        Args:
            activity_data: All the data, including parse, about this method
        """
        # These are common to both Method and State Activities
        self.anum = activity_data.anum
        self.domain = activity_data.domain
        self.activity_path = activity_data.activity_path

        # These are not relevant for a creation activity
        self.parse = None
        self.signum = None
        self.scrall_text = None
        self.domain_method_output_types = None

        if type(activity_data).__name__ != 'DelegatedCreationActivityAP':
            self.parse = activity_data.parse
            self.signum = activity_data.signum
            self.scrall_text = activity_data.scrall_text
            self.domain_method_output_types = activity_data.domain_method_output_types
            self.synch_output_flows: set[Flow_ap] = set()  # Tracks synch outputs of a Method Activity

        # These default to None since they are specific to either Method or State Activities
        self.method_name: Optional[str] = None
        self.class_name: Optional[str] = None
        self.state_name: Optional[str] = None
        self.state_model: Optional[str] = None
        self.smtype: Optional[SMType] = None
        self.pclass: Optional[str] = None
        self.xiflow: Optional[Flow_ap] = None  # Executable instance flow (for a Method or Lifecycle)
        self.piflow: Optional[Flow_ap] = None  # Partitioning instance flow (for a Multiple Assigner)
        self.flow_path = None  # Not set until flow dependencies are processed
        # self.domain_method_output_types: Optional[dict[str, Method_Output_Type]] = None

        match type(activity_data).__name__:
            case 'MethodActivityAP':
                self.atype = ActivityType.METHOD
                self.method_name = activity_data.opname
                self.class_name = activity_data.cname
                self.xiflow = activity_data.xiflow
            case 'StateActivityAP':
                self.atype = ActivityType.STATE
                self.state_name = activity_data.sname
                self.state_model = activity_data.state_model
                self.smtype = activity_data.smtype
                self.piflow = activity_data.piflow
                self.xiflow = activity_data.xiflow  # None if not a Lifecycle state
                self.smtype = activity_data.smtype
            case 'DelegatedCreationActivityAP':
                self.class_name = activity_data.cname
                pass
            case _:
                msg = f"Activity is neither a Method, State, or Delegated Creation Activity"
                _logger.error(msg)
                raise ActionException(msg)

        # Maintain a dictionary of seq token control flow dependencies
        # seq_token_out_action: {seq_token_in_actions}
        self.seq_flows: dict[str, set[str]] = {}
        # seq_token: output_action_ids
        self.seq_tokens: dict[str, set[str]] = {}

        self.wave_ctr = 1  # Initialize wave counter
        self.waves: dict[int, list[str]] = {}

    def pop_actions(self):
        """
        Populate all actions for this Activity
        """
        self.pop_xunits()
        if self.atype == ActivityType.METHOD:
            self.resolve_method_outputs()  # Ensure that each method with an output has only one

    def prep_for_execution(self):
        """
        Post process the populated activities to provide helpful information for execution
        """
        self.pop_seq_flows()
        self.pop_flow_dependencies()
        self.assign_waves()
        self.populate_waves()

    def pop_seq_flows(self):
        for source, destinations in self.seq_flows.items():
            # Find the token associated with the source action
            # A source action can emit at most one sequence flow, so only one t value should be found
            t = next(k for k, v in self.seq_tokens.items() if source in v)
            if not t:
                msg = f"Sequence token not found in: {self.activity_path}"
                _logger.error(msg)
                raise FlowException(msg)
            s = SequenceFlow(token=t, source_aid=source, dest_aids=destinations, anum=self.anum, domain=self.domain)

    def resolve_method_outputs(self):
        # Check the synch outputs for this method

        # Just return if this activity is not a method or if it is and has no output flows
        if self.atype != ActivityType.METHOD or not self.synch_output_flows:
            return

        # If there is only one output flow, just populate it as the method's synchronous output
        if len(self.synch_output_flows) == 1:
            single_output_flow = self.synch_output_flows.pop()
            Relvar.insert(db=mmdb, relvar='Synchronous Output', tuples=[
                Synchronous_Output_i(Anum=self.anum, Domain=self.domain,
                                     Output_flow=single_output_flow.fid, Type=single_output_flow.tname)
            ])
            _logger.info(f"INSERT Synchronous operation output flow): ["
                         f"{self.activity_path}:^{single_output_flow.fid}]")
            return

        # There are multiple output flows and we need to funnel them into a single flow
        #
        # and then populate a gate action to combine them with a single output
        # Then make that output the synch output as above
        # Check for any existing Pass Actions in this Activity
        # These would have been created to provide a required destination action for any Decision Action results
        # that just pass one of the output flows
        # pass_output_flows: set[Flow_ap] = set()
        R = f"Activity:<{self.anum}>, Domain:<{self.domain}>"
        pass_action_r = Relation.restrict(db=mmdb, relation="Pass Action", restriction=R)
        # Remove any synch output flows from consideration that are input to a Pass Action
        passed_input_fids = {t["Input_flow"] for t in pass_action_r.body}
        pass_action_input_fids = {f.fid for f in self.synch_output_flows if f.fid not in passed_input_fids}
        gate_input_fids = {t["Output_flow"] for t in pass_action_r.body}

        # Populate the output flow (no transaction required)
        tr_Pass = "Pass Action"
        for input_fid in pass_action_input_fids:
            # Each Pass Action is populated in its own transaction
            Transaction.open(db=mmdb, name=tr_Pass)
            # Each synch output will will be populated as an input to its own Pass Action
            # Create a copy of the input to be the passed output
            pass_output_flow = Flow.copy_data_flow(tr=tr_Pass, ref_fid=input_fid, ref_anum=self.anum,
                                                   new_anum=self.anum, domain=self.domain)
            # Add it to the set of outputs to be converged into a gate
            gate_input_fids.add(pass_output_flow.fid)

            # Populate the Pass Action
            aid = Action.populate(tr=tr_Pass, anum=self.anum, domain=self.domain, action_type="pass")
            Relvar.insert(db=mmdb, tr=tr_Pass, relvar='Instance Action', tuples=[
                Instance_Action_i(ID=aid, Activity=self.anum, Domain=self.domain)
            ])
            Relvar.insert(db=mmdb, tr=tr_Pass, relvar='Flow Connector', tuples=[
                Flow_Connector_i(ID=aid, Activity=self.anum, Domain=self.domain)
            ])
            Relvar.insert(db=mmdb, tr=tr_Pass, relvar='Pass Action', tuples=[
                Pass_Action_i(ID=aid, Activity=self.anum, Domain=self.domain, Input_flow=input_fid,
                              Output_flow=pass_output_flow.fid)
            ])
            Transaction.execute(db=mmdb, name=tr_Pass)

        pass

        # Populate a gate with the outputs
        tr_Gate = "Gate Action"
        Transaction.open(db=mmdb, name=tr_Gate)

        # Get a new action id
        gate_aid = Action.populate(tr=tr_Gate, anum=self.anum, domain=self.domain, action_type="gate")

        # Populate the gate's output flow by copying one of the input flows
        # Just grab this methods first synch output flow as a copy reference
        # (as with the pass action, the input and output flow characteristics must match exactly)
        ref_pass_input_flow = next(iter(gate_input_fids))
        gate_output_flow = Flow.copy_data_flow(tr=tr_Gate, ref_fid=ref_pass_input_flow, ref_anum=self.anum,
                                               new_anum=self.anum, domain=self.domain)

        # Now we can populate the Gate Action
        Relvar.insert(db=mmdb, tr=tr_Gate, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=gate_aid, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Gate, relvar='Flow Connector', tuples=[
            Flow_Connector_i(ID=gate_aid, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Gate, relvar='Gate Action', tuples=[
            Gate_Action_i(ID=gate_aid, Output_flow=gate_output_flow.fid, Activity=self.anum, Domain=self.domain)
        ])

        # A Gate Input is populated per input flow
        for input_fid in gate_input_fids:
            Relvar.insert(db=mmdb, tr=tr_Gate, relvar='Gate Input', tuples=[
                Gate_Input_i(Gate_action=gate_aid, Input_flow=input_fid, Activity=self.anum,
                             Domain=self.domain)
            ])

        Transaction.execute(db=mmdb, name=tr_Gate)
        pass

        # Now we can populate the Synchronous Output with the gate output flow
        # (no transaction required since it's just one relvar)
        Relvar.insert(db=mmdb, relvar='Synchronous Output', tuples=[
            Synchronous_Output_i(Anum=self.anum, Domain=self.domain,
                                 Output_flow=gate_output_flow.fid, Type=gate_output_flow.tname)
        ])

        # Finally, we can populate Method Call Outputs
        from xuml_populate.populate.actions.method_call import MethodCall
        MethodCall.complete_output_transaction()

    def pop_xunits(self):
        """
        Break each parsed Scrall statement down into any number of Actions, or at the very least, Flow
        assignments, and populate the relevant metamodel classes.
        """
        # Iterate through each Scrall statement
        for count, xunit in enumerate(self.parse):
            c = count + 1  # Use count to assist debugging
            # A parsed Scrall statement is delivered as an ExecutionUnit namedtuple
            boundary_actions = ExecutionUnit.process_statement_set(
                activity=self, content=xunit.statement_set)

            # The boundary_actions variable gives us the initial and final actions, if any, for each populated statement
            # This information is relevant to a statement that enables, is enabled, or both by sequence tokens.
            # Seqence tokens are populated as Control Flows from one Action to possibly multiple other Actions
            # triggered by control rather than data dependencies. So the boundary_actions tell us the path of each
            # required Control Flow from one Action to another.

            # Let's say the populated ExecutionUnit above populates a chain of Actions connected by data flows like
            # this:  ACTN4 -> ACTN2 -> ACTN7
            # and let's also say that there is both an input <1> and output <2> sequence token defined in the
            # ExecutionUnit.  Whichever Action enabled <1> will emit a Control Flow to ACTN4 since that is the initial
            # action. There is no need to emit Control Flows to ACTN2 or ACTN7 since neither will execute unless ACTN4
            # is enabled.  Similarly, <2> may be emitted from ACTN7 to some initial Action(s) reported by another
            # ExecutionUnit.  In other words, we don't need to connect Control Flows to any Actions inside between the
            # boundary actions to get the specified sequencing dependency.

            # TODO: Test case where there are no boundary actions
            # Process any sequence tokens
            in_tokens, out_token = xunit.statement_set.input_tokens, xunit.output_token
            if out_token:
                # The statement has set an output_token (it cannot set more than one)
                # Register the new out_token
                if out_token in self.seq_tokens:
                    pass  # TODO: raise exception -- token can ony be set by one statement
                self.seq_tokens[out_token.name] = set()
                for a in boundary_actions.aout:
                    # Each output_action is the source of a control dependency named by that output token
                    # Register the output token and the emitting action
                    self.seq_tokens[out_token.name].add(a)
                    self.seq_flows[a] = set()  # Set is filled when in_tokens are processed
            for tk in in_tokens:
                for a_upstream in self.seq_tokens[tk.name]:  # All upstream actions that set the token
                    for a_in in boundary_actions.ain:  # All initial_pseudo_state actions in this statement
                        self.seq_flows[a_upstream].add(a_in)  # Add that initial_pseudo_state action to the downstream value

    @classmethod
    def valid_param(cls, pname: str, activity: ActivityAP):
        # TODO: Verify that the parameter is in the signature of the specified activity with exception if not
        pass

    @classmethod
    def populate(cls, tr: str, action_text: str, subsys: str, domain: str) -> str:
        """
        Populate an Activity

        :param tr: The name of the open transaction
        :param action_text: Unparsed scrall text
        :param subsys: The subsystem name
        :param domain: The domain name
        :return: The Activity number (Anum)
        """
        Anum = Element.populate_unlabeled_subsys_element(tr=tr, prefix='A', subsystem=subsys, domain=domain)
        Relvar.insert(db=mmdb, tr=tr, relvar='Activity', tuples=[
            Activity_i(Anum=Anum, Domain=domain)
        ])
        return Anum

    @classmethod
    def populate_state(cls, tr: str, state_model: str, sm_type: SMType, actions: str,
                       subsys: str, domain: str, parse_actions: bool, initial_pseudo_state: bool = False) -> dict:
        """

        Args:
            tr: Name of the transaction
            initial_pseudo_state: True if this is an initial state
            state_model: State model name
            sm_type: Lifecycle, Single or Multiple assigner
            actions:
            subsys:
            domain:
            parse_actions:

        Returns:
            Dictionary of state info including parse result
        """

        # Parse scrall in this state and add it to temporary sm dictionary
        action_text = ''.join(actions) + '\n'
        if parse_actions:
            parsed_activity = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        else:
            parsed_activity = None
        # cls.populate_activity(text=action_text, pa=parsed_activity)

        # Create the Susbystem Element and obtain a unique Anum
        Anum = cls.populate(tr=tr, action_text=action_text, subsys=subsys, domain=domain)
        state_info = {'anum': Anum, 'sm_type': sm_type, 'parse': parsed_activity[0],
                      'text': action_text, 'domain': domain}
        Relvar.insert(db=mmdb, tr=tr, relvar='State Activity', tuples=[
            State_Activity_i(Anum=Anum, Domain=domain)
        ])
        if initial_pseudo_state:
            Relvar.insert(db=mmdb, tr=tr, relvar='Delegated Creation Activity', tuples=[
                Delegated_Creation_Activity_i(Anum=Anum, Domain=domain)
            ])
        else:
            Relvar.insert(db=mmdb, tr=tr, relvar='Real State Activity', tuples=[
                Real_State_Activity_i(Anum=Anum, Domain=domain)
            ])
            match sm_type:
                case SMType.LIFECYCLE:
                    # Populate the executing instance (me) flow
                    xi_flow = Flow.populate_instance_flow(cname=state_model, anum=Anum, domain=domain,
                                                          label='me', single=True, activity_tr=tr)
                    Relvar.insert(db=mmdb, tr=tr, relvar='Lifecycle_Activity', tuples=[
                        Lifecycle_Activity_i(Anum=Anum, Domain=domain, Executing_instance_flow=xi_flow.fid)
                    ])
                case SMType.MA:
                    # Populate the executing instance (me) flow
                    partition_flow = Flow.populate_instance_flow(cname=state_model, anum=Anum, domain=domain,
                                                                 label='partition_instance', single=True, activity_tr=tr)
                    Relvar.insert(db=mmdb, tr=tr, relvar='Multiple_Assigner_Activity', tuples=[
                        Multiple_Assigner_Activity_i(Anum=Anum, Domain=domain,
                                                     Partitioning_instance_flow=partition_flow.fid)
                    ])
                case SMType.SA:
                    Single_Assigner_Activity_i(Anum=Anum, Domain=domain)
        return state_info

    def populate_waves(self):
        """
        Populate Wave and Wave Assignment class relvars
        """
        for wave_number, wave_actions in self.waves.items():
            wave_tr = f"wave_{wave_number}"
            Transaction.open(db=mmdb, name=wave_tr)
            Relvar.insert(db=mmdb, relvar="Wave", tuples=[
                Wave_i(Number=wave_number, Activity=self.anum, Domain=self.domain)
            ], tr=wave_tr)
            wa_tuples = [Wave_Assignment_i(Action=a, Activity=self.anum, Domain=self.domain, Wave=wave_number)
                         for a in wave_actions]
            Relvar.insert(db=mmdb, relvar="Wave_Assignment", tuples=wa_tuples, tr=wave_tr)
            Transaction.execute(db=mmdb, name=wave_tr)
        # Relation.print(db=mmdb, variable_name="Wave")
        # Relation.print(db=mmdb, variable_name="Wave_Assignment")

    def initially_enabled_flows(self):
        """
        For a Method Activity, there are three kinds of Flows that are enabled prior to any Action execution.
        In other words, these Flows are enabled before the first Wave executes.

        These are all parameter flows, the executing instance flow, and the optional output flow

        Here we create a relation representing the set of all flow IDs for these flows.
        """
        # Get the executing instance flow (probably always F1, but just to be safe...)
        # It's a referential attribute of Method, so we just project on that

        # Get the method for our Anum and Domain
        R = f"Anum:<{self.anum}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Method', restriction=R)
        # Project on the referential attribute to the flow
        Relation.project(db=mmdb, attributes=("Executing_instance_flow",))
        # Rename it to "Flow"
        Relation.rename(db=mmdb, names={"Executing_instance_flow": "Flow"}, svar_name="xiflow")
        # Relation.print(db=mmdb, variable_name="xiflow")

        # Get the parameter input flows for our Anum and Domain
        R = f"Activity:<{self.anum}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Activity Input', restriction=R)
        # Project on the referential attribute to the flow
        r = Relation.project(db=mmdb, attributes=("Flow",), svar_name="param_flows")
        # Relation.print(db=mmdb, variable_name="param_flows")

        # Get any class accessor flows for our Anum and Domain
        R = f"Activity:<{self.anum}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Class_Accessor', restriction=R)
        # Project on the referential attribute to the flow
        Relation.project(db=mmdb, attributes=("Output_flow",))
        # Rename it to "Flow"
        Relation.rename(db=mmdb, names={"Output_flow": "Flow"}, svar_name="class_flows")
        # Relation.print(db=mmdb, variable_name="class_flows")

        # Now take the union of all three
        Relation.union(db=mmdb, relations=("xiflow", "param_flows", "class_flows"), svar_name="wave_enabled_flows")
        # Relation.print(db=mmdb, variable_name="wave_enabled_flows")

    def initially_executable_actions(self) -> RelationValue:
        """
        Identify all actions that can be executed in the first wave.

        To populate the first wave of execution we need to gather all Actions whose inputs consist entirely
        of Flows that are initially available. In other words, each Action in the initial_pseudo_state Wave will require
        no inputs from any other Action.
        """
        # Get all downstream actions (actions that require input from other actions)

        # First we'll need to pair down the Flow Dependency instances to just those
        # in our Method Activity
        R = f"Activity:<{self.anum}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Flow_Dependency', restriction=R, svar_name="fd")
        # fd relaton set to local Flow Dependency instances

        # Define downstream_actions as the ID's of those Actions that take at least one input from some other Action
        Relation.project(db=mmdb, attributes=("To_action",))  # Actions that are a Flow destination
        Relation.rename(db=mmdb, names={"To_action": "ID"}, svar_name="downstream_actions")

        # Now subtract those downstream actions from the set of unexecuted_actions (all Actions at this point)
        ia = Relation.subtract(db=mmdb, rname1="unexecuted_actions", rname2="downstream_actions",
                               svar_name="executable_actions")
        # Relation.print(db=mmdb, variable_name="executable_actions")
        # Here we are initializing a relation variable named "executable_actions" that will update for each new Wave
        # And in Wave 1, it is the set of initial_pseudo_state actions
        return ia

    def enable_action_outputs(self, source_action_relation: str):
        """
        Given a set of Action IDs as a relation value, get the set of all output Flows for those Actions
        Those Flows are saved in the wave_enabled_flows relation value

        :param source_action_relation: This relation is a set of Action IDs representing the source of the output Flows
        """
        # Lookup all Flow Dependencies where the source action is a From_action and collect the output Flows
        Relation.join(db=mmdb, rname1=source_action_relation, rname2="fd", attrs={"ID": "From_action"})
        Relation.project(db=mmdb, attributes=("Flow",), svar_name="wave_enabled_flows")
        # Relation.print(db=mmdb, variable_name="wave_enabled_flows")

    def assign_waves(self):
        """
        Assign each Action in this Method Activity to a Wave of exe

        We do this by simulating the execution of Actions and propagation of Flow data.

        We start by enabling all initially available Flows and then collecting the Actions soley dependendent
        on those inputs. These Actions are assigned to the first Wave since they can execute immediately
        upon Activity invocation.

        Iteration begins with step 1: We enable all output Flows of those initial_pseudo_state executed Actions

        Then for step 2: We find all downstream Actions yet to be executed solely dependent
        on currently enabled Flows. We assign those Actions to the next Wave, increment the wave counter
        and then repeat step 1.

        We continue until all Actions have executed and been assigned to a Wave of execution.
        """
        # Flow_Dep from_action, to_action, available,
        _logger.info("Assigning actions to waves")

        # Initialize the set of unexecuted Actions to be teh set of all Actions in this Activity
        R = f"Activity:<{self.anum}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Action', restriction=R)
        unex_actions = Relation.project(db=mmdb, attributes=("ID",), svar_name="unexecuted_actions")
        # Relation.print(db=mmdb, variable_name="unexecuted_actions")

        while unex_actions.body:
            # The loop starts with Wave 1 and then repeats the else clause until all actions have been assigned

            # Wave 1
            if self.wave_ctr == 1:
                # Set the wave_enabled_flows relation value to all initially enabled flows
                self.initially_enabled_flows()
                # Set the executable_actions relation value to all initially executable actions
                xactions = self.initially_executable_actions()

                # Initialize the completed_actions relational value to the set of executable_actions
                # We have effectively simulated their execution
                Relation.restrict(db=mmdb, relation="executable_actions", svar_name="completed_actions")
                # Relation.print(db=mmdb, variable_name="completed_actions")
                # Initialize the enabled_flows relational value to this first set of wave_enabled_flows
                # (the initially available flows)
                Relation.restrict(db=mmdb, relation="wave_enabled_flows", svar_name="enabled_flows")
                # Relation.print(db=mmdb, variable_name="enabled_flows")

                # As we move through the remaining Waves we will keep updating the set of completed_actions
                # and the set of enabled_flows until we get them all

            # Weve 2 onward
            else:
                # Proceeding from the Actions completed in the prior Wave,
                # enable the set of Flows output from those Actions
                # and make those the new wave_enabled_flows (replacing the prior set of flows)
                self.enable_action_outputs(source_action_relation="executable_actions")

                # The total set of enabled flows becomes the new wave_enabled_flows relation value added to
                # all earlier enabled flows in the enabled_flows relation value
                Relation.union(db=mmdb, relations=("enabled_flows", "wave_enabled_flows"),
                               svar_name="enabled_flows")
                # Relation.print(db=mmdb, variable_name="enabled_flows")

                # Now for the fun part:
                # For each unexecuted Action, see if its total set of required input Flows is a subset
                # of the currently enabled Flows. If so, this Action can execute and be assigned to the current Wave.

                # We use the summarize command to do the relational magic.
                # The idea is to go through the unexecuted_actions relation value and, for each Action ID
                # execute the sum_expr (summarization expression) yielding a true or false result.
                # Either the Action can or cannot execute. The unexecuted_actions relation is extended with an extra
                # column that holds this boolean result.
                # Then we'll restrict that table to find only the true results and throw away the extra column
                # in the process so that we just end up with a new set of executable_actions (replacing the previous
                # relation value of the same name).

                # Taking it step by step, here we build the sum_expr
                sum_expr = Relation.build_expr(commands=[
                    # the temproary s (summarize) relation represents the current unexecuted action
                    # We join it with the Flow Dependencies for this Activity as the To_action
                    # to obtain the set of action generated inputs it requires.
                    # (we don't care about the non-action generated initial_pseudo_state flows since we know these are always
                    # available)
                    JoinCmd(rname1="s", rname2="fd", attrs={"ID": "To_action"}),
                    ProjectCmd(attributes=("Flow",), relation=None),
                    # And here we see if those flows are a subset of the enabled flows (true or false)
                    SetCompareCmd(rname2="enabled_flows", op=SetOp.subset, rname1=None)
                ])
                # Now we embed the sum_expr in our summarize command
                Relation.summarize(db=mmdb, relation="unexecuted_actions", per_attrs=("ID",),
                                   summaries=(
                                       SumExpr(attr=Attribute(name="Can_execute", type="boolean"), expr=sum_expr),), )
                R = f"Can_execute:<{1}>"  # True is 1, False is 0 in TclRAL and we just want the 1's
                Relation.restrict(db=mmdb, restriction=R)
                # Just take the ID attributes.  After the restrict we don't need the extra boolean attribute anymore
                xactions = Relation.project(db=mmdb, attributes=("ID",), svar_name="executable_actions")
                # Relation.print(db=mmdb, variable_name="executable_actions")
                # And here we replace the set of completed_actions with our new batch of executable_actions
                Relation.restrict(db=mmdb, relation="executable_actions", svar_name="completed_actions")

            # Having processed either the initial_pseudo_state or subsequent waves, we do the same work
            # Add all Action IDs in the executable_actions relation into the current Wave, and increment the counter
            self.waves[self.wave_ctr] = [t['ID'] for t in xactions.body]
            self.wave_ctr += 1
            # print(f"Wave --- [{self.wave_ctr}] ---")
            # Finally, remove the latest completed actions from the set of unexecuted_actions
            unex_actions = Relation.subtract(db=mmdb, rname1="unexecuted_actions", rname2="completed_actions",
                                             svar_name="unexecuted_actions")
            # Relation.print(db=mmdb, variable_name="unexecuted_actions")
            # Rinse and repeat until all the actions are completed
        pass

    def pop_flow_dependencies(self):
        """
        For each activity, determine the flow dependencies among its actions and populate the Flow Dependency class
        """
        # TODO: Optimize redundant read actions ... (moved here from Read Action)
        # TODO: Avoid populating duplicate for reading the same attr set by maintaining dict of action/flows
        # TODO: for the current activity. If duplicate found, return its action id and output flows instead.
        # TODO: Ensure that the existing read action that has no incoming control flows

        # Initialize dict with key for each flow, status to be determined
        R = f"Activity:<{self.anum}>, Domain:<{self.domain}>"
        flow_r = Relation.restrict(db=mmdb, relation='Flow', restriction=R)
        self.flow_path = {f['ID']: {'source': set(), 'dest': set(), 'available': False} for f in flow_r.body}

        # Set each sequence flow dependency first
        # Find all sequence flows
        R = f"Activity:<{self.anum}>, Domain:<{self.domain}>"
        seq_flow_r = Relation.restrict(db=mmdb, relation='Sequence Flow', restriction=R)
        for seq_flow_t in seq_flow_r.body:
            source_action = seq_flow_t["Source_action"]
            seq_fid = seq_flow_t["Flow"]
            sdeps = self.seq_flows[source_action]
            for dest_action in sdeps:
                self.flow_path[seq_fid]['dest'].add(dest_action)
                self.flow_path[seq_fid]['source'].add(source_action)

        # Now proceed through each flow usage class (actions, cases, etc)
        for flow_header in flow_attrs:
            # Get all instances below the flow_header
            R = f"Activity:<{self.anum}>, Domain:<{self.domain}>"
            flow_usage_r = Relation.restrict(db=mmdb, relation=flow_header.cname, restriction=R)
            flow_usage_instances = flow_usage_r.body

            for flow_usage in flow_usage_instances:  # For each instance of this usage
                # If the header specifies an action id
                if flow_header.in_attr:
                    # Header specifies an input flow, thus a destination action
                    input_flow = flow_usage[flow_header.in_attr]
                    if input_flow in self.flow_path[input_flow]['dest']:
                        pass  # Dest added previously
                    self.flow_path[input_flow]['dest'].add(flow_usage[flow_header.id_attr])
                if flow_header.in_attr2:
                    # Header specifies an additional input flow, thus a destination action
                    input_flow = flow_usage[flow_header.in_attr2]
                    if input_flow in self.flow_path[input_flow]['dest']:
                        pass  # Dest added previously
                    self.flow_path[input_flow]['dest'].add(flow_usage[flow_header.id_attr])
                if flow_header.out_attr:
                    output_flow = flow_usage[flow_header.out_attr]
                    if output_flow in self.flow_path[output_flow]['source']:
                        pass  # Source added previously
                    self.flow_path[output_flow]['source'].add(flow_usage[flow_header.id_attr])

        # Mark all flows in Activity that are available in the first wave of execution

        # The single executing instance flow is available
        if self.xiflow:
            self.flow_path[self.xiflow.fid]['available'] = True

        # All activity parameter flows are available
        R = f"Activity:<{self.anum}>, Domain:<{self.domain}>"
        activity_input_r = Relation.restrict(db=mmdb, relation='Activity Input', restriction=R)
        for ai_flow in activity_input_r.body:
            self.flow_path[ai_flow['Flow']]['available'] = True

        # All class accessor flows are available
        R = f"Activity:<{self.anum}>, Domain:<{self.domain}>"
        result = Relation.restrict(db=mmdb, relation='Class_Accessor', restriction=R)
        for ca_flow in result.body:
            self.flow_path[ca_flow['Output_flow']]['available'] = True

        for f, p in self.flow_path.items():
            if not (p['source'] and p['dest']):
                continue
            for source_action in p['source']:
                for dest_action in p['dest']:
                    Relvar.insert(db=mmdb, relvar='Flow_Dependency', tuples=[
                        Flow_Dependency_i(From_action=source_action, To_action=dest_action,
                                          Activity=self.anum, Domain=self.domain, Flow=f)
                    ])