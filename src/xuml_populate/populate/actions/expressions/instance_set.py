""" instance_set.py """

import logging
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.traverse_action import TraverseAction
from xuml_populate.populate.actions.expressions.class_accessor import ClassAccessor
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.select_action import SelectAction
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from pyral.relation import Relation
from pyral.transaction import Transaction
from xuml_populate.exceptions.action_exceptions import NoClassOrInstanceFlowForInstanceSetName, \
    SelectionOnScalarFlow

_logger = logging.getLogger(__name__)


class InstanceSet:
    """
    An instance set is a Scrall grammar element representing a chain of one or more components. Each component is a
    parse element that populates as one or more Actions or Flows. Each Action outputs an instance flow which is fed
    into the next Action until a final Instance Flow output is generated.

    Our goal is to process each component and populate the associated Actions and Flows. Along the way, we verify
    that the requested elements are consistent with the underlying class model and any Flows previously defined
    in the same Activity. An exception is thrown if there is any inconsistency.
    """

    component_flow = None  # Output flow from the most recenlty populated component
    initial_action = None  # The first action in the chain
    final_action = None  # The last action in the chain

    @classmethod
    def process(cls, input_instance_flow: Flow_ap, iset_components,
                activity_data: Activity_ap) -> ( str, str, Flow_ap):
        """
        Populate any Actions or Flows corresponding to a sequence of instance set components.
        Return the boundary actions and the resultant output Instance Flow

        :param input_instance_flow: This Flow provides input at the beginning of the chain
        :param iset_components: The components in the instance set
        :param activity_data:  General information about the enclosing anum, anum, domain, etc
        :return: The initial action id, the final action id, and the output instance flow
        """
        cls.initial_action = None  # Clear out whatever old values might remain from a prior instance set
        cls.final_action = None
        cls.component_flow = input_instance_flow  # This will be input to the first component
        domain = activity_data.domain
        anum = activity_data.anum

        first_action = True  # We use this to recognize the initial action
        for count, comp in enumerate(iset_components):
            # We use the count to recognize the final action
            match type(comp).__name__:
                case 'PATH_a':
                    # Path component
                    # Process the path to create the traverse action and obtain the resultant output instance flow
                    traverse_action = TraverseAction()
                    aid, cls.component_flow = traverse_action.build_path(input_instance_flow=cls.component_flow,
                                                                        path=comp, activity_data=activity_data)
                    # Data flow to/from actions within the instance_set
                    if first_action:
                        # For the first component, there can be dflow input from another action
                        cls.initial_action = aid
                        first_action = False  # The first action has been encountered and recognized as initial
                    if count == len(iset_components) - 1:
                        # For the last component, there can be no dflow output to another action
                        cls.final_action = aid
                case 'N_a':
                    # Name component
                    # Is it a class name?  If so, we'll need a Class Accessor populated if we don't have one already
                    class_flow = ClassAccessor.populate(name=comp.name, anum=anum, domain=domain)
                    if class_flow:
                        # We have a Class Accessor either previously or just now populated
                        # Set its output flow to the current component output
                        cls.component_flow = Flow_ap(fid=class_flow, content=Content.INSTANCE,
                                                     tname=comp.name, max_mult=MaxMult.MANY)
                    else:
                        # Is it a Non Scalar Flow?
                        ns_flow = Flow.find_labeled_ns_flow(name=comp.name, anum=anum, domain=domain)
                        if ns_flow:
                            cls.component_flow = ns_flow
                        else:
                            # Either there is no corresponding flow or it is a Scalar Flow
                            raise NoClassOrInstanceFlowForInstanceSetName(path=activity_data.activity_path,
                                                                          text=activity_data.scrall_text,
                                                                          x=iset_components.X)
                case 'Selection_a':
                    # Process to populate a select action, the output type does not change
                    # since we are selecting on a known class
                    aid, cls.component_flow, sflows = SelectAction.populate(
                        input_instance_flow=cls.component_flow, selection_parse=comp, activity_data=activity_data)

                    cls.final_action = aid
                case _:
                    raise Exception
        return cls.initial_action, cls.final_action, cls.component_flow
