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
from xuml_populate.populate.actions.action import Action
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions, Flow_ap
from xuml_populate.populate.mmclass_nt import Method_Call_i, Method_Call_Parameter_i

tr_Call = "Method Call"

class MethodCall:
    """
    Populate all components of a Method Call action and any other
    actions required by the parse
    """

    def __init__(self, method_name: str, method_anum: str, caller_flow: Flow_ap, parse: Call_a,
                 activity_data: ActivityAP) -> Boundary_Actions:
        """

        Args:
            call_parse:
            activity_data:
        """
        self.method_name = method_name
        self.method_anum = method_anum
        self.parse = parse
        self.op_parse = self.parse.call.components[-1]
        self.activity_data = activity_data
        self.caller_flow = caller_flow
        self.action_id = None
        self.anum = self.activity_data.anum
        self.domain = self.activity_data.domain

    def process(self):
        """

        Returns:

        """

        Transaction.open(db=mmdb, name=tr_Call)
        self.action_id = Action.populate(tr=tr_Call, anum=self.anum, domain=self.domain, action_type="method call")
        Relvar.insert(db=mmdb, tr=tr_Call, relvar='Method Call', tuples=[
            Method_Call_i(ID=self.action_id, Activity=self.anum, Domain=self.domain, Method=self.method_anum,
                          Instance_flow=self.caller_flow.fid)
        ])

        for sp in self.op_parse.supplied_params:
            pname = sp.pname
            sval = sp.sval.name

            # Populate parameter data flows
            R = f"Parameter:<{sval}>, Activity:<{self.anum}>, Signature:<{self.activity_data.signum}>, Domain:<{self.domain}>"
            activity_input_r = Relation.restrict(db=mmdb, relation='Activity Input', restriction=R)
            sval_flow = activity_input_r.body[0]["Flow"]
            Relvar.insert(db=mmdb, tr=tr_Call, relvar='Method Call Parameter', tuples=[
                Method_Call_Parameter_i(Method_call=self.action_id, Activity=self.anum, Parameter=pname,
                                        Signature=self.activity_data.signum, Domain=self.domain, Flow=sval_flow)
            ])

        Transaction.execute(db=mmdb, name=tr_Call)

        print_mmdb()
        pass

