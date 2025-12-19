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

from xuml_populate.config import mmdb
from xuml_populate.populate.actions.traverse_action import TraverseAction
from xuml_populate.populate.actions.create_action import CreateAction
from xuml_populate.populate.actions.external_operation import ExternalOperation
from xuml_populate.populate.actions.expressions.class_accessor import ClassAccessor
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.select_action import SelectAction
from xuml_populate.populate.actions.restrict_action import RestrictAction
from xuml_populate.populate.actions.rank_restrict_action import RankRestrictAction
from xuml_populate.populate.actions.type_action import TypeAction
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, SMType, ActivityType
from xuml_populate.exceptions.action_exceptions import *

if __debug__:
    from xuml_populate.utility import print_mmdb

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
    def __init__(self, iset_components, activity: 'Activity', input_instance_flow: Optional[Flow_ap] = None):
        """
        Gather all of the data required to resolve an instance set into an instance flow

        Args:
            iset_components: The Scrall grammar series of components forming a linear instance data flow
            activity: The enclosing activity object
            input_instance_flow: This Flow provides input at the beginning of the chain
        """
        self.component_flow = input_instance_flow
        self.activity = activity
        self.iset_components = iset_components

        self.initial_action = None  # The first action in the chain
        self.final_action = None  # The last action in the chain
        self.to_many_assoc_on_one = False  # Default setting

        if not input_instance_flow:
            # This will be None when the caller is a single assigner.
            # (A multiple assigner uses the paritioning instance flow as a the implicit starting point in a path)
            # This means that a path such as /R1/R2/Flot won't work because we have no starting point
            # A single assigner would need to specify something like: p/R1/R2/Flot instead, me/self is not available
            # TODO: Handle case where a single assigner processes an instance set

            # This could also be none if there is an upstream action and the flow is in the mmdb, but
            # hasn't yet been looked up for this staement.  Labeled flow input to a decision action, for example
            pass

    def process(self, write_to_attr: bool = False) -> tuple[str, str, Optional[Flow_ap]]:
        """
        Populate any Actions or Flows corresponding to a sequence of instance set components.
        Return the boundary actions and the resultant output Instance Flow

        Args:
            write_to_attr: By default, we assume that this expression is the right hand side of an assignment.
                This means that the output flow will be passed back to the caller so it can be processed and assign
                assigned to some flow on the the lhs.

                But if this expression is a call invocation AND it starts off with a qualified or unqualified attribute,
                set this to False and a write action will be appended at the end targeting the initiating attribute and
                no output flow will be returned.

        Returns:
            output: The initial action id, the final action id, and the output instance flow. If no
                Output flow is returned, it means that the result is not an instance set and the caller should
                probably try looking for a scalar flow (scalar expression) instead.
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
                    # A single assigner must specify an explicit initial_which means that it cannot start off
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
                    aid = traverse_action.action_id  # Action ID
                    self.component_flow = traverse_action.output_flow
                    self.to_many_assoc_on_one = traverse_action.to_many_assoc_on_one

                    # Data flow to/from actions within the instance_set
                    if first_action:
                        # For the first component, there can be data flow input from another action
                        self.initial_action = aid
                        first_action = False  # The first action has been encountered and recognized as initial action
                    if count == len(self.iset_components) - 1:
                        # For the last component, there can be no dflow output to another action
                        self.final_action = aid
                case 'N_a' | 'IN_a':
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
                        ns_flows = Flow.find_labeled_ns_flow(name=comp.name, anum=anum, domain=domain)
                        ns_flow = ns_flows[0] if ns_flows else None
                        # TODO: Check case where multiple flows are returned
                        if ns_flow:
                            self.component_flow = ns_flow
                        else:
                            return '', '', None
                            # Either no flow exists, or the flow is a Scalar flow
                            # In any case, there is no instance set flow to return
                            # TODO: The empty strings are returned instead of None's because many usages use
                            # TODO: _, _, flow  Should change this the returned tuple as a whole is optional
                case 'Criteria_Selection_a':
                    # Process to populate a select action, the output type does not change
                    # since we are selecting on a known class
                    if self.component_flow.content == Content.INSTANCE:
                        sa = SelectAction(
                            input_instance_flow=self.component_flow, selection_parse=comp,
                            activity=self.activity, hop_to_many_assoc_from_one_instance=self.to_many_assoc_on_one
                        )
                        if sa.ain:
                            # If the select action created any upstream action, make that the initial action
                            # of this instance set
                            self.initial_action = sa.ain
                        aid = sa.action_id if not sa.ain else sa.ain
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
                        first_action = False  # The first action has been encountered and recognized as initial action
                    if count == len(self.iset_components) - 1:
                        # For the last component, there can be no dflow output to another action
                        self.final_action = aid
                case 'Rank_Selection_a':
                    rr_action = RankRestrictAction(input_flow=self.component_flow, selection_parse=comp,
                                                   activity=self.activity)
                    aid, output_rflow = rr_action.populate()
                    self.component_flow = output_rflow
                    # Data flow to/from actions within the instance_set
                    if first_action:
                        # For the first component, there can be dflow input from another action
                        self.initial_action = aid
                        first_action = False  # The first action has been encountered and recognized as initial action
                    if count == len(self.iset_components) - 1:
                        # For the last component, there can be no dflow output to another action
                        self.final_action = aid
                case 'Op_a':
                    # By examining the owner component we can determine whether the operation is a Method or
                    # a type operation on a Scalar ipnut
                    if comp.owner == '_external':
                        # TODO: Process external services
                        # At may return a scalar expression depending on external service definition
                        # So we look up the type External Operation Output
                        R = f"Name:<{comp.op_name}>, Domain:<{domain}>"
                        ext_service_r = Relation.restrict(db=mmdb, relation="External Service", restriction=R)
                        if not ext_service_r.body:
                            msg = f"Undefined external service {comp.op_name} in: {self.activity.activity_path}"
                            _logger.error(msg)
                            raise ActionException(msg)
                        ext_op_output_r = Relation.semijoin(db=mmdb, rname2='External Operation Output', attrs={
                            'Name': 'Operation', 'Domain':'Domain'
                        })
                        if ext_op_output_r.body:
                            eop = ExternalOperation(parse=comp, activity=self.activity)
                            ain, aout, output_flow = eop.populate()
                            self.initial_action = ain
                            self.final_action = aout
                            self.component_flow = output_flow
                        else:
                            pass
                    elif comp.owner == '_implicit':
                        # We use the component flow as input if there is one
                        op_name = comp.op_name  # op_name must be a Method name

                        # Verify that the input flow is a single instance flow
                        if self.component_flow.max_mult != MaxMult.ONE:
                            msg = (f"Method call target [{self.component_flow}] in {self.activity.activity_path} "
                                   f"must be a single instance flow")
                            _logger.error(msg)
                            raise ActionException(msg)

                        # Verify that the method is defined on the component flow class
                        R = f"Name:<{op_name}>, Class:<{self.component_flow.tname}>, Domain:<{self.activity.domain}>"
                        method_r = Relation.restrict(db=mmdb, relation='Method', restriction=R)
                        if not method_r:
                            msg = (f"Called method [{op_name}] not defined on [{self.component_flow.tname}] in "
                                   f"{self.activity.activity_path}")
                            _logger.error(msg)
                            raise ActionException(msg)

                        # Method and instance target valid
                        method_t = method_r.body[0]
                        from xuml_populate.populate.actions.method_call import MethodCall
                        mcall = MethodCall(
                            method_name=op_name, method_anum=method_t["Anum"],
                            caller_flow=self.component_flow,
                            parse=comp, activity=self.activity
                        )
                        ain, aout, self.component_flow = mcall.process()
                        if first_action:
                            self.initial_action = ain
                        self.final_action = aout
                        pass
                    else:
                        target_flow_label = comp.owner if comp.owner != '_implicit' else 'me'
                        # Name on a flow delivering a single instance method target
                        op_name = comp.op_name

                        # Validate the single instance flow
                        R = (f"Name:<{target_flow_label}>, Activity:<{self.activity.anum}>, "
                             f"Domain:<{self.activity.domain}>")
                        sv_labeled_flow = 'sv_lflow'  # Result used in two semijoins below
                        labeled_flow_r = Relation.restrict(db=mmdb, relation='Labeled Flow', restriction=R,
                                                           svar_name=sv_labeled_flow)
                        if not labeled_flow_r:
                            msg = f"No labeled flow named {target_flow_label} in {self.activity.activity_path}"
                            _logger.error(msg)
                            raise ActionException(msg)

                        # Is it a single instance flow?
                        single_inst_flow_r = Relation.semijoin(db=mmdb, rname2='Single Instance Flow')
                        if single_inst_flow_r.body:
                            # Get the class name
                            inst_flow_r = Relation.semijoin(db=mmdb, rname2='Instance Flow')
                            inst_class_name = inst_flow_r.body[0]['Class']

                            # Verify that the method is defined on this class
                            R = f"Name:<{op_name}>, Class:<{inst_class_name}>, Domain:<{self.activity.domain}>"
                            method_r = Relation.restrict(db=mmdb, relation='Method', restriction=R)
                            if not method_r:
                                msg = (f"Called method [{op_name}] not defined on [{inst_class_name}] in "
                                       f"{self.activity.activity_path}")
                                _logger.error(msg)
                                raise ActionException(msg)

                            # Method and instance target valid
                            inst_flow_t = inst_flow_r.body[0]
                            method_t = method_r.body[0]
                            from xuml_populate.populate.actions.method_call import MethodCall
                            mcall = MethodCall(method_name=op_name, method_anum=method_t["Anum"], caller_flow=
                                               Flow_ap( fid=inst_flow_t["ID"], content=Content.INSTANCE,
                                                        tname=inst_class_name, max_mult=MaxMult.ONE),
                                               parse=comp,
                                               activity=self.activity)
                            ain, aout, self.component_flow = mcall.process()
                            if first_action:
                                self.initial_action = ain
                            self.final_action = aout
                        else:
                            # This must be a scalar input, and therefore a type operation, so we
                            # populate a type operation with supplied params
                            scalar_input_flows = Flow.find_labeled_scalar_flow(
                                name=target_flow_label, anum=self.activity.anum, domain=self.activity.domain)
                            if not scalar_input_flows:
                                msg = f"No flow found for label {target_flow_label} at {self.activity.activity_path}"
                                _logger.error(msg)
                                raise ActionException(msg)
                            if len(scalar_input_flows) != 1:
                                msg = (f"Duplicate flows found for label {target_flow_label} "
                                       f"at {self.activity.activity_path}")
                                _logger.error(msg)
                                raise ActionException(msg)

                            ta = TypeAction(op_name=op_name, anum=self.activity.anum, domain=self.activity.domain,
                                            input_flow=scalar_input_flows[0],
                                            params=comp.supplied_params)
                            self.initial_action, self.final_action, self.component_flow = ta.populate()
                            pass

                case 'New_inst_a':
                    # A New instance
                    pass
                case _:
                    raise Exception
        return self.initial_action, self.final_action, self.component_flow
