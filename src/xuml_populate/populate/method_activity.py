""" method_activity.py -- Process all execution components of a method's activity """

# System
import logging
from typing import NamedTuple

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from scrall.parse.parser import ScrallParser

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Activity_ap, Boundary_Actions
from xuml_populate.populate.xunit import ExecutionUnit
from xuml_populate.populate.mmclass_nt import (Activity_i, Asynchronous_Activity_i, State_Activity_i,
                                               Synchronous_Activity_i, Flow_Dependency_i)
from xuml_populate.exceptions.action_exceptions import ActionException, MethodXIFlowNotPopulated

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


class MethodActivity:

    def __init__(self, name: str, class_name: str, method_data, activity_data, domain: str):

        self.name = name
        self.class_name = class_name
        self.activity_data = activity_data
        self.method_data = method_data
        self.domain = domain
        self.wave = 1  # Initialize wave counter
        self.waves = dict()

        self.pop_xunits()
        self.pop_flow_dependencies()
        self.assign_waves()

    def next_xactions(self):
        pass

    def assign_waves(self):
        """
        For each activity, assign each action to a Wave
        """
        # Flow_Dep from_action, to_action, available,
        _logger.info("Populating flow dependencies")

        # Identify all actions in the first Wave
        # These are all actions driven only by the xi_inst_flow (executing instance), class accessor flows,
        # and parameter input flows.
        # In fact, we can just find all actions in the flow dependency graph that have no inputs

        # Get the ids of all Actions
        R = f"Activity:<{self.activity_data['anum']}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Action', restriction=R)
        Relation.project(db=mmdb, attributes=("ID",), svar_name="all_action_ids")
        # Get the ids of all destination Actions in Flow Dependency
        R = f"Activity:<{self.activity_data['anum']}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Flow_Dependency', restriction=R)
        Relation.project(db=mmdb, attributes=("To_action",), svar_name="to_action_ids")
        # Subtract the destination action ids from all action ids to get those actions that are not
        # destinations of any flow dependency.  These are the actions that should execute in the first wave
        # since they do not require any flow input from another action.
        Relation.rename(db=mmdb, names={"To_action": "ID"}, svar_name="to_action_ids")  # headers must match
        result = Relation.subtract(db=mmdb, rname1="all_action_ids", rname2="to_action_ids")
        self.waves[self.wave] = [t['ID'] for t in result.body]


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
