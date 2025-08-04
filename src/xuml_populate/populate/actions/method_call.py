"""
method_call.py – Process a call action
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
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.action import Action
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions, Flow_ap
from xuml_populate.populate.mmclass_nt import Method_Call_i, Method_Call_Parameter_i

_logger = logging.getLogger(__name__)

tr_Call = "Method Call"

class MethodCall:
    """
    Populate all components of a Method Call action and any other
    actions required by the parse
    """

    def __init__(self, method_name: str, method_anum: str, caller_flow: Flow_ap, parse: Call_a,
                 activity_data: ActivityAP):
        """
        Initialize the data we need to populate a method call

        Args:
            method_name:  The name of the method to be called
            method_anum:  The method's activity number
            caller_flow:  A single instance flow providing the target instance of the method call
            parse: A parsed call statement
            activity_data:  Information about the activity where this action executes
        """
        self.method_name = method_name
        self.method_anum = method_anum
        self.parse = parse
        # The Scrall grammar indicates that the last element in the components list must be an operation
        self.op_parse = self.parse.call.components[-1]
        self.activity_data = activity_data
        self.caller_flow = caller_flow
        self.action_id = None
        self.anum = self.activity_data.anum
        self.domain = self.activity_data.domain

    def process(self) -> Boundary_Actions:
        """
        Populate a Method Call action

        Returns:
            There's only one action here, so the initial and output actions will just be the id of the method call.
        """
        # Open transaction to populate the Method Call Action and all required Method Call Parameters
        Transaction.open(db=mmdb, name=tr_Call)
        # Populate the action superclass and obtain our action id
        self.action_id = Action.populate(tr=tr_Call, anum=self.anum, domain=self.domain, action_type="method call")
        # Insert the Method Call instance
        Relvar.insert(db=mmdb, tr=tr_Call, relvar='Method Call', tuples=[
            Method_Call_i(ID=self.action_id, Activity=self.anum, Domain=self.domain, Method=self.method_anum,
                          Instance_flow=self.caller_flow.fid)
        ])

        # Validate Method Call params (ensure that the call matches the Method's populated signature
        R = f"Anum:<{self.method_anum}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Method', restriction=R)
        Relation.semijoin(db=mmdb, rname2='Method Signature', attrs={'Name': 'Method', 'Domain': 'Domain'})
        param_r = Relation.semijoin(db=mmdb, rname2='Parameter', attrs={'SIGnum': 'Signature', 'Domain': 'Domain'})
        sig_params = {t["Name"]: t["Type"] for t in param_r.body}

        # Populate each Parameter specified in the Method's signature with an incoming Data Flow
        sp_pnames: set[str] = set()
        for sp in self.op_parse.supplied_params:
            pname = sp.pname
            sp_pnames.add(pname)
            sval = sp.sval.name

            # Populate parameter data flows
            R = f"Parameter:<{sval}>, Activity:<{self.anum}>, Signature:<{self.activity_data.signum}>, Domain:<{self.domain}>"
            activity_input_r = Relation.restrict(db=mmdb, relation='Activity Input', restriction=R)
            sval_flow = activity_input_r.body[0]["Flow"]

            # Validate type match
            sval_flow_type = Flow.flow_type(fid=sval_flow, anum=self.anum, domain=self.domain)
            if sval_flow_type != sig_params[pname]:
                msg = f"Supplied parameter flow type for {pname} does not match signature Parameter type {sig_params[pname]}"
                _logger.error(msg)
                raise ActionException  # TODO : Type define mismatch exception

            Relvar.insert(db=mmdb, tr=tr_Call, relvar='Method Call Parameter', tuples=[
                Method_Call_Parameter_i(Method_call=self.action_id, Activity=self.anum, Parameter=pname,
                                        Signature=self.activity_data.signum, Domain=self.domain, Flow=sval_flow)
            ])

        # Validate match between set of supplied params and the Method Signature Parameters
        if sp_pnames != set(sig_params.keys()):
            msg = (f"Supplied parameter names [{sp_pnames}] does not match the signature {sig_params} of: "
                   f"Method {self.caller_flow.tname}.{self.method_name}")
            _logger.error(msg)
            ActionException(msg)

        Transaction.execute(db=mmdb, name=tr_Call)
        return Boundary_Actions(ain={self.action_id}, aout={self.action_id})

