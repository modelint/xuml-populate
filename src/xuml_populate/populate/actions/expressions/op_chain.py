"""
op_chain.py – Process an op_chain expression
"""
# System
import logging
from typing import TYPE_CHECKING, Optional

# Model Integration
from scrall.parse.visitor import Supplied_Parameter_a, Op_chain_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

from xuml_populate.populate.actions.write_action import WriteAction

# xUML Populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow, Flow_ap
from xuml_populate.populate.attribute import Attribute
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.populate.actions.type_action import TypeAction
from xuml_populate.populate.actions.expressions.instance_set import InstanceSet
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import Boundary_Actions, Content, MaxMult

_logger = logging.getLogger(__name__)

if __debug__:
    from xuml_populate.utility import print_mmdb

class OpChain:
    """
    An OpChain processed one or more operation invocations in a chain
    """

    def __init__(self, iflow: Optional[Flow_ap], sflow: Optional[Flow_ap], parse: Op_chain_a, activity: 'Activity'):
        """

        Args:
            parse: A Scrall Op_chain_a parse
            activity: The enclosing ativity
        """
        self.parse = parse
        self.activity = activity
        self.anum = activity.anum
        self.domain = activity.domain

        self.iflow = iflow
        self.sflow = sflow

        # Boundary actions
        self.ain: Optional[str] = None
        self.aout: Optional[str] = None

    def process(self) -> tuple[Boundary_Actions, Flow_ap]:
        """
        """
        # These will all be type actions without any params
        first_comp = True
        for c in self.parse.components:
            component_type = type(c).__name__
            match component_type:
                case 'N_a' | 'IN_a':
                    if self.sflow:
                        # Populate a type operation with no params
                        ta = TypeAction(op_name=c.name, anum=self.anum, domain=self.domain, input_flow=self.sflow)
                        tin, self.aout, self.sflow = ta.populate()
                        self.ain = tin if not self.ain else self.ain  # Update the input only if it has not been set
                    elif self.iflow:
                        # Read the attribute
                        # TODO: Check for any cases where it should be c.name.name
                        ra = ReadAction(input_single_instance_flow=self.iflow, attrs=(c.name,),
                                        anum=self.anum, domain=self.domain)
                        rin, sflows = ra.populate()  # Any attribute read must be the input action
                        self.ain = rin if not self.ain else self.ain  # Update the input only if it has not been set
                        if not sflows:
                            raise ActionException
                        # Set the read action output as the current sflow
                        self.sflow = sflows[0]
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
                        tin, self.aout, self.sflow = ta.populate()
                        self.ain = tin if not self.ain else self.ain  # Update the input only if it has not been set
                    else:
                        raise UnexpectedParsePattern
                case _:
                    raise UnexpectedParsePattern
            first_comp = False

        # Since we are either parsing a full instance expression or
        # just a simple name (which is just the simple case of an instance expression,
        # we know that there is only one input action and one output action in the call statement data flow
        return Boundary_Actions(ain={self.ain}, aout={self.aout}), self.sflow
