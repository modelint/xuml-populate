""" instance_set.py """

# System
import logging
from typing import Optional, TYPE_CHECKING

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.traverse_action import TraverseAction
from xuml_populate.populate.actions.expressions.class_accessor import ClassAccessor
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.select_action import SelectAction
from xuml_populate.populate.actions.restrict_action import RestrictAction
from xuml_populate.populate.actions.rank_restrict_action import RankRestrictAction
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, SMType, ActivityType
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
    def __init__(self, iset_components, activity: 'Activity', input_instance_flow: Optional[Flow_ap] = None):
        self.component_flow = input_instance_flow
        self.activity = activity
        self.iset_components = iset_components

        self.initial_action = None  # The first action in the chain
        self.final_action = None  # The last action in the chain

        if not input_instance_flow:
            # This will be None when the caller is a single assigner.
            # (A multiple assigner uses the paritioning instance flow as a the implicit starting point in a path)
            # This means that a path such as /R1/R2/Flot won't work because we have no starting point
            # A single assigner would need to specify something like: p/R1/R2/Flot instead, me/self is not available
            # TODO: Handle case where a single assigner processes an instance set

            # This could also be none if there is an upstream action and the flow is in the mmdb, but
            # hasn't yet been looked up for this staement.  Labeled flow input to a decision action, for example
            pass

    def process(self) -> tuple[str, str, Flow_ap]:
        """
        Populate any Actions or Flows corresponding to a sequence of instance set components.
        Return the boundary actions and the resultant output Instance Flow

        Returns:
            output: The initial action id, the final action id, and the output instance flow
        """
        domain = self.activity.domain
        anum = self.activity.anum

        first_action = True  # We use this to recognize the initial action
        for count, comp in enumerate(self.iset_components):
            # We use the count to recognize the final action
            match type(comp).__name__:
                case 'PATH_a':
                    # If this path is the first component, it assumes it is traversing from an executing
                    # or instance (self) or partitioning instance of a multiple assigner.
                    # A single assigner must specify an explicit initial flow which means that it cannot start off
                    # with an implicit /R<n>, rather <inst set>/R<n> instead.
                    if count == 0 and self.activity.atype == ActivityType.STATE and \
                            self.activity.smtype == SMType.SA:
                        msg = (f"Single Assigner traverse action must specify instancse set to begin "
                               f"path (self not defined): {self.activity.activity_path} with path"
                               f"parse: {comp}")
                        _logger.error(msg)
                        raise ActionException(msg)

                    # Path component
                    # Process the path to create the traverse action and obtain the resultant output instance flow
                    traverse_action = TraverseAction(input_instance_flow=self.component_flow, path=comp,
                                                     activity=self.activity)
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
                            raise NoClassOrInstanceFlowForInstanceSetName(path=self.activity.activity_path,
                                                                          text=self.activity.scrall_text,
                                                                          x=self.iset_components.X)
                case 'Criteria_Selection_a':
                    # Process to populate a select action, the output type does not change
                    # since we are selecting on a known class
                    if self.component_flow.content == Content.INSTANCE:
                        sa = SelectAction(
                            input_instance_flow=self.component_flow, selection_parse=comp,
                            activity=self.activity
                        )
                        aid = sa.action_id
                        self.component_flow = sa.output_instance_flow
                        sflows = sa.sflows
                    elif self.component_flow.content == Content.RELATION:
                        ra = RestrictAction(
                            input_relation_flow=self.component_flow, selection_parse=comp,
                            activity=self.activity
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
                                                 activity=self.activity)
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
                case 'Op_a':
                    # The only kind of operation that can return an instance set is a Method
                    # Type operations and external services cannot do this
                    # So we need to validate that we have a proper method invocation statement and then
                    # populate the Method Call

                    single_inst_flow_label = comp.owner if comp.owner != 'implicit' else 'me'
                    # Name on a flow delivering a single instance method target
                    method_name = comp.op_name  # op_name must be a Method name

                    # Validate the single instance flow
                    R = (f"Name:<{single_inst_flow_label}>, Activity:<{self.activity.anum}>, "
                         f"Domain:<{self.activity.domain}>")
                    labeled_flow_r = Relation.restrict(db=mmdb, relation='Labeled Flow', restriction=R)
                    if not labeled_flow_r:
                        msg = f"No labeled flow named {single_inst_flow_label} in {self.activity.activity_path}"
                        _logger.error(msg)
                        raise ActionException(msg)

                    # It must be a single instance flow
                    single_inst_flow_r = Relation.semijoin(db=mmdb, rname2='Single Instance Flow')
                    if not single_inst_flow_r:
                        msg = (f"Method call target [{single_inst_flow_label}] in {self.activity.activity_path} "
                               f"must be a single instance flow")
                        _logger.error(msg)
                        raise ActionException(msg)

                    # Get the class name
                    inst_flow_r = Relation.semijoin(db=mmdb, rname2='Instance Flow')
                    inst_class_name = inst_flow_r.body[0]['Class']

                    # Verify that the method is defined on this class
                    R = f"Name:<{method_name}>, Class:<{inst_class_name}>, Domain:<{self.activity.domain}>"
                    method_r = Relation.restrict(db=mmdb, relation='Method', restriction=R)
                    if not method_r:
                        msg = (f"Called method [{method_name}] not defined on [{inst_class_name}] in "
                               f"{self.activity.activity_path}")
                        _logger.error(msg)
                        raise ActionException(msg)

                    # Method and instance target valid
                    inst_flow_t = inst_flow_r.body[0]
                    method_t = method_r.body[0]
                    from xuml_populate.populate.actions.method_call import MethodCall
                    mcall = MethodCall(method_name=method_name, method_anum=method_t["Anum"], caller_flow=
                                       Flow_ap( fid=inst_flow_t["ID"], content=Content.INSTANCE,
                                                tname=inst_class_name, max_mult=MaxMult.ONE),
                                       parse=comp,
                                       activity=self.activity)
                    ain, aout, self.component_flow = mcall.process()
                    if first_action:
                        self.initial_action = ain
                    self.final_action = aout
                case _:
                    raise Exception
        return self.initial_action, self.final_action, self.component_flow
