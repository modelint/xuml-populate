"""
method_call.py – Process a call action
"""
# System
import logging
from typing import Optional

# Model Integration
from scrall.parse.visitor import Call_a, Op_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# xUML Populate
from xuml_populate.utility import print_mmdb
from xuml_populate.populate.actions.expressions.scalar_expr import ScalarExpr
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.actions.read_action import ReadAction
from xuml_populate.exceptions.action_exceptions import *
from xuml_populate.populate.actions.aparse_types import ActivityAP, Boundary_Actions, Flow_ap
from xuml_populate.populate.mmclass_nt import (Method_Call_i, Method_Call_Parameter_i, Method_Call_Output_i,
                                               Instance_Action_i)

_logger = logging.getLogger(__name__)

tr_Call = "Method Call"

class MethodCall:
    """
    Populate all components of a Method Call action and any other
    actions required by the parse
    """

    def __init__(self, method_name: str, method_anum: str, caller_flow: Flow_ap, parse: Call_a | Op_a,
                 activity_data: ActivityAP):
        """
        Initialize the data we need to populate a method call

        Args:
            method_name:  The name of the method to be called
            method_anum:  The method's activity number
            caller_flow:  A single instance flow providing the target instance of the method call
            parse: A parsed call or op statement (that resolves to a method invocation)
            activity_data:  Information about the activity where this action executes
        """
        self.method_name = method_name
        self.method_anum = method_anum
        self.parse = parse
        # The Scrall grammar indicates that the last element in the components list must be an operation
        self.op_parse = self.parse.call.components[-1] if type(parse).__name__ == "Call_a" else parse
        self.activity_data = activity_data
        self.caller_flow = caller_flow
        self.action_id = None
        self.anum = self.activity_data.anum
        self.domain = self.activity_data.domain

    def process(self) -> tuple[str, str, Flow_ap]:
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
        Relvar.insert(db=mmdb, tr=tr_Call, relvar='Instance Action', tuples=[
            Instance_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Call, relvar='Method Call', tuples=[
            Method_Call_i(ID=self.action_id, Activity=self.anum, Domain=self.domain, Method=self.method_anum,
                          Instance_flow=self.caller_flow.fid)
        ])

        # Validate Method Call params (ensure that the call matches the Method's populated signature
        R = f"Anum:<{self.method_anum}>, Domain:<{self.domain}>"
        Relation.restrict(db=mmdb, relation='Method', restriction=R, svar_name="target_method_sv")
        target_method_sig_r = Relation.semijoin(db=mmdb, rname2='Method Signature',
                                                attrs={'Name': 'Method', 'Domain': 'Domain'})
        # IMPORTANT:
        # We need the signature of the method we are calling (not the signature of the activity calling the method)
        target_method_signum = target_method_sig_r.body[0]['SIGnum']
        param_r = Relation.semijoin(db=mmdb, rname2='Parameter', attrs={'SIGnum': 'Signature', 'Domain': 'Domain'})
        sig_params = {t["Name"]: t["Type"] for t in param_r.body}

        # Populate each Parameter specified in the Method's signature with an incoming Data Flow
        sp_pnames: set[str] = set()
        for sp in self.op_parse.supplied_params:

            # Set the supplied parameter name
            pname = sp.pname
            sp_pnames.add(pname)

            # Resolve the supplied value to a flow or constant value
            sval = None
            sval_type = type(sp.sval).__name__
            match sval_type:
                case 'N_a':
                    sval = sp.sval.name
                case 'INST_PROJ_a':
                    se = ScalarExpr(expr=sp.sval, input_instance_flow=self.caller_flow, activity_data=self.activity_data)
                    bactions, scalar_flows = se.process()

                    pass  # TODO: resolve scalar expression
                case '_':
                    pass

            sval_flow = None
            # Populate parameter data flows
            R = f"Name:<{sval}>, Class:<{self.caller_flow.tname}>, Domain:<{self.domain}>"
            attr_r = Relation.restrict(db=mmdb, relation="Attribute", restriction=R)
            if attr_r.body:
                ra = ReadAction(input_single_instance_flow=self.caller_flow,
                                attrs=(sval,), anum=self.anum, domain=self.domain)
                aid, sflows = ra.populate()
                sval_flow = sflows[0]
            else:
                # Look up a matching scalar flow
                sval_flow = Flow.find_labeled_scalar_flow(name=sval, anum=self.anum, domain=self.domain)
                # R = f"Parameter:<{sval}>, Activity:<{self.anum}>, Signature:<{self.activity_data.signum}>, Domain:<{self.domain}>"
                # activity_input_r = Relation.restrict(db=mmdb, relation='Activity Input', restriction=R)
                # sval_flow = activity_input_r.body[0]["Flow"]

            # Validate type match
            # sval_flow_type = Flow.flow_type(fid=sval_flow.fid, anum=self.anum, domain=self.domain)
            if sval_flow.tname != sig_params[pname]:
                msg = (f"Supplied parameter flow type for {pname} does not match signature Parameter type "
                       f"{sig_params[pname]}")
                _logger.error(msg)
                raise ActionException  # TODO : Type define mismatch exception

            Relvar.insert(db=mmdb, tr=tr_Call, relvar='Method Call Parameter', tuples=[
                Method_Call_Parameter_i(Method_call=self.action_id, Activity=self.anum, Parameter=pname,
                                        Signature=target_method_signum, Domain=self.domain, Flow=sval_flow.fid)
            ])

        # Validate match between set of supplied params and the Method Signature Parameters
        if sp_pnames != set(sig_params.keys()):
            msg = (f"Supplied parameter names [{sp_pnames}] does not match the signature {sig_params} of: "
                   f"Method {self.caller_flow.tname}.{self.method_name}")
            _logger.error(msg)
            ActionException(msg)


        # Create an output flow in this activity compatible with the output of the target method, if any
        method_call_output_flow = None
        synch_output_r = Relation.semijoin(db=mmdb, rname1="target_method_sv", rname2="Synchronous Output")
        if synch_output_r:
            synch_output_fid = synch_output_r.body[0]["Output_flow"]
            synch_output_anum = synch_output_r.body[0]["Anum"]
            method_call_output_flow = Flow.copy_data_flow(tr=tr_Call, ref_fid=synch_output_fid,
                                                          ref_anum=synch_output_anum, new_anum=self.anum,
                                                          domain=self.domain)
            # Populate the output of the Method Call action (corresponds to the target Method's Synch Output)
            Relvar.insert(db=mmdb, relvar="Method Call Output", tr=tr_Call, tuples=[
                Method_Call_Output_i(Method_call=self.action_id, Activity=self.anum, Domain=self.domain,
                                     Target_method=synch_output_anum, Flow=method_call_output_flow.fid)
            ])

        # TODO: Populate metamodel with synch output method flow (need to update make_xuml_db)

        Transaction.execute(db=mmdb, name=tr_Call)
        return self.action_id, self.action_id, method_call_output_flow

