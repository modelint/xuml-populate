"""
call_statement.py – Process a Scrall call statement
"""
# System
import logging
from typing import TYPE_CHECKING

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
from xuml_populate.populate.actions.method_call import MethodCall
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import Boundary_Actions, Content, MaxMult

_logger = logging.getLogger(__name__)

class CallStatement:
    """
    Populate all components of a call statement

    This can be a method call, an ee operation, or the invocation of a type operation.

    The first component is either an Instance Set (INST_a) or just a name (N_a)

    If it is just a name, that name must be the name of a

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
        # match type(call_parse.call).__name__:
        #     case 'N_a' | 'IN_a':
        #         self.op_parse = call_parse.call.name
        #         self.caller_parse = None
        #     case _:
        #         self.op_parse = call_parse.call.components[-1]
        #         self.caller_parse = call_parse.call.components[:-1]

    def process(self) -> Boundary_Actions:
        """

        Returns:

        """
        # We are calling an operation on an instance set, in which case we are calling a method
        # OR we are calling an operation on a scalar flow

        call_source = type(self.parse.call).__name__

        match call_source:
            case 'INST_a':
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
                        pass  # TODO: It's an attribute, the input flow will be emitted by the Read Action

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

