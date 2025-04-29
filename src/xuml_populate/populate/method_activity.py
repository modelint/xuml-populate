""" method_activity.py -- Process all execution components of a method's activity """

# System
import logging
from typing import NamedTuple

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from pyral.rtypes import JoinCmd, ProjectCmd, SetCompareCmd, SetOp, Attribute, SumExpr, RelationValue

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Activity_ap
from xuml_populate.populate.xunit import ExecutionUnit
from xuml_populate.populate.mmclass_nt import Flow_Dependency_i, Wave_i, Wave_Assignment_i
from xuml_populate.exceptions.action_exceptions import MethodXIFlowNotPopulated

_logger = logging.getLogger(__name__)

# TODO: This can be generated later by make_repo, ensure each name ends with 'Action'
class UsageAttrs(NamedTuple):
    cname: str
    id_attr: str | None
    in_attr: str | None
    out_attr: str | None


flow_attrs = [
    UsageAttrs(cname='Select_Action', id_attr='ID', in_attr='Input_flow', out_attr=None),
    UsageAttrs(cname='Traverse_Action', id_attr='ID', in_attr='Source_flow', out_attr='Destination_flow'),
    UsageAttrs(cname='Many_Select', id_attr='ID', in_attr=None, out_attr='Output_flow'),
    UsageAttrs(cname='Single_Select', id_attr='ID', in_attr=None, out_attr='Output_flow'),
    UsageAttrs(cname='Table_Action', id_attr='ID', in_attr='Input_a_flow', out_attr='Output_flow'),
    UsageAttrs(cname='Set_Action', id_attr='ID', in_attr='Input_b_flow', out_attr=None),
    UsageAttrs(cname='Read_Action', id_attr='ID', in_attr='Instance_flow', out_attr=None),
    UsageAttrs(cname='Attribute_Read_Access', id_attr='Read_action', in_attr=None, out_attr='Output_flow'),
    UsageAttrs(cname='Comparison_Criterion', id_attr='Action', in_attr='Value', out_attr=None),
    UsageAttrs(cname='Switched_Data_Flow', id_attr=None, in_attr='Input_flow', out_attr='Output_flow'),
    UsageAttrs(cname='Case', id_attr='Switch_action', in_attr=None, out_attr='Flow'),
    UsageAttrs(cname='Control_Dependency', id_attr='Action', in_attr='Control_flow', out_attr=None),
    UsageAttrs(cname='Extract_Action', id_attr='ID', in_attr='Input_tuple', out_attr='Output_scalar'),
]

# For debugging
from collections import namedtuple
Action_i = namedtuple('Action_i', 'ID')

class MethodActivity:

    def __init__(self, name: str, class_name: str, method_data, activity_data, domain: str):

        self.name = name
        self.class_name = class_name
        self.activity_data = activity_data
        self.anum = self.activity_data['anum']
        self.method_data = method_data
        self.domain = domain
        self.wave_ctr = 1  # Initialize wave counter
        self.waves = dict()
        self.xactions = None

        self.pop_xunits()
        self.pop_flow_dependencies()
        self.assign_waves()
        self.populate_waves()

        # Now we can populate the Wave and Wave Assignment relvars
        pass

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
        Relation.print(db=mmdb, variable_name="Wave")
        Relation.print(db=mmdb, variable_name="Wave_Assignment")

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
        R = f"Anum:<{self.activity_data['anum']}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Method', restriction=R)
        # Project on the referential attribute to the flow
        Relation.project(db=mmdb, attributes=("Executing_instance_flow",))
        # Rename it to "Flow"
        Relation.rename(db=mmdb, names={"Executing_instance_flow": "Flow"}, svar_name="xi_flow")
        Relation.print(db=mmdb, variable_name="xi_flow")

        # Get the parameter input flows for our Anum and Domain
        R = f"Activity:<{self.activity_data['anum']}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Parameter', restriction=R)
        # Project on the referential attribute to the flow
        Relation.project(db=mmdb, attributes=("Input_flow",))
        # Rename it to "Flow"
        Relation.rename(db=mmdb, names={"Input_flow": "Flow"}, svar_name="param_flows")
        Relation.print(db=mmdb, variable_name="param_flows")

        # Get any class accessor flows for our Anum and Domain
        R = f"Activity:<{self.activity_data['anum']}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Class_Accessor', restriction=R)
        # Project on the referential attribute to the flow
        Relation.project(db=mmdb, attributes=("Output_flow",))
        # Rename it to "Flow"
        Relation.rename(db=mmdb, names={"Output_flow": "Flow"}, svar_name="class_flows")
        Relation.print(db=mmdb, variable_name="class_flows")

        # Now take the union of all three
        Relation.union(db=mmdb, relations=("xi_flow", "param_flows", "class_flows"), svar_name="wave_enabled_flows")
        Relation.print(db=mmdb, variable_name="wave_enabled_flows")

    def initially_executable_actions(self) -> RelationValue:
        """
        Identify all actions that can be executed in the first wave.

        To populate the first wave of execution we need to gather all Actions whose inputs consist entirely
        of Flows that are initially available. In other words, each Action in the initial Wave will require
        no inputs from any other Action.
        """
        # Get all downstream actions (actions that require input from other actions)

        # First we'll need to pair down the Flow Dependency instances to just those
        # in our Method Activity
        R = f"Activity:<{self.activity_data['anum']}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Flow_Dependency', restriction=R, svar_name="fd")
        # fd relaton set to local Flow Dependency instances

        # Define downstream_actions as the ID's of those Actions that take at least one input from some other Action
        Relation.project(db=mmdb, attributes=("To_action",))  # Actions that are a Flow destination
        Relation.rename(db=mmdb, names={"To_action": "ID"}, svar_name="downstream_actions")

        # Now subtract those downstream actions from the set of unexecuted_actions (all Actions at this point)
        ia = Relation.subtract(db=mmdb, rname1="unexecuted_actions", rname2="downstream_actions", svar_name="executable_actions")
        Relation.print(db=mmdb, variable_name="executable_actions")
        # Here we are initializing a relation variable named "executable_actions" that will update for each new Wave
        # And in Wave 1, it is the set of initial actions
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
        Relation.print(db=mmdb, variable_name="wave_enabled_flows")

    def assign_waves(self):
        """
        Assign each Action in this Method Activity to a Wave of exe

        We do this by simulating the execution of Actions and propagation of Flow data.

        We start by enabling all initially available Flows and then collecting the Actions soley dependendent
        on those inputs. These Actions are assigned to the first Wave since they can execute immediately
        upon Activity invocation.

        Iteration begins with step 1: We enable all output Flows of those initial executed Actions

        Then for step 2: We find all downstream Actions yet to be executed solely dependent
        on currently enabled Flows. We assign those Actions to the next Wave, increment the wave counter
        and then repeat step 1.

        We continue until all Actions have executed and been assigned to a Wave of execution.
        """
        # Flow_Dep from_action, to_action, available,
        _logger.info("Assigning actions to waves")

        # Initialize the set of unexecuted Actions to be teh set of all Actions in this Activity
        R = f"Activity:<{self.activity_data['anum']}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Action', restriction=R)
        unex_actions = Relation.project(db=mmdb, attributes=("ID",), svar_name="unexecuted_actions")
        Relation.print(db=mmdb, variable_name="unexecuted_actions")

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
                Relation.print(db=mmdb, variable_name="completed_actions")
                # Initialize the enabled_flows relational value to this first set of wave_enabled_flows
                # (the initially available flows)
                Relation.restrict(db=mmdb, relation="wave_enabled_flows", svar_name="enabled_flows")
                Relation.print(db=mmdb, variable_name="enabled_flows")

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
                Relation.print(db=mmdb, variable_name="enabled_flows")

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
                    # (we don't care about the non-action generated initial flows since we know these are always
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
                Relation.print(db=mmdb, variable_name="executable_actions")
                # And here we replace the set of completed_actions with our new batch of executable_actions
                Relation.restrict(db=mmdb, relation="executable_actions", svar_name="completed_actions")

            # Having processed either the initial or subsequent waves, we do the same work
            # Add all Action IDs in the executable_actions relation into the current Wave, and increment the counter
            self.waves[self.wave_ctr] = [t['ID'] for t in xactions.body]
            self.wave_ctr += 1
            print(f"Wave --- [{self.wave_ctr}] ---")
            # Finally, remove the latest completed actions from the set of unexecuted_actions
            unex_actions = Relation.subtract(db=mmdb, rname1="unexecuted_actions", rname2="completed_actions", svar_name="unexecuted_actions")
            Relation.print(db=mmdb, variable_name="unexecuted_actions")
            # Rinse and repeat until all the actions are completed
        pass

    def pop_flow_dependencies(self):
        """
        For each method activity, determine the flow dependencies among its actions and populate the Flow Dependency class
        """
        # Initialize dict with key for each flow, status to be determined
        R = f"Domain:<{self.domain}>"
        result = Relation.restrict(db=mmdb, relation='Flow', restriction=R)
        flow_path = {f['ID']: {'source': set(), 'dest': set(), 'merge': None, 'available': False,
                               'conditional': False} for f in result.body}

        # Now proceed through each flow usage class (actions, cases, etc)
        for flow_header in flow_attrs:
            # Get all instances below the flow_header
            R = f"Domain:<{self.domain}>"
            result = Relation.restrict(db=mmdb, relation=flow_header.cname, restriction=R)
            flow_usage_instances = result.body

            for flow_usage in flow_usage_instances:  # For each instance of this usage
                if flow_header.id_attr:
                    # If the header specifies an action id
                    if flow_header.in_attr:
                        # Header specifies an input flow, thus a destination action
                        input_flow = flow_usage[flow_header.in_attr]
                        if input_flow in flow_path[input_flow]['dest']:
                            pass  # Dest added previously
                        flow_path[input_flow]['dest'].add(flow_usage[flow_header.id_attr])
                    if flow_header.out_attr:
                        output_flow = flow_usage[flow_header.out_attr]
                        if output_flow in flow_path[output_flow]['source']:
                            pass  # Source added previously
                        flow_path[output_flow]['source'].add(flow_usage[flow_header.id_attr])
                        if flow_header.cname == 'Case':
                            flow_path[output_flow]['conditional'] = True
                else:
                    # Usage does not specify any action (conditional)
                    input_flow = flow_usage[flow_header.in_attr]
                    merge_flow = flow_usage[flow_header.out_attr]
                    flow_path[input_flow]['merge'] = merge_flow

        # Mark all flows in method that are available in the first wave of execution

        # The single executing instance flow is available
        R = f"Anum:<{self.activity_data['anum']}>, Domain:<{self.domain}>"
        result = Relation.restrict(db=mmdb, relation='Method', restriction=R)
        if not result.body:
            msg = f"No executing instance populated for method: {self.domain}::{self.class_name}.{self.name}"
            _logger.error(msg)
            raise MethodXIFlowNotPopulated(msg)
        method_xi_flow = result.body[0]['Executing_instance_flow']
        flow_path[method_xi_flow]['available'] = True

        # All method parameter flows are available
        R = f"Activity:<{self.activity_data['anum']}>, Domain:<{self.domain}>"
        result = Relation.restrict(db=mmdb, relation='Parameter', restriction=R)
        for pflow in result.body:
            flow_path[pflow['Input_flow']]['available'] = True

        # All class accessor flows are available
        R = f"Activity:<{self.activity_data['anum']}>, Domain:<{self.domain}>"
        result = Relation.restrict(db=mmdb, relation='Class_Accessor', restriction=R)
        for ca_flow in result.body:
            flow_path[ca_flow['Output_flow']]['available'] = True

        # Resolve any merged flows into the data switch output
        for f, p in flow_path.items():
            if p['merge']:
                p['dest'].update(flow_path[p['merge']]['dest'])

        for f, p in flow_path.items():
            if not (p['source'] and p['dest']):
                continue
            for source_action in p['source']:
                for dest_action in p['dest']:
                    Relvar.insert(db=mmdb, relvar='Flow_Dependency', tuples=[
                        Flow_Dependency_i(From_action=source_action, To_action=dest_action,
                                          Activity=self.activity_data['anum'], Domain=self.domain, Flow=f,
                                          Conditional=p['conditional'], Merge=bool(p['merge']))
                    ])
                pass
            pass
        pass

    pass  # Method
    pass  # Populate

    def pop_xunits(self):

        _logger.info(f"Populating method execution units: {self.class_name}.{self.name}")
        # Look up signature
        R = f"Method:<{self.name}>, Class:<{self.class_name}>, Domain:<{self.domain}>"
        result = Relation.restrict(db=mmdb, relation='Method_Signature', restriction=R)
        if not result.body:
            # TODO: raise exception here
            pass
        signum = result.body[0]['SIGnum']

        # Look up xi flow
        R = f"Name:<{self.name}>, Class:<{self.class_name}>, Domain:<{self.domain}>"
        result = Relation.restrict(db=mmdb, relation='Method', restriction=R)
        if not result.body:
            # TODO: raise exception here
            pass
        xi_flow_id = result.body[0]['Executing_instance_flow']
        method_path = f"{self.domain}:{self.class_name}:{self.name}.mtd"

        aparse = self.activity_data['parse']
        activity_detail = Activity_ap(anum=self.activity_data['anum'], domain=self.domain,
                                      cname=self.class_name, sname=None, eename=None, opname=self.name,
                                      xiflow=xi_flow_id, activity_path=method_path, scrall_text=aparse[1])
        seq_flows = {}
        seq_labels = set()
        # for xunit in aparse[0]:
        for count, xunit in enumerate(aparse[0]):  # Use count for debugging
            c = count + 1
            # print(f"Processing statement: {c}")
            if type(xunit.statement_set.statement).__name__ == 'Output_Flow_a':
                ExecutionUnit.process_synch_output(activity_data=activity_detail,
                                                   synch_output=xunit.statement_set.statement)
            else:
                boundary_actions = ExecutionUnit.process_method_statement_set(
                    activity_data=activity_detail, statement_set=xunit.statement_set)

            # Process any input or output tokens
            # if output_tk not in seq_flows:
            # Get a set of terminal actions
            # seq_flows[output_tk] = {'from': [terminal_actions], 'to': []}
        pass
