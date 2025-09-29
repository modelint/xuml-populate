"""
call_statement.py – Process a Scrall call statement
"""
# System
import logging
from typing import TYPE_CHECKING
from collections import namedtuple

# Model Integration
from scrall.parse.visitor import Call_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
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
        self.calling_iflow = None
        self.calling_sflow = None
        self.calling_attribute = None
        self.calling_method_name = None
        self.calling_external_service_name = None
        self.positions: list[dict] = []  # List of actions to populate

    def add_write_action(self, name: str) -> bool:
        if self.activity.xiflow and Attribute.defined(
                name=name, class_name=self.activity.xiflow.tname, domain=self.domain):
            self.positions.append({'write': {'attr': name}})
            return True
        return False

    def add_si_flow(self, name: str) -> bool:
        ns_flows = Flow.find_labeled_ns_flow(name=name, anum=self.anum, domain=self.domain)
        if len(ns_flows) > 1:
            msg = f"Duplicate flow labels encountered processing Call Statement in: {self.activity.activity_path}"
            _logger.error(msg)
            raise ActionException
        if ns_flows:
            # There is one matching non scalar flow in this activity matching the name
            # But we need a single instance flow (not a table or many instance flow)
            if ns_flows[0].content == Content.INSTANCE and ns_flows[0].max_mult == MaxMult.ONE:
                self.positions.append({'si_flow': ns_flows[0]})
                return True
        return False


    def walk(self):
        call_source = self.parse.call
        op_chain = self.parse.op_chain

        # Process call_source
        match call_source:
            # These are the only anticipated parse output patterns

            case 'N_a' | 'IN_a':  # (call=<N_a | IN_a>, op_chain=<Op_chain_a>) pattern
                # We have a name without any parameters in the first position
                # It is either an attribute name or a single instance iflow label

                if not self.add_write_action(name=call_source.name):  # Write to this attribute
                    if not self.add_si_flow(name=):  # Single instance flow
                        raise ActionException

            case 'INST_a':
                pass

        pass

    def resolve_caller(self):
        """
        The caller what we might call the 'owner'.
        If the owner is a single instance flow, we are either:
            a) calling a Method or an External Service.
            b) prefacing an Attribute:  some door.Close attempts

        The owner can never be a multiple instance flow.

        Otherwise, the owner is a scalar flow which means we are calling a type operation

        The owner cannot be a type since this is a standalone invocation (no assignment)
        """
        # Collect information about the first two positions (x.y)
        # We want to know the names of x and y and whether or not y specifies any parameters
        call_source = type(self.parse.call).__name__
        position1 = None
        position2 = None
        params = False

        match call_source:
            # These are the only anticipated parse output patterns

            case 'N_a' | 'IN_a':  # (call=<N_a | IN_a>, op_chain=<Op_chain_a>) pattern
                # Example: x.y
                # This parse pattern starts with an N_a instance set (just a name)
                # followed by an op_chain with one or more name components
                position1 = self.parse.call.name  # So position1 is the name
                comp2 = self.parse.op_chain.components[0]
                if type(comp2).__name__ not in {'N_a', 'IN_a'}:
                    msg = f"Parse pattern error: {self.activity.activity_path}"
                    raise UnexpectedParsePattern(msg)
                position2 = comp2.name  # position2 is the first op_chain component which must be a name
                params = False  # No params with this parse pattern

            case 'INST_a':
                # Examples: x(a:b), x.y(a:b), x(a:b).y(c:d)
                # This pattern occurs only if positions 1, 2 or both supply params
                params = True
                comp1 = self.parse.call.components[0]
                match type(comp1).__name__:
                    case 'Op_a':  # x.y(a:b)
                        # There are two positions specified by the first component
                        # with position2 supplying params
                        position1 = comp1.owner
                        position2 = comp1.op_name
                        params = bool(comp1.supplied_params)  # False if no params
                    case 'N_a' | 'IN_a':  # x(a:b), x(a:b).y(c:d)
                        # There is only one position and it supplies params
                        position1 = comp1.name
                        if len(self.parse.call.components) < 2:
                            msg = f"Parse pattern error: {self.activity.activity_path}"
                            raise UnexpectedParsePattern(msg)
                        comp2 = self.parse.call.components[1]
                        if type(comp2).__name__ == 'Criteria_Selection_a':
                            if len(self.parse.call.components) > 2:
                                comp3 = self.parse.call.components[2]
                                if type(comp3).__name__ != 'Op_a':
                                    msg = f"Parse pattern error: {self.activity.activity_path}"
                                    raise UnexpectedParsePattern(msg)
                                # Both positions supply params
                                position2 = comp3.op_name
                            else:
                                # Only one position and it supplies params
                                position2 = None
                            params = True
                        else:
                            msg = f"Parse pattern error: {self.activity.activity_path}"
                            raise UnexpectedParsePattern(msg)
            case _:
                msg = f"Unknown call source in Call Statement at {self.activity.activity_path}"
                _logger.error(msg)
                raise ActionException(msg)

        # Is the first position an attribute?
        if self.activity.xiflow and not params:
            # Must be an attribute of the executing instance with a dot and no signature on the right
            if Attribute.defined(name=position1, class_name=self.activity.xiflow.tname, domain=self.domain):
                self.calling_attribute = position1
                return # It's an attribute name in position one

            # Do we have a qualified attribute (attribute in second position, instance flow in first, no params)
            iflow = None
            ns_flows = Flow.find_labeled_ns_flow(name=position1, anum=self.anum, domain=self.domain)
            if len(ns_flows) > 1:
                msg = f"Duplicate flow labels encountered processing Call Statement in: {self.activity.activity_path}"
                _logger.error(msg)
                raise ActionException
            if ns_flows:
                # There is one matching non scalar flow in this activity
                # This is a labeled non_scalar flow matching the position1 name
                if ns_flows[0].content == Content.INSTANCE and ns_flows[0].max_mult == MaxMult.ONE:
                    # It must be a single instance flow (not a table or many instance flow)
                    iflow = ns_flows[0]
                    if Attribute.defined(name=position2, class_name=iflow.tname, domain=self.domain):
                        self.calling_iflow = iflow
                        self.calling_attribute = position2
                        return  # It's an attribute name in position two qualifying a single instnace flow in position 1
                    # Maybe the second position is a method?
                    R = f"Name:<{position2}>, Class:<{iflow.tname}>, Domain:<{self.domain}>"
                    method_r = Relation.restrict(db=mmdb, relation="Method", restriction=R)
                    if method_r.body:
                        self.calling_iflow = iflow
                        self.calling_method_name = position2
                        return
                    R = f"Name:<{position2}>, Class:<{iflow.tname}>, Domain:<{self.domain}>"
                    external_service_r = Relation.restrict(db=mmdb, relation="External Service", restriction=R)
                    if external_service_r.body:
                        self.calling_iflow = iflow
                        self.calling_external_service_name = position2
                        return

        # TODO: Cannot be a scalar flow outside of an assignment statement
        # TODO: Either writing to an attribute or calling a method/ext service

        # TODO: Let's break this down with a decision tree (see tablet)
        # The first position is not an attribute or an instance flow
        # The only other possibility is a scalar flow
        sflows = Flow.find_labeled_scalar_flow(name=position1, anum=self.anum, domain=self.domain)
        if not sflows:
            msg = f"No caller found in call statement at: {self.activity.activity_path}"
            _logger.error(msg)
            raise ActionException(msg)
        if len(sflows) > 1:
            msg = f"Duplicate flow labels encountered processing Call Statement in: {self.activity.activity_path}"
            _logger.error(msg)
            raise ActionException
        self.calling_sflow = sflows[0]


    def process(self) -> Boundary_Actions:
        """

        Returns:

        """
        # We are calling an operation on an instance set, in which case we are calling a method
        # OR we are calling an operation on a scalar flow
        self.walk()
        pass

        # self.resolve_caller()

        call_source = type(self.parse.call).__name__

        match call_source:
            case 'INST_a':
                components = self.parse.call.components
                if len(components) > 1:
                    pass
                # We are likely invoking a method on some instance, so let's try that first
                op_parse = self.parse.call.components[-1]
                caller_parse = self.parse.call.components[:-1]
                # At this point we don't know whether we are calling a method, type op, or EE op
                # We'll need to know the type of the caller and that means we need to process the instance set
                iset = InstanceSet(input_instance_flow=self.activity.xiflow,
                                   iset_components=caller_parse, activity=self.activity)
                ain, aout, caller_flow = iset.process()

                # Are we calling Class's Method?
                # Two conditions must be met to qualify as a class method
                #   1. We at least one named method that matches the op name
                #   2. The associated class is also the type of the caller

                # If the caller flow tname matches the name of a class that also defines the op_name
                # we know that we have an target instance of the method's defining class
                R = f"Name:<{op_parse.op_name}>, Class:<{caller_flow.tname}>, Domain:<{self.domain}>"
                method_r = Relation.restrict(db=mmdb, relation='Method', restriction=R)
                if len(method_r.body) == 1:
                    # We found a single matching method so we need to populate a Method Call
                    # Just to be sure, let's ensure that the caller_flow is a single instance flow
                    if caller_flow.content != Content.INSTANCE or caller_flow.max_mult != MaxMult.ONE:
                        msg = (f"Method caller type [{caller_flow.tname}] is not a single instance flow for "
                               f"op_name: {op_parse.op_name}")
                        _logger.error(msg)
                        raise ActionException(msg)
                    method_t = method_r.body[0]
                    mcall = MethodCall(method_name=method_t["Name"], method_anum=method_t["Anum"],
                                       caller_flow=caller_flow, parse=self.parse, activity=self.activity)
                    ain, aout, flow = mcall.process()
                    return Boundary_Actions(ain=set(ain), aout=set(aout))
                else:
                    pass  # TODO: is there any other possibility?

            case 'N_a' | 'IN_a':
                # Not an instance set, so we are invoking a type operation on some scalar input flow
                # OR we are invoking an operation directly on a type

                scalar_input_flow = None  # We need to figure this out based on the call name

                # The call field of Call_a is a name that calls the operation
                # It must be:
                #   1. The name of a local attribute
                #   2. A Scalar Flow that is also a Labled Flow
                #   3. A Scalar (scalar data type name)
                # And we need to test these assumptions in precedence order

                # First assumption is an Attribute, which only works if we have an executing instance
                xiflow = getattr(self.activity, 'xiflow')
                if xiflow:
                    R = f"Name:<{self.parse.call.name}>, Class:<{xiflow.tname}>, Domain:<{self.domain}>"
                    attr_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
                    if attr_r.body:
                        # We'll need to populate a Read Action
                        ra = ReadAction(input_single_instance_flow=xiflow, attrs=(self.parse.call.name,),
                                        anum=self.anum, domain=self.domain)
                        aid, sflow = ra.populate()
                        for op in self.parse.op_chain:
                            pass
                        pass
                        # Now we need to resolve the opchain taking the read flow as input
                        # Now feed the output into a Type Action

                # Not an attribute, try Scalar Flow
                scalar_input_flow = Flow.find_labeled_scalar_flow(name=self.parse.call.name, anum=self.anum,
                                                                  domain=self.domain)

                if not scalar_input_flow:
                    # Must be a type name, verify that
                    R = f"Name:<{self.parse.call.name}>, Domain:<{self.domain}>"
                    type_r = Relation.restrict(db=mmdb, relation="Type", restriction=R)
                    if type_r.body:
                        pass
                        # TODO: If not already populated, populate the Type Operation


                pass

        #         name = call_parse.call.name
        #
        #         # Is the caller a Class?
        #         R = f"Name:<{name}>, Domain:<{activity.domain}>"
        #         class_r = Relation.restrict(db=mmdb, relation="Class", restriction=R)
        #         if class_r.body:
        #             pass  # TODO: Call method
        #
        #         # Is the caller an External Entity?
        #         R = f"Name:<{name}>, Domain:<{activity.domain}>"
        #         ee_r = Relation.restrict(db=mmdb, relation="External Entity", restriction=R)
        #         if ee_r.body:
        #             pass  # TODO: Call Synchronous Operation
        #
        #         # It must be a type operation on either an Attribute or a Scalar Flow
        #         # First assumption is an Attribute
        #         R = f"Name:<{name}>, Class:<{activity.state_model}>, Domain:<{activity.domain}>"
        #         attr_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
        #         if attr_r.body:
        #             # The caller is an attribute
        #             # So we could only be calling an operation on a Type
        #             # Type operations are outside of our metamodel domain, so we will just
        #             # We can look up the operator in the types db and verify that it exists
        #             pass  # TODO: It's an attribute
        #         else:
        #             # It must be a labeled flow
        #             R = f"Name:<{name}>, Activity:<{self.activity.anum}>, Domain:<{activity.domain}>"
        #             labeled_flow_r = Relation.restrict(db=mmdb, relation="Labeled_Flow", restriction=R)
        #             if not labeled_flow_r.body:
        #                 msg = f"Name: {name} in State: {activity.activity_path} undefined"
        #                 logging.error(msg)
        #                 raise CallFromUndefinedName(msg)
        #
        #
        # pass

