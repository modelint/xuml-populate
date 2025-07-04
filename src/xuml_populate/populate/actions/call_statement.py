"""
call_statement.py – Process a call statement
"""
# System
import logging

# Model Integration
from scrall.parse.visitor import Call_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import CallFromUndefinedName
from xuml_populate.populate.actions.aparse_types import Activity_ap, Boundary_Actions

class CallStatement:
    """
    Populate all components of a call statement

    This can be a method call, an ee operation, or the invocation of a type operation.

    The first component is either an Instance Set (INST_a) or just a name (N_a)

    If it is just a name, that name must be the name of a

    """

    def __init__(self, call_parse: Call_a, activity_data: Activity_ap):

        self.parse = call_parse
        self.activity_data = activity_data

        call_source = type(call_parse.call).__name__

        if call_source == 'N_a':
            name = call_parse.call.name

            # Is the caller a Class?
            R = f"Name:<{name}>, Domain:<{activity_data.domain}>"
            class_r = Relation.restrict(db=mmdb, relation="Class", restriction=R)
            if class_r.body:
                pass  # TODO: Call method

            # Is the caller an External Entity?
            R = f"Name:<{name}>, Domain:<{activity_data.domain}>"
            ee_r = Relation.restrict(db=mmdb, relation="External Entity", restriction=R)
            if ee_r.body:
                pass  # TODO: Call Synchronous Operation

            # It must be a type operation on either an Attribute or a Scalar Flow
            # First assumption is an Attribute
            R = f"Name:<{name}>, Class:<{activity_data.state_model}>, Domain:<{activity_data.domain}>"
            attr_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
            if attr_r.body:
                # The caller is an attribute
                # So we could only be calling an operation on a Type
                # Type operations are outside of our metamodel domain, so we will just
                # We can look up the operator in the types db and verify that it exists
                pass  # TODO: It's an attribute
            else:
                # It must be a labeled flow
                R = f"Name:<{name}>, Activity:<{self.activity_data.anum}>, Domain:<{activity_data.domain}>"
                labeled_flow_r = Relation.restrict(db=mmdb, relation="Labeled_Flow", restriction=R)
                if not labeled_flow_r.body:
                    msg = f"Name: {name} in State: {activity_data.activity_path} undefined"
                    logging.error(msg)
                    raise CallFromUndefinedName(msg)


        pass

        # If the
