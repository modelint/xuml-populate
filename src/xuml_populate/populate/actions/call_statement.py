"""
call_statement.py – Process a Scrall call statement
"""
# System
import logging
from typing import TYPE_CHECKING, Optional
from collections import namedtuple

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

        self.positions: list[dict] = []  # List of actions to populate

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

    def add_write_action(self, class_name: str, attr_name: str):
        """
        Add an attribute write action to the list of positions. Raises exception if the attribute is not defined.

        Args:
            class_name: A class name
            attr_name: An attribute of this class
        """
        if Attribute.defined(name=attr_name, class_name=class_name, domain=self.domain):
            self.positions = [{'write action': {'class': class_name, 'attr': attr_name}}]
            # Note that we are initializng the positiosn decitionary and not appending a position
            return

        # No such attribute found in the mmdb
        msg = f"Attribute {class_name}.{attr_name} not defined in: {self.activity.activity_path}"
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
        flow_content = None  # Flow content at most recent position
        unresolved_iflow = None

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
                        # First position is an unqualified attribute and we are starting off with a write action
                        self.add_write_action(class_name=class_name, attr_name=call_source.name)
                        flow_content = 'scalar'
                    else:
                        # Must be an iflow, it is unresolved until we check the next position
                        unresolved_iflow = self.find_iflow(name=call_source.name)
                        if not unresolved_iflow:
                            msg = (f"Could not match name at beginning of a call statement to either a local attribute"
                                   f"or a single instance flow in: {self.activity.activity_path}")
                            _logger.error(msg)
                            raise ActionException(msg)  # Last possibility for first position
                        flow_content = 'instance' if unresolved_iflow.max_mult == MaxMult.ONE else 'other'


            case 'INST_a':
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
        for c in op_chain.components:
            match type(c).__name__:
                case 'N_a' | 'IN_a':
                    match flow_content:
                        case 'scalar':
                            # Populate a type operation with no params
                            self.add_type_action(name=c.name, params=[])
                        case 'instance':
                            # Could be a method/ext service or attribute
                            pass
                        case 'other':
                            raise UnexpectedParsePattern
                        case _:
                            raise UnexpectedParsePattern
                case 'Scalar_op_a':
                    if type(c.name).__name__ not in {'N_a', 'IN_a'}:
                        raise UnexpectedParsePattern
                    self.add_type_action(name=c.name.name, params=c.supplied_params)
                case _:
                    raise UnexpectedParsePattern

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