"""
call_statement.py – Process a Scrall call statement
"""
# System
import logging

# Model Integration
from scrall.parse.visitor import Call_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.utility import print_mmdb
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.method_call import MethodCall
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions, Content, MaxMult

_logger = logging.getLogger(__name__)

class CallStatement:
    """
    Populate all components of a call statement

    This can be a method call, an ee operation, or the invocation of a type operation.

    The first component is either an Instance Set (INST_a) or just a name (N_a)

    If it is just a name, that name must be the name of a

    """

    def __init__(self, call_parse: Call_a, activity_data: ActivityAP):
        """

        Args:
            call_parse:
            activity_data:
        """
        self.parse = call_parse
        self.activity_data = activity_data
        match type(call_parse.call).__name__:
            case 'N_a' | 'IN_a':
                self.op_parse = call_parse.call.name
                self.caller_parse = None
            case _:
                self.op_parse = call_parse.call.components[-1]
                self.caller_parse = call_parse.call.components[:-1]
        self.op_chain = call_parse.op_chain

    def process(self) -> Boundary_Actions:
        """

        Returns:

        """

        call_source = type(self.parse.call).__name__

        match call_source:
            case 'INST_a':
                # At this point we don't know whether we are calling a method, type op, or EE op
                # We'll need to know the type of the caller and that means we need to process the instance set
                iset = InstanceSet(input_instance_flow=self.activity_data.xiflow,
                                   iset_components=self.caller_parse, activity_data=self.activity_data)
                ain, aout, caller_flow = iset.process()

                # Are we calling Class's Method?
                # Two conditions must be met to qualify as a class method
                #   1. We at least one named method that matches the op name
                #   2. The associated class is also the type of the caller

                # If the caller flow tname matches the name of a class that also defines the op_name
                # we know that we have an target instance of the method's defining class
                R = f"Name:<{self.op_parse.op_name}>, Class:<{caller_flow.tname}>, Domain:<{self.activity_data.domain}>"
                method_r = Relation.restrict(db=mmdb, relation='Method', restriction=R)
                if len(method_r.body) == 1:
                    # We found a single matching method so we need to populate a Method Call
                    # Just to be sure, let's ensure that the caller_flow is a single instance flow
                    if caller_flow.content != Content.INSTANCE or caller_flow.max_mult != MaxMult.ONE:
                        msg = (f"Method caller type [{caller_flow.tname}] is not a single instance flow for "
                               f"op_name: {self.op_parse.op_name}")
                        _logger.error(msg)
                        raise ActionException(msg)
                    method_t = method_r.body[0]
                    mcall = MethodCall(method_name=method_t["Name"], method_anum=method_t["Anum"],
                                       caller_flow=caller_flow, parse=self.parse, activity_data=self.activity_data)
                    boundary_actions = mcall.process()
                    return boundary_actions
                else:
                    pass
                    # TODO: Locate ee op or type call and populate that

            case 'N_a':
                # TODO: Not sure what Scrall will result in this case
                pass

        #         name = call_parse.call.name
        #
        #         # Is the caller a Class?
        #         R = f"Name:<{name}>, Domain:<{activity_data.domain}>"
        #         class_r = Relation.restrict(db=mmdb, relation="Class", restriction=R)
        #         if class_r.body:
        #             pass  # TODO: Call method
        #
        #         # Is the caller an External Entity?
        #         R = f"Name:<{name}>, Domain:<{activity_data.domain}>"
        #         ee_r = Relation.restrict(db=mmdb, relation="External Entity", restriction=R)
        #         if ee_r.body:
        #             pass  # TODO: Call Synchronous Operation
        #
        #         # It must be a type operation on either an Attribute or a Scalar Flow
        #         # First assumption is an Attribute
        #         R = f"Name:<{name}>, Class:<{activity_data.state_model}>, Domain:<{activity_data.domain}>"
        #         attr_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
        #         if attr_r.body:
        #             # The caller is an attribute
        #             # So we could only be calling an operation on a Type
        #             # Type operations are outside of our metamodel domain, so we will just
        #             # We can look up the operator in the types db and verify that it exists
        #             pass  # TODO: It's an attribute
        #         else:
        #             # It must be a labeled flow
        #             R = f"Name:<{name}>, Activity:<{self.activity_data.anum}>, Domain:<{activity_data.domain}>"
        #             labeled_flow_r = Relation.restrict(db=mmdb, relation="Labeled_Flow", restriction=R)
        #             if not labeled_flow_r.body:
        #                 msg = f"Name: {name} in State: {activity_data.activity_path} undefined"
        #                 logging.error(msg)
        #                 raise CallFromUndefinedName(msg)
        #
        #
        # pass

