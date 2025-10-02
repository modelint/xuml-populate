"""
call_statement.py – Process a Scrall call statement
"""
# System
import logging
from typing import TYPE_CHECKING, Optional

# Model Integration
from scrall.parse.visitor import Call_a, Supplied_Parameter_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow, Flow_ap
from xuml_populate.populate.attribute import Attribute
from xuml_populate.populate.actions.method_call import MethodCall
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.populate.actions.type_action import TypeAction
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import Boundary_Actions, Content, MaxMult

_logger = logging.getLogger(__name__)


class CallStatement:
    """
    A Call Statement represents the standalone invocation of a callable model element.
    Currently, these model elements are Method, External Service, and Type Action.
    By 'standalone' we mean that the invocation is not happening within the context of an assignment.

    For example:

        Close attempts.reset  // 1. Standalone Type Action invocation vs.
        dest .= my cabin.Ping( dir: 2. current travel direction ) // Method invoccation in assignment

    Only the statement 1. in the example above will result in a Call Statement.
    """

    def __init__(self, call_parse: Call_a, activity: 'Activity'):
        """

        Args:
            call_parse:
            activity:
        """
        self.parse = call_parse
        self.activity = activity
        self.anum = activity.anum
        self.domain = activity.domain

        # These two are set if a type action is writing its output back into an attribute
        # Close attempts.reset, for example, where the reset type action writes 0 to the Door.Close attempts attr
        self.write_to_iflow: Optional[Flow_ap] = None
        self.write_to_attr: Optional[str] = None

    def add_call_op(self, caller_name: str, op_name: str, params: list[Supplied_Parameter_a]) -> bool:
        """
        Appends a method_call or external service action position.

        Args:
            caller_name: Name of the calling instance flow
            op_name: Name of the method or external service
            params: Supplied parameters

        Returns:
            False if no Method or External Service matches the name

        """
        # Lookup the caller flow
        # Is there a matching method?
        R = f"Name:<{op_name}>, Class<{caller_name}>, Domain:<{self.domain}>"
        method_r = Relation.restrict(db=mmdb, relation="Method", restriction=R)
        if method_r.body:
            pass
            # self.positions.append({'method call': {'caller': }})

    def op_defined(self, class_name: str, op_name: str) -> Optional[tuple[str, str]]:
        """

        Args:
            class_name:
            op_name:

        Returns:
            The op type and type of returned value (si_flow, scalar, other)
        """
        R = f"Name:<{op_name}>, Class:<{class_name}>, Domain:<{self.domain}>"
        method_r = Relation.restrict(db=mmdb, relation="Method", restriction=R)
        if method_r.body:
            # TODO: look up the return value
            return 'method', ''  # put return value of method here also
        R = f"Name:<{op_name}>, Class:<{class_name}>, Domain:<{self.domain}>"
        external_service_r = Relation.restrict(db=mmdb, relation="External Service", restriction=R)
        if external_service_r.body:
            # TODO: look up the return value
            return 'external service', ''  # put return value of service here also
        return None


    def add_type_action(self, name:str, params:list[Supplied_Parameter_a]):
        """
        Add type action to the dictionary. We don't do any type operation or param validation
        here since this occurs when we try to populate the type action.

        Args:
            name:  Type name
            params:  Supplied params
        """
        self.positions.append({'type action': {'name': name, 'params': params}})

    def prep_write_action(self, iflow: Flow_ap, attr_name: str):
        """
        Prepare a write action so that it can be created later (when the input flow is determined)

        Raises exception if the attribute is not defined.

        Args:
            iflow: A single instance flow name
            attr_name: An attribute of this class
        """
        if Attribute.defined(name=attr_name, class_name=iflow.tname, domain=self.domain):
            self.write_to_iflow = iflow
            self.write_to_attr = attr_name
            return

        # No such attribute found in the mmdb
        msg = f"Attribute {iflow.tname}.{attr_name} not defined in: {self.activity.activity_path}"
        _logger.error(msg)
        raise ActionException(msg)

    def find_iflow(self, name: str) -> Optional[Flow_ap]:
        """
        If the name matches the label of an instance flow, that flow summary is returned.

        Args:
            name: Flow name

        Returns:
            Flow_ap (flow summary) if found, otherwise None
        """
        ns_flows = Flow.find_labeled_ns_flow(name=name, anum=self.anum, domain=self.domain)
        if len(ns_flows) > 1:
            msg = f"Duplicate flow labels encountered processing Call Statement in: {self.activity.activity_path}"
            _logger.error(msg)
            raise ActionException
        if ns_flows:
            # There is one matching non scalar flow in this activity matching the name
            # But we need a single instance flow (not a table or many instance flow)
            if ns_flows[0].content == Content.INSTANCE:
                return ns_flows[0]

        return None

    def find_si_flow(self, name: str) -> Optional[Flow_ap]:
        """
        If the name matches the label of a single instance flow, that flow summary is returned.

        Args:
            name: Flow name

        Returns:
            Flow_ap (flow summary) if found, otherwise None
        """
        ns_flows = Flow.find_labeled_ns_flow(name=name, anum=self.anum, domain=self.domain)
        if len(ns_flows) > 1:
            msg = f"Duplicate flow labels encountered processing Call Statement in: {self.activity.activity_path}"
            _logger.error(msg)
            raise ActionException
        if ns_flows:
            # There is one matching non scalar flow in this activity matching the name
            # But we need a single instance flow (not a table or many instance flow)
            if ns_flows[0].content == Content.INSTANCE and ns_flows[0].max_mult == MaxMult.ONE:
                return ns_flows[0]

        return None


    def resolve_actions(self):
        call_source = self.parse.call
        op_chain = self.parse.op_chain
        unresolved_iflow: Optional[Flow_ap] = None
        active_sflow: Optional[Flow_ap] = None
        ie_output_flow: Optional[Flow_ap] = None

        # Process call_source
        match type(call_source).__name__:
            # These are the only anticipated parse output patterns

            case 'N_a' | 'IN_a':  # (call=<N_a | IN_a>, op_chain=<Op_chain_a>) pattern
                # Here we are getting an instance set that has no components, it's just a name
                # We know that we are writing an attribute value.

                # The attribute is either a self-attribute or it is qualified by an instance flow
                # The name must match an attribute of the executing instance to be a self-attribute
                # Otherwise, the instance flow must be a single instance flow and the first comonent
                # in the op_chain must be a name (not a scalar op) that matches an attribute of
                # that instance flow's class.

                # We cannot be calling a method since a method must use parentheses even if it
                # doesn't require any parameters. And that will cause it to be scanned as an operation
                # which means it will be delivered as a component of an INST_a.

                class_name = self.activity.xiflow.tname
                if class_name:
                    # We have an executing instance (lifecycle, method activity) so it is possible
                    # to specify an unqualified (self) attribute to write.
                    # See if the attribute is defined on the xi class
                    if Attribute.defined(name=call_source.name, class_name=class_name, domain=self.domain):
                        # Read the attribute
                        ra = ReadAction(input_single_instance_flow=self.activity.xiflow, attrs=(call_source.name,),
                                        anum=self.anum, domain=self.domain)
                        _, sflows = ra.populate()
                        if not sflows:
                            raise ActionException
                        # Set the read action output as the current sflow
                        active_sflow = sflows[0]
                        # First name is an unqualified attribute and we are starting off with a write action
                        self.prep_write_action(iflow=self.activity.xiflow, attr_name=call_source.name)
                    else:
                        # Must be an iflow, it is unresolved until we check the next position
                        unresolved_iflow = self.find_iflow(name=call_source.name)
                        if not unresolved_iflow:
                            msg = (f"Could not match name at beginning of a call statement to either a local attribute"
                                   f"or a single instance flow in: {self.activity.activity_path}")
                            _logger.error(msg)
                            raise ActionException(msg)  # Last possibility for first position

            case 'INST_a':
                ie = InstanceSet(iset_components=call_source.components, activity=self.activity,
                                 input_instance_flow=self.activity.xiflow)
                ain, aout, ie_output_flow = ie.process(write_to_attr=True)
                active_sflow = None if ie_output_flow.content != Content.SCALAR else ie_output_flow
                # If we get an f back, we know this was not an attr write
                # We still might get an empty flow if it was a method or ext service that did not specify an output
                # But we cannot tack on any op_chain components if the output is not scalar
                # so we need to clear the active_sflow unless we obtain a scalar output from the instance expression
                # in which case, that becomes the active_sflow

                for c in call_source.components:
                    match type(c).__name__:
                        case 'Op_a':
                            # We have an owner and op_name and a list of one or more params
                            # The owner can be named or '_implicit' in which case it takes input from the prior
                            # action
                            #
                            # Let's assume we are at the first position (empty dict)
                            # There are only two possibilities:
                            #
                            # The owner could be an unqualified attribute (write action) followed by
                            # a type action with params.  That's our first assumption.
                            if not self.positions:  # empty dictionary indicates first position
                                if self.activity.xiflow and Attribute.defined(
                                        name=c.owner, class_name=self.activity.xiflow.tname,
                                        domain=self.domain):
                                    self.add_write_action(class_name=self.activity.xiflow.tname,
                                                          attr_name=c.owner)
                                    self.add_type_action(name=c.op_name, params=c.supplied_params)
                                    flow_content = 'scalar'
                                else:
                                    # Otherwise, at the first position, the owner is an si_flow
                                    # followed by a method or ext service with params
                                    self.add_call_op(caller_name=c.owner, op_name=c.op_name,
                                                     params=c.supplied_params)
                            else:
                                # If this is NOT the first position, this must be a type action with
                                # params
                                self.add_type_action(name=c.op_name, params=c.supplied_params)
                                flow_content = 'scalar'
                        case 'N_a' | 'IN_a':
                            pass
                        case 'Criteria_Selection_a':
                            pass
                        case _:
                            raise ActionException
            case _:
                raise UnexpectedParsePattern

        # Handle any remaining op_chain components
        # These will all be type actions without any params
        first_comp = True
        for c in op_chain.components:
            match type(c).__name__:
                case 'N_a' | 'IN_a':
                    if active_sflow:
                        # Populate a type operation with no params
                        ta = TypeAction(op_name=c.name, anum=self.anum, domain=self.domain, input_flow=self.sflow)
                        _, _, active_sflow = ta.populate()
                    elif unresolved_iflow:
                        # Read the attribute
                        ra = ReadAction(input_single_instance_flow=unresolved_iflow, attrs=(c.name.name,),
                                        anum=self.anum, domain=self.domain)
                        _, sflows = ra.populate()
                        if not sflows:
                            raise ActionException
                        # Set the read action output as the current sflow
                        active_sflow = sflows[0]
                        # First two names define a qualified attribute and we are starting off with a write action
                        # so we can now resolve the saved iflow
                        self.prep_write_action(iflow=unresolved_iflow, attr_name=c.name.name)
                    else:
                        msg = (f"Cannot perform type operation on non-scalar input for call statement {self.parse} "
                               f"in: {self.activity.activity_path}")
                        _logger.error(msg)
                        raise ActionException(msg)
                case 'Scalar_op_a':
                    if first_comp:
                        # If the first name specifies parameters in the call statement, this will have been scanned
                        # in an INST_a and shouldn't happen here. So the first component is never a Scalar_op_a
                        raise UnexpectedParsePattern
                    if type(c.name).__name__ in {'N_a', 'IN_a'}:
                        # Populate a type operation with supplied params
                        ta = TypeAction(op_name=c.name.name, anum=self.anum, domain=self.domain, input_flow=self.sflow,
                                        params=c.supplied_params)
                        _, _, active_sflow = ta.populate()
                    else:
                        raise UnexpectedParsePattern
                case _:
                    raise UnexpectedParsePattern
            first_comp = False

    def process(self) -> Boundary_Actions:
        """

        Returns:

        """
        # We are calling an operation on an instance set, in which case we are calling a method
        # OR we are calling an operation on a scalar flow
        self.resolve_actions()
        pass
        # TODO: Populate the positions moving right to left (ignoring any write attr)
        # TODO: Populate the write attribute action, if any


        # TODO: NOTE: consider case where there is a chain of methods returning single instance flows