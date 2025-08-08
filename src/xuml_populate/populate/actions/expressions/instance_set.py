""" instance_set.py """

# System
import logging

# xUML Populate
from xuml_populate.populate.actions.traverse_action import TraverseAction
from xuml_populate.populate.actions.expressions.class_accessor import ClassAccessor
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.select_action import SelectAction
from xuml_populate.populate.actions.restrict_action import RestrictAction
from xuml_populate.populate.actions.rank_restrict_action import RankRestrictAction
from xuml_populate.populate.actions.aparse_types import (Flow_ap, MaxMult, Content, ActivityAP, SMType,
                                                         StateActivityAP, MethodActivityAP)
from xuml_populate.exceptions.action_exceptions import *

_logger = logging.getLogger(__name__)


class InstanceSet:
    """
    An instance set is a Scrall grammar element representing a chain of one or more components. Each component is a
    parse element that populates as one or more Actions or Flows. Each Action outputs an instance flow which is fed
    into the next Action until a final Instance Flow output is generated.

    Our goal is to process each component and populate the associated Actions and Flows. Along the way, we verify
    that the requested elements are consistent with the underlying class model and any Flows previously defined
    in the same Activity. An exception is thrown if there is any inconsistency.

    Args:
        input_instance_flow: This Flow provides input at the beginning of the chain
        iset_components: The components in the instance set
        activity_data: General information about the enclosing anum, anum, domain, etc
    """
    def __init__(self, input_instance_flow: Flow_ap | None, iset_components, activity_data: ActivityAP):
        self.component_flow = input_instance_flow
        self.activity_data = activity_data
        self.iset_components = iset_components

        self.initial_action = None  # The first action in the chain
        self.final_action = None  # The last action in the chain

        if not input_instance_flow:
            # This will be None when the caller is a single assigner.
            # (A multiple assigner uses the paritioning instance flow as a the implicit starting point in a path)
            # This means that a path such as /R1/R2/Flot won't work because we have no starting point
            # A single assigner would need to specify something like: p/R1/R2/Flot instead, me/self is not available
            # TODO: Handle case where a single assigner processes an instance set
            pass

    def process(self) -> ( str, str, Flow_ap):
        """
        Populate any Actions or Flows corresponding to a sequence of instance set components.
        Return the boundary actions and the resultant output Instance Flow

        Returns:
            output: The initial action id, the final action id, and the output instance flow
        """
        domain = self.activity_data.domain
        anum = self.activity_data.anum

        first_action = True  # We use this to recognize the initial action
        for count, comp in enumerate(self.iset_components):
            # We use the count to recognize the final action
            match type(comp).__name__:
                case 'PATH_a':
                    # If this path is the first component, it assumes it is traversing from an executing
                    # or instance (self) or partitioning instance of a multiple assigner.
                    # A single assigner must specify an explicit initial flow which means that it cannot start off
                    # with an implicit /R<n>, rather <inst set>/R<n> instead.
                    if count == 0 and isinstance(self.activity_data, StateActivityAP) and \
                            self.activity_data.smtype == SMType.SA:
                        msg = (f"Single Assigner traverse action must specify instancse set to begin "
                               f"path (self not defined): {self.activity_data.activity_path} with path"
                               f"parse: {comp}")
                        _logger.error(msg)
                        raise PathFromSelfOnAssigner

                    # Path component
                    # Process the path to create the traverse action and obtain the resultant output instance flow
                    traverse_action = TraverseAction(input_instance_flow=self.component_flow, path=comp,
                                                     activity_data=self.activity_data)
                    aid = traverse_action.action_id
                    self.component_flow = traverse_action.output_flow

                    # Data flow to/from actions within the instance_set
                    if first_action:
                        # For the first component, there can be dflow input from another action
                        self.initial_action = aid
                        first_action = False  # The first action has been encountered and recognized as initial
                    if count == len(self.iset_components) - 1:
                        # For the last component, there can be no dflow output to another action
                        self.final_action = aid
                case 'N_a':
                    # Name component
                    # Is it a class name?  If so, we'll need a Class Accessor populated if we don't have one already
                    class_flow = ClassAccessor.populate(name=comp.name, anum=anum, domain=domain)
                    if class_flow:
                        # We have a Class Accessor either previously or just now populated
                        # Set its output flow to the current component output
                        self.component_flow = Flow_ap(fid=class_flow, content=Content.INSTANCE,
                                                      tname=comp.name, max_mult=MaxMult.MANY)
                    else:
                        # Is it a Non Scalar Flow?
                        ns_flow = Flow.find_labeled_ns_flow(name=comp.name, anum=anum, domain=domain)
                        if ns_flow:
                            self.component_flow = ns_flow
                        else:
                            # Either there is no corresponding flow or it is a Scalar Flow
                            raise NoClassOrInstanceFlowForInstanceSetName(path=self.activity_data.activity_path,
                                                                          text=self.activity_data.scrall_text,
                                                                          x=self.iset_components.X)
                case 'Criteria_Selection_a':
                    # Process to populate a select action, the output type does not change
                    # since we are selecting on a known class
                    if self.component_flow.content == Content.INSTANCE:
                        sa = SelectAction(
                            input_instance_flow=self.component_flow, selection_parse=comp,
                            activity_data=self.activity_data
                        )
                        aid = sa.action_id
                        self.component_flow = sa.output_instance_flow
                        sflows = sa.sflows
                    elif self.component_flow.content == Content.RELATION:
                        ra = RestrictAction(
                            input_relation_flow=self.component_flow, selection_parse=comp,
                            activity_data=self.activity_data
                        )
                        aid = ra.action_id
                        self.component_flow = ra.output_relation_flow
                        sflows = ra.sflows
                    else:
                        pass  # TODO: Exception (can't be scalar)
                    # Data flow to/from actions within the instance_set
                    if first_action:
                        # For the first component, there can be dflow input from another action
                        self.initial_action = aid
                        first_action = False  # The first action has been encountered and recognized as initial
                    if count == len(self.iset_components) - 1:
                        # For the last component, there can be no dflow output to another action
                        self.final_action = aid
                case 'Rank_Selection_a':
                    ranksel = RankRestrictAction(input_relation_flow=self.component_flow, selection_parse=comp,
                                                 activity_data=self.activity_data)
                    aid = ranksel.action_id
                    self.component_flow = ranksel.output_relation_flow
                    # Data flow to/from actions within the instance_set
                    if first_action:
                        # For the first component, there can be dflow input from another action
                        self.initial_action = aid
                        first_action = False  # The first action has been encountered and recognized as initial
                    if count == len(self.iset_components) - 1:
                        # For the last component, there can be no dflow output to another action
                        self.final_action = aid
                case _:
                    raise Exception
        return self.initial_action, self.final_action, self.component_flow
