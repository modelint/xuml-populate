"""
method_extender.py – Populate a Method Extender action
"""

# System
import logging
from typing import TYPE_CHECKING, Optional

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from scrall.parse.visitor import Op_a


# xUML populate
if TYPE_CHECKING:
    from xuml_populate.populate.activity import Activity
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Boundary_Actions
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.actions.iterator import IteratorAction
from xuml_populate.populate.mmclass_nt import Method_Extender_i, Extender_i

if __debug__:
    from xuml_populate.utility import print_mmdb

_logger = logging.getLogger(__name__)

tr_Method_Extender = "Method Extender"

class MethodExtender:
    """
    Populate a Method Extender Action
    """

    def __init__(self, op_parse: Op_a, input_iflow: Flow_ap, activity: 'Activity'):
        """
        Collect all data required to populate a Computation Action

        Args:
            op_parse: Parsed op which must be an unqualified method invocation
            input_iflow: Must be an input instance flow, typically many
            activity: The enclosing Activity
        """
        self.op_parse = op_parse
        # Input iflow must be an instance flow
        if input_iflow.content != Content.INSTANCE:
            msg = (f"Method Extender action requires an instance input flow and got {input_iflow} instead at "
                   f"{activity.activity_path}")
            _logger.error(msg)
            raise ActionException(msg)
        self.input_flow = input_iflow

        self.anum = activity.anum
        self.domain = activity.domain
        self.activity = activity

    def populate(self) -> tuple[str, str, Flow_ap, str]:
        """
        Populate a Method Extender action

        Returns:
            The ain and aout action ids
            The output table flow
            The name of the extended attribute (based on the called method name)
        """
        # Validate the op_parse
        # Owner must be implicit (local / unqualified)
        owner = self.op_parse.owner
        if owner != '_implicit':
            msg = (f"Method extender requries a local (unqualified) method but got class {owner} at"
                   f" {self.activity.activity_path}")
            _logger.error(msg)
            raise ActionException(msg)

        Transaction.open(db=mmdb, name=tr_Method_Extender)
        iterator_id, iterated_flow = IteratorAction.populate(
            tr=tr_Method_Extender, input_mult_inst_flow=self.input_flow, activity=self.activity
        )
        # Validate method and obtain its anum
        method_name = self.op_parse.op_name
        class_name = self.input_flow.tname
        R = f"Name:<{method_name}>, Class:<{class_name}>, Domain:<{self.domain}>"
        method_r = Relation.restrict(db=mmdb, relation="Method", restriction=R)
        if not method_r.body:
            msg = f"Method {self.domain}:{class_name}.{method_name} for Method Extender's Method Call not found"
            _logger.error(msg)
            raise FlowException(msg)
        method_anum = method_r.body[0]['Anum']

        # Populate the method call
        from xuml_populate.populate.actions.method_call import MethodCall
        mcall = MethodCall(method_name=method_name, method_anum=method_anum, caller_flow=iterated_flow,
                           parse=self.op_parse, activity=self.activity)
        ain, method_call_id, sflow = mcall.process()
        # The Method Call might sprout additional actions such as a Read Action, but the final output emanates
        # from the method call itself, so aout must be the Method Call action's ID
        # And the output flow must be a Scalar Flow, so we verify that now
        if sflow.content != Content.SCALAR:
            msg = (f"Method called by Method Extender does not have an output Scalar flow. Got {sflow} instead at"
                   f" {self.activity.activity_path}")
            _logger.error(msg)
            raise ActionException(msg)

        # Populate the Method Extender
        Relvar.insert(db=mmdb, tr=tr_Method_Extender, relvar='Method Extender', tuples=[
            Method_Extender_i(ID=iterator_id, Activity=self.anum, Domain=self.domain, Method_call=method_call_id)
        ])
        # Set name and type of extended attribute: method name and type of method call scalar flow output
        extend_attr_name = f'_{method_name}'
        extend_attr_type = sflow.tname

        # Get the header of the class as a dictionary of (attr/type pairs)
        table_attrs = MMclass.header(cname=class_name, domain=self.domain)
        # Add the extend attr to the dictionary to define the extended header of the table output flow
        table_attrs[extend_attr_name] = extend_attr_type
        output_tflow = Flow.populate_relation_flow_by_header(table_header=table_attrs, anum=self.anum,
                                                             domain=self.domain, max_mult=MaxMult.MANY)
        pass
        # Now we can finish population of the Method Extender action
        Relvar.insert(db=mmdb, tr=tr_Method_Extender, relvar='Extender', tuples=[
            Extender_i(ID=iterator_id, Activity=self.anum, Domain=self.domain, Attribute_flow=sflow.fid,
                       Table_output=output_tflow.fid)
        ])

        Transaction.execute(db=mmdb, name=tr_Method_Extender)

        return ain, method_call_id, output_tflow, extend_attr_name



